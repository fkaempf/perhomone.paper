#!/usr/bin/env Rscript
# Agent 07: P1 -> P1 lateral/recurrent connectivity analysis
# Characterize within-ensemble structure: reciprocal pairs, isolated subtypes,
# and Ward-linkage clustering on P1xP1 connectivity profile.

suppressMessages(source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R"))
library(dplyr)
library(tidyr)
library(tibble)
library(Matrix)

out_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# =============================================================================
# 1. Build P1 x P1 subtype-level matrix from adj.matrix
# =============================================================================
# NOTE: data$adj.matrix in this project is already type-aggregated
# (rownames/colnames are neuron types, e.g. "P1_4a"). The edge weight thus
# already represents the summed synaptic weight across all instances of that
# type pair. We therefore extract the P1 x P1 block directly.

p1_meta <- mba %>% filter(grepl("^P1_", type)) %>% select(bodyid, type)
cat(sprintf("P1 cells: %d | P1 subtypes (mba): %d\n",
            nrow(p1_meta), length(unique(p1_meta$type))))

all_subtypes <- sort(unique(p1_meta$type))
have_row <- intersect(all_subtypes, rownames(adj.matrix))
have_col <- intersect(all_subtypes, colnames(adj.matrix))
cat(sprintf("P1 subtypes present in adj.matrix rows: %d | cols: %d\n",
            length(have_row), length(have_col)))

# Use the union of subtypes present as dimnames, zero-fill missing
present_subtypes <- sort(union(have_row, have_col))
p1_lat <- matrix(0, nrow = length(present_subtypes),
                 ncol = length(present_subtypes),
                 dimnames = list(present_subtypes, present_subtypes))
block <- as.matrix(adj.matrix[have_row, have_col, drop = FALSE])
p1_lat[rownames(block), colnames(block)] <- block

# Keep all_subtypes for reporting
all_subtypes <- present_subtypes

cat(sprintf("P1xP1 matrix: %d x %d | total weight: %.1f | nonzero entries: %d\n",
            nrow(p1_lat), ncol(p1_lat), sum(p1_lat), sum(p1_lat > 0)))

# Save matrix
mat_path <- file.path(out_dir, "p1_lateral_matrix.csv")
write.csv(as.data.frame(p1_lat), mat_path, row.names = TRUE)
cat("Wrote:", mat_path, "\n")

# =============================================================================
# 2. Reciprocal pairs and isolated subtypes
# =============================================================================

# Reciprocal strength: min(A->B, B->A) for unordered pair; top by product sqrt
pair_df <- expand.grid(a = all_subtypes, b = all_subtypes,
                       stringsAsFactors = FALSE) %>%
  filter(a < b) %>%
  mutate(
    ab = mapply(function(x, y) p1_lat[x, y], a, b),
    ba = mapply(function(x, y) p1_lat[y, x], a, b),
    recip_min = pmin(ab, ba),
    recip_geom = sqrt(ab * ba),
    total = ab + ba
  ) %>%
  arrange(desc(recip_geom))

top_recip <- pair_df %>% filter(recip_min > 0) %>% head(5)
cat("\nTop 5 reciprocal pairs (by geometric mean of bidirectional weight):\n")
print(top_recip)

# Isolated subtypes: no within-P1 connection in either direction
row_sums <- rowSums(p1_lat)
col_sums <- colSums(p1_lat)
isolated <- all_subtypes[row_sums == 0 & col_sums == 0]
cat("\nIsolated subtypes (no P1->P1 or P1<-P1 connectivity):\n")
print(isolated)

# =============================================================================
# 3. Hierarchical clustering (Ward) on connectivity profile
# =============================================================================
# Profile = concatenation of outgoing row + incoming column (as-source + as-target).
# Use subtypes with ANY within-P1 connectivity. Drop fully-isolated subtypes.

active <- setdiff(all_subtypes, isolated)
prof <- cbind(p1_lat[active, active, drop = FALSE],
              t(p1_lat)[active, active, drop = FALSE])
colnames(prof) <- c(paste0("out_", active), paste0("in_", active))

# Log-scale + row-normalize for robustness
prof_log <- log1p(prof)
# avoid zero rows (shouldn't happen for active)
rs <- rowSums(prof_log)
prof_norm <- prof_log / pmax(rs, 1)

d <- dist(prof_norm, method = "euclidean")
hc <- hclust(d, method = "ward.D2")

# Choose k by inspecting dendrogram heights: use a simple rule -- k that yields
# clusters >= 2 members where possible; try k=4 as default (typical P1 lit.).
# Emit multiple cuts and pick based on mean silhouette if cluster package avail.
pick_k <- NA_integer_
if (requireNamespace("cluster", quietly = TRUE)) {
  ks <- 2:min(8, length(active) - 1)
  sils <- sapply(ks, function(k) {
    cl <- cutree(hc, k)
    if (length(unique(cl)) < 2) return(NA_real_)
    ss <- cluster::silhouette(cl, d)
    mean(ss[, 3])
  })
  # Guard against degenerate cuts dominated by singletons.
  non_trivial <- sapply(ks, function(k) {
    sizes <- table(cutree(hc, k))
    sum(sizes >= 2) >= 2   # need at least 2 clusters with >=2 members
  })
  sils_eff <- ifelse(non_trivial, sils, NA_real_)
  cat(sprintf("\nSilhouette scores: %s\n",
              paste(sprintf("k=%d:%.3f%s", ks, sils,
                            ifelse(non_trivial, "", "*")),
                    collapse = ", ")))
  cat("  (* = cut dominated by singletons, excluded)\n")
  if (all(is.na(sils_eff))) {
    pick_k <- 4L
    cat("All k dominated by singletons; defaulting k=4\n")
  } else {
    pick_k <- ks[which.max(sils_eff)]
    cat(sprintf("Chosen k (max non-trivial silhouette) = %d\n", pick_k))
  }
} else {
  pick_k <- 4L
  cat("\ncluster package unavailable; defaulting k=4\n")
}

clusters <- cutree(hc, k = pick_k)
clust_df <- data.frame(subtype = names(clusters),
                       cluster_id = as.integer(clusters),
                       stringsAsFactors = FALSE)

# Append isolated as cluster_id = 0 for bookkeeping
if (length(isolated) > 0) {
  clust_df <- bind_rows(clust_df,
    data.frame(subtype = isolated, cluster_id = 0L,
               stringsAsFactors = FALSE))
}
clust_df <- clust_df %>% arrange(cluster_id, subtype)

clust_path <- file.path(out_dir, "p1_lateral_clusters.csv")
write.csv(clust_df, clust_path, row.names = FALSE)
cat("Wrote:", clust_path, "\n")

cat("\nCluster membership:\n")
print(clust_df)

# =============================================================================
# 4. Cross-compare with Agent 4 (input clustering) and Agent 2 (DN clustering)
# =============================================================================
# Search for pre-existing outputs, then compute ARI (adjusted Rand index).

find_cluster_csv <- function(patterns) {
  candidates <- c()
  for (p in patterns) {
    candidates <- c(candidates,
      list.files(out_dir, pattern = p, full.names = TRUE, ignore.case = TRUE))
  }
  unique(candidates)
}

agent4_files <- find_cluster_csv(c("p1_input_clusters\\.csv$",
                                   "agent04.*cluster", "input.*cluster",
                                   "p1_input_cluster"))
# Prefer the per-subtype file over the summary aggregate
agent4_files <- agent4_files[order(grepl("summary", agent4_files,
                                         ignore.case = TRUE))]
agent2_files <- find_cluster_csv(c("p1_dn_clusters\\.csv$",
                                   "agent02.*cluster", "dn.*cluster",
                                   "downstream.*cluster", "p1_dn_cluster"))
agent2_files <- agent2_files[order(grepl("summary", agent2_files,
                                         ignore.case = TRUE))]

cat("\nAgent 4 candidate cluster files:", paste(agent4_files, collapse = ", "), "\n")
cat("Agent 2 candidate cluster files:", paste(agent2_files, collapse = ", "), "\n")

ari <- function(a, b) {
  # adjusted Rand index via mclust if available, else manual
  if (requireNamespace("mclust", quietly = TRUE)) {
    return(mclust::adjustedRandIndex(a, b))
  }
  tab <- table(a, b)
  n <- sum(tab)
  sum_comb <- function(x) sum(choose(x, 2))
  a_sum <- sum_comb(rowSums(tab)); b_sum <- sum_comb(colSums(tab))
  t_sum <- sum_comb(as.vector(tab))
  expected <- a_sum * b_sum / choose(n, 2)
  max_i <- 0.5 * (a_sum + b_sum)
  (t_sum - expected) / (max_i - expected)
}

compare_report <- c()

do_compare <- function(label, files) {
  if (length(files) == 0) {
    return(sprintf("%s: no cluster file found on disk -- cross-comparison deferred.", label))
  }
  fp <- files[1]
  other <- tryCatch(read.csv(fp, stringsAsFactors = FALSE),
                    error = function(e) NULL)
  if (is.null(other)) return(sprintf("%s: could not read %s.", label, fp))
  # expect columns subtype, cluster_id (be permissive)
  sc <- intersect(c("subtype", "p1_subtype", "type", "target_type"), colnames(other))[1]
  cc <- intersect(c("cluster_id", "cluster", "k"), colnames(other))[1]
  if (is.na(sc) || is.na(cc)) {
    return(sprintf("%s: file %s has no subtype/cluster columns.", label, fp))
  }
  merged <- inner_join(clust_df, other[, c(sc, cc)] %>%
                         rename(subtype = !!sc, other = !!cc),
                       by = "subtype")
  merged <- merged %>% filter(cluster_id != 0)
  if (nrow(merged) < 3) return(sprintf("%s: too few overlapping subtypes.", label))
  ari_val <- ari(merged$cluster_id, merged$other)
  sprintf("%s (%s): ARI = %.3f over n=%d subtypes.",
          label, basename(fp), ari_val, nrow(merged))
}

compare_report <- c(compare_report,
  do_compare("Agent 4 (input clustering)",    agent4_files),
  do_compare("Agent 2 (downstream-DN clustering)", agent2_files))

cat("\n", paste(compare_report, collapse = "\n"), "\n", sep = "")

# =============================================================================
# 5. Findings narrative (~200 words)
# =============================================================================

n_active <- length(active)
n_iso    <- length(isolated)
k_used   <- pick_k
total_w  <- sum(p1_lat)
diag_w   <- sum(diag(p1_lat))
density  <- mean(p1_lat > 0)

top_str <- paste(sprintf("%s<->%s (min=%.0f, geom=%.1f)",
                         top_recip$a, top_recip$b,
                         top_recip$recip_min, top_recip$recip_geom),
                 collapse = "; ")

iso_str <- if (length(isolated) == 0) "none" else paste(isolated, collapse = ", ")

cluster_sizes <- table(clust_df$cluster_id[clust_df$cluster_id != 0])
cs_str <- paste(sprintf("c%d:n=%d", as.integer(names(cluster_sizes)),
                        as.integer(cluster_sizes)), collapse = ", ")

narrative <- paste0(
  "Agent 07 -- P1 lateral/recurrent connectivity findings\n",
  sprintf("Date: %s\n\n", Sys.Date()),
  sprintf("Built a %d x %d P1 x P1 connectivity matrix by extracting the P1 ",
          length(all_subtypes), length(all_subtypes)),
  "block of the project's type-level adj.matrix (entries already sum across ",
  "all instances of each subtype pair; normalized by the project's default ",
  "pipeline). ",
  sprintf("Total within-ensemble weight = %.3f (diag = %.3f; ",
          total_w, diag_w),
  sprintf("density = %.1f%% of subtype-pairs have >=1 edge). ",
          100 * density),
  sprintf("%d of %d subtypes are fully isolated (no outgoing or incoming ",
          n_iso, length(all_subtypes)),
  "P1<->P1 edge): ",
  iso_str, ".\n\n",
  "Top-5 reciprocal pairs (ranked by geometric mean of bidirectional weight): ",
  top_str, ". These reciprocal hubs likely form the functional backbone of ",
  "P1 lateral integration and are candidates for mutual recurrent excitation ",
  "or feedback sharpening.\n\n",
  "Ward.D2 hierarchical clustering on log-scaled, row-normalized ",
  sprintf("out+in connectivity profiles of %d active subtypes yielded k=%d ",
          n_active, k_used),
  sprintf("clusters (silhouette-optimal). Cluster sizes: %s.\n\n", cs_str),
  "Cross-scheme agreement:\n  ",
  paste(compare_report, collapse = "\n  "),
  "\n\nInterpretation: if lateral clusters align with Agent 4 input-based ",
  "clusters but not Agent 2 DN-output clusters, lateral wiring mirrors shared ",
  "sensory drive (co-activation groups). If it aligns with Agent 2 instead, ",
  "lateral recurrence enforces output-module coherence (courtship vs aggression ",
  "pools). Weak agreement with both implies lateral wiring is an independent ",
  "organizational axis.\n"
)

findings_path <- file.path(out_dir, "agent07_findings.txt")
writeLines(narrative, findings_path)
cat("\nWrote:", findings_path, "\n")

cat("\n=== DONE ===\n")
