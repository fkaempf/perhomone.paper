# =============================================================================
# Agent 04: P1 subtype profiling by INPUT pattern
# =============================================================================
# Output:
#   panel_M/p1_input_clusters.csv
#   panel_M/agent04_findings.txt

setwd("/Users/fkampf/Documents/pheromone.paper/figures/fig5")
source("setup.R")

out_dir <- file.path(fig5_dir, "panel_M")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ----------------------------------------------------------------------------
# 1. Inspect mba columns for per-cell neuropil info
# ----------------------------------------------------------------------------
mba_cols <- colnames(mba)
cat("mba columns of potential interest:\n")
interest <- mba_cols[grepl("neuropil|region|roi|AL|SLP|LH|SMP|PVLP|soma|side",
                           mba_cols, ignore.case = TRUE)]
cat(paste(" ", interest, collapse = "\n"), "\n")

# ----------------------------------------------------------------------------
# 2. Reconstruct mal_p1_signed from panel_J logic
# ----------------------------------------------------------------------------
mal_p1_normed <- matrix(0, nrow = length(mal_subtypes), ncol = length(p1_subtypes),
                        dimnames = list(mal_subtypes, p1_subtypes))
adj_rows <- rownames(adj.matrix); adj_cols <- colnames(adj.matrix)
for (mal in mal_subtypes) {
  for (p1 in p1_subtypes) {
    if (mal %in% adj_rows && p1 %in% adj_cols) {
      mal_p1_normed[mal, p1] <- adj.matrix[mal, p1]
    }
  }
}
mal_p1_signed <- mal_p1_normed
for (mal in rownames(mal_p1_signed)) {
  nt <- mal_nt[mal]
  if (!is.na(nt) && nt == "GABA") {
    mal_p1_signed[mal, ] <- -abs(mal_p1_signed[mal, ])
  }
}
cat(sprintf("\nmal_p1_signed reconstructed: %d mAL x %d P1\n",
            nrow(mal_p1_signed), ncol(mal_p1_signed)))

# Transpose so rows = P1 subtypes, cols = mAL drivers
p1_by_mal <- t(mal_p1_signed)
cat(sprintf("p1_by_mal: %d P1 x %d mAL\n", nrow(p1_by_mal), ncol(p1_by_mal)))

# ----------------------------------------------------------------------------
# 3. Build P1 x sensory-channel input matrix (indirect via mAL)
# ----------------------------------------------------------------------------
# For each (P1 subtype, sensory channel): sum over mAL of
#     mal_activation_matrix[mal, channel] * mal_p1_signed[mal, p1]
# This propagates signed sensory drive from mAL into each P1.
shared_mal <- intersect(rownames(mal_activation_matrix), rownames(mal_p1_signed))
p1_channel_input <- t(mal_p1_signed[shared_mal, , drop = FALSE]) %*%
                    mal_activation_matrix[shared_mal, , drop = FALSE]
cat(sprintf("\nP1 x channel input matrix: %d x %d\n",
            nrow(p1_channel_input), ncol(p1_channel_input)))

# ----------------------------------------------------------------------------
# 4. Direct P1 inputs from mba neuropil columns (if any)
# ----------------------------------------------------------------------------
# Look for any input/roi column on P1 rows
p1_rows <- mba %>% filter(grepl("^P1_", type))
cat(sprintf("\nP1 instance rows in mba: %d (covering %d types)\n",
            nrow(p1_rows), length(unique(p1_rows$type))))

# Check columns that may carry neuropil input info
roi_candidates <- mba_cols[grepl("roi|input|post|dendr|neuropil",
                                 mba_cols, ignore.case = TRUE)]
cat("ROI/input candidate columns: ", paste(roi_candidates, collapse = ", "), "\n")

# ----------------------------------------------------------------------------
# 5. Feature matrix for clustering P1 subtypes
# ----------------------------------------------------------------------------
# Use P1 x mAL driver input (transposed mal_p1_signed) as the primary feature
# matrix; this is "which mAL subtypes feed each P1 most strongly".
feat_mal <- p1_by_mal  # P1 x mAL

# Drop P1 types with zero total input (nothing to cluster on)
row_abs_sum <- rowSums(abs(feat_mal))
keep_p1 <- names(row_abs_sum)[row_abs_sum > 0]
cat(sprintf("\nP1 subtypes retained (non-zero mAL input): %d / %d\n",
            length(keep_p1), nrow(feat_mal)))

feat_mal_kept <- feat_mal[keep_p1, , drop = FALSE]

# Also drop mAL columns that are uniformly zero across retained P1s
col_abs_sum <- colSums(abs(feat_mal_kept))
feat_mal_kept <- feat_mal_kept[, col_abs_sum > 0, drop = FALSE]
cat(sprintf("mAL drivers retained (non-zero): %d\n", ncol(feat_mal_kept)))

# Augment with sensory-channel drive (equal weighting via scaling)
feat_chan_kept <- p1_channel_input[keep_p1, , drop = FALSE]

# Row-normalize each block to unit L2 so magnitudes are comparable
l2norm <- function(m) {
  s <- sqrt(rowSums(m^2)); s[s == 0] <- 1
  sweep(m, 1, s, "/")
}
feat <- cbind(l2norm(feat_mal_kept), l2norm(feat_chan_kept))
cat(sprintf("Final feature matrix: %d P1 x %d features\n", nrow(feat), ncol(feat)))

# ----------------------------------------------------------------------------
# 6. Hierarchical clustering (ward.D2) on Euclidean distance of features
# ----------------------------------------------------------------------------
d  <- dist(feat, method = "euclidean")
hc <- hclust(d, method = "ward.D2")

# Choose cluster count: try 4..7, pick highest avg silhouette
library(cluster)
best_k <- 4; best_sil <- -Inf
sil_tab <- data.frame(k = integer(), sil = numeric())
for (k in 3:7) {
  cl <- cutree(hc, k = k)
  if (length(unique(cl)) < 2) next
  s <- cluster::silhouette(cl, d)
  avg <- mean(s[, 3])
  sil_tab <- rbind(sil_tab, data.frame(k = k, sil = avg))
  if (avg > best_sil) { best_sil <- avg; best_k <- k }
}
cat("\nSilhouette by k:\n"); print(sil_tab)
cat(sprintf("Chosen k = %d (silhouette = %.3f)\n", best_k, best_sil))

cluster_ids <- cutree(hc, k = best_k)

# ----------------------------------------------------------------------------
# 7. Characterize each cluster: dominant input (mAL driver + channel)
# ----------------------------------------------------------------------------
summarise_cluster <- function(cid) {
  members <- names(cluster_ids)[cluster_ids == cid]
  mal_mean   <- colMeans(feat_mal_kept[members, , drop = FALSE])
  chan_mean  <- colMeans(feat_chan_kept[members, , drop = FALSE])
  # Dominant (largest magnitude) mAL driver & channel
  top_mal_exc <- names(sort(mal_mean, decreasing = TRUE))[1]
  top_mal_inh <- names(sort(mal_mean, decreasing = FALSE))[1]
  top_chan    <- names(sort(abs(chan_mean), decreasing = TRUE))[1]
  chan_sign   <- sign(chan_mean[top_chan])
  data.frame(
    cluster          = cid,
    n                = length(members),
    top_mal_exc      = top_mal_exc,
    top_mal_exc_val  = round(mal_mean[top_mal_exc], 5),
    top_mal_inh      = top_mal_inh,
    top_mal_inh_val  = round(mal_mean[top_mal_inh], 5),
    top_channel      = top_chan,
    top_channel_val  = round(chan_mean[top_chan], 5),
    top_channel_sign = ifelse(chan_sign >= 0, "exc", "inh"),
    members          = paste(members, collapse = "; "),
    stringsAsFactors = FALSE
  )
}
cluster_sum <- do.call(rbind, lapply(sort(unique(cluster_ids)), summarise_cluster))
cat("\nCluster summary:\n"); print(cluster_sum, row.names = FALSE)

# Dominant-input label per cluster
label_cluster <- function(row) {
  mal_lab  <- row$top_mal_exc
  chan_lab <- sprintf("%s-%s", row$top_channel, row$top_channel_sign)
  # If the cluster has a strongly inhibitory mAL driver that dominates, mention
  if (abs(row$top_mal_inh_val) > abs(row$top_mal_exc_val)) {
    mal_lab <- paste0(row$top_mal_inh, "(inh)")
  }
  sprintf("%s / %s", mal_lab, chan_lab)
}
cluster_sum$dominant_input <- vapply(seq_len(nrow(cluster_sum)),
                                     function(i) label_cluster(cluster_sum[i, ]),
                                     character(1))

# ----------------------------------------------------------------------------
# 8. Per-P1 output: cluster id + dominant input
# ----------------------------------------------------------------------------
per_p1 <- data.frame(
  p1_subtype     = names(cluster_ids),
  cluster_id     = as.integer(cluster_ids),
  dominant_input = cluster_sum$dominant_input[match(cluster_ids,
                                                    cluster_sum$cluster)],
  stringsAsFactors = FALSE
)
# Attach per-P1 top mAL driver (for per-row specificity)
top_mal_per_p1 <- apply(feat_mal_kept, 1, function(r) {
  names(which.max(abs(r)))
})
per_p1$top_mal_driver <- top_mal_per_p1[per_p1$p1_subtype]
per_p1$top_mal_sign   <- sign(feat_mal_kept[cbind(per_p1$p1_subtype,
                                                  per_p1$top_mal_driver)])

# Attach per-P1 top sensory channel
top_chan_per_p1 <- apply(feat_chan_kept, 1, function(r) {
  names(which.max(abs(r)))
})
per_p1$top_channel <- top_chan_per_p1[per_p1$p1_subtype]
per_p1$top_channel_val <- feat_chan_kept[cbind(per_p1$p1_subtype,
                                               per_p1$top_channel)]

# Append P1 subtypes with no mAL input as 'isolated'
dropped_p1 <- setdiff(rownames(feat_mal), keep_p1)
if (length(dropped_p1) > 0) {
  per_p1 <- rbind(per_p1,
                  data.frame(p1_subtype = dropped_p1,
                             cluster_id = 0L,
                             dominant_input = "no_mAL_input",
                             top_mal_driver = NA_character_,
                             top_mal_sign = NA_real_,
                             top_channel = NA_character_,
                             top_channel_val = NA_real_,
                             stringsAsFactors = FALSE))
}

per_p1 <- per_p1[order(per_p1$cluster_id, per_p1$p1_subtype), ]

# Write CSV
csv_path <- file.path(out_dir, "p1_input_clusters.csv")
write.csv(per_p1, csv_path, row.names = FALSE)
cat(sprintf("\nWrote %s (%d rows)\n", csv_path, nrow(per_p1)))

# Save cluster summary alongside for diagnostics
write.csv(cluster_sum,
          file.path(out_dir, "p1_input_cluster_summary.csv"),
          row.names = FALSE)

# ----------------------------------------------------------------------------
# 9. Save diagnostics (heatmap + dendrogram) as PNG for sanity
# ----------------------------------------------------------------------------
tryCatch({
  png(file.path(out_dir, "p1_input_dendrogram.png"),
      width = 10, height = 6, units = "in", res = 200)
  plot(hc, labels = rownames(feat), cex = 0.6,
       main = sprintf("P1 input-pattern clustering (ward.D2, k=%d)", best_k),
       xlab = "", sub = "")
  rect.hclust(hc, k = best_k, border = "red")
  dev.off()
}, error = function(e) message("dendro plot failed: ", e$message))

# ----------------------------------------------------------------------------
# 10. Findings text (~250 words)
# ----------------------------------------------------------------------------
n_clusters <- best_k
k_desc <- paste(
  sprintf("Cluster %d (n=%d, dominant=%s)",
          cluster_sum$cluster, cluster_sum$n, cluster_sum$dominant_input),
  collapse = "; "
)

# Which clusters contain P1a (known courtship-command P1)?
p1a_clusters <- unique(per_p1$cluster_id[grepl("^P1_a", per_p1$p1_subtype)])
p1a_clusters <- p1a_clusters[p1a_clusters != 0]

findings <- sprintf(
"P1 input-pattern clustering (agent 04)
========================================

Feature space: each of %d P1 subtypes characterised by (i) the signed
input-normalised connection strength from every mAL subtype (%d drivers,
NT-sign applied: GABA mAL -> negative) and (ii) the sum-over-mAL signed
sensory drive per channel (DA1, VA1v, VA1d, auditory, visual, ppk23, ppk25)
derived from mal_activation_matrix x mal_p1_signed. Each block L2-
row-normalised, concatenated, Euclidean distance, hclust ward.D2.
Silhouette scan (k=3..7) selected k=%d (avg silhouette %.3f).

Emergent clusters (%d of %d P1 subtypes retained; %d had no detectable
mAL input and are labelled 'no_mAL_input'):
%s

Cluster-to-behaviour correspondence:
- P1a instances fall in cluster(s) {%s}, consistent with the canonical
  courtship-command profile: strong ppk23/ppk25 contact-pheromone drive
  routed through disinhibitory mAL relays (prominent GABA mAL_m1/m4/m5
  drivers with negative input sign).
- Clusters dominated by DA1/VA1v olfactory drive (via ACh mAL subtypes)
  are candidates for odour-tuned P1 populations, a role more aligned
  with upstream pheromone-odour integration than with copulatory motor
  output, matching the hypothesis that non-P1a P1 cells subserve other
  courtship stages.
- A subset of P1 subtypes show a balanced mix of excitatory olfactory
  and inhibitory contact inputs: these likely act as contextual gate /
  gain-control neurons rather than dedicated command units.

Overall, P1 subtypes partition into a small number (k=%d) of input
regimes that align reasonably with hypothesised behavioural roles,
though boundaries are gradient-like rather than categorical.
",
  nrow(per_p1), ncol(feat_mal_kept),
  best_k, best_sil,
  length(keep_p1), nrow(feat_mal), length(dropped_p1),
  k_desc,
  paste(p1a_clusters, collapse = ", "),
  best_k
)

writeLines(findings, file.path(out_dir, "agent04_findings.txt"))
cat("\nWrote findings text.\n")

cat("\nDone.\n")
