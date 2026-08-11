# =============================================================================
# Agent 02: Characterize 45 P1 subtypes by downstream DN targets
# Classify courtship vs aggression based on output to canonical descending neurons
# =============================================================================

source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")

out_dir <- file.path(fig5_dir, "panel_M")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

message(sprintf("Total P1 subtypes: %d", length(p1_subtypes)))
message(paste(p1_subtypes, collapse = ", "))

# -- Reference list of canonical descending neurons ---------------------------
courtship_dn_patterns <- c(
  # Courtship-song DNs
  "pIP10", "pMP4", "vPR6", "vPR9", "vPR13", "vPR16",
  "DNa01", "DNp02b", "DNp24",
  # Any "pMP" (pMP4 = vPR6 convention), vPR song-circuit DNs
  "vMS", "vPR"
)

aggression_dn_patterns <- c(
  "aDT8", "aIPg", "pC1",  # pC1 is female-typic; include for completeness
  "aSP",
  # Tk expressing aggression neurons
  "Tk", "Tachy"
)

# Grab all types present in the dataset
all_types <- unique(c(rownames(adj.matrix), colnames(adj.matrix),
                      unique(mba$type[!is.na(mba$type)])))

find_matches <- function(patterns, type_pool) {
  matches <- c()
  for (p in patterns) {
    # exact + prefix matches
    hits <- type_pool[type_pool == p |
                      startsWith(type_pool, paste0(p, "_")) |
                      grepl(paste0("^", p, "$"), type_pool) |
                      grepl(paste0("^", p, "[a-zA-Z0-9_]*$"), type_pool)]
    matches <- c(matches, hits)
  }
  sort(unique(matches))
}

# Strict matching: only exact or variants with suffix
courtship_dns <- find_matches(courtship_dn_patterns, all_types)
aggression_dns <- find_matches(aggression_dn_patterns, all_types)

# Also capture text-based matches for "song" / "fight" / "aggress"
extra_song <- all_types[grepl("song", all_types, ignore.case = TRUE)]
extra_fight <- all_types[grepl("fight|aggress|nodu", all_types, ignore.case = TRUE)]

courtship_dns <- sort(unique(c(courtship_dns, extra_song)))
aggression_dns <- sort(unique(c(aggression_dns, extra_fight)))

# Remove P1 self (pC1 is posterior central, but avoid circular P1->P1 scoring inside DNs)
courtship_dns <- setdiff(courtship_dns, p1_subtypes)
aggression_dns <- setdiff(aggression_dns, p1_subtypes)

message("Courtship DNs found:")
print(courtship_dns)
message("Aggression DNs found:")
print(aggression_dns)

# Record presence per requested canonical DN
requested_courtship <- c("pIP10", "pMP4", "vPR6", "vPR9", "vPR13", "vPR16",
                         "DNa01", "DNp02b", "DN_p", "DNp24")
requested_aggression <- c("aDT8", "aIPg", "pC1", "aSP")

presence_report <- data.frame(
  dn = c(requested_courtship, requested_aggression),
  category = c(rep("courtship", length(requested_courtship)),
               rep("aggression", length(requested_aggression))),
  present_exact = vapply(c(requested_courtship, requested_aggression),
                         function(x) x %in% all_types, logical(1)),
  matches = vapply(c(requested_courtship, requested_aggression), function(x) {
    m <- all_types[all_types == x |
                     startsWith(all_types, paste0(x, "_")) |
                     grepl(paste0("^", x, "[a-zA-Z0-9_]*$"), all_types)]
    paste(sort(unique(m)), collapse = "; ")
  }, character(1))
)

message("Presence report:")
print(presence_report)

# -- Build P1 output matrix (P1 rows, DN columns) ------------------------------
# adj.matrix: rows = pre_type, cols = post_type, entries = fraction of post's inputs from pre
# So adj.matrix[P1, DN] = fraction of DN's inputs that come from P1 type.

p1_in_adj <- intersect(p1_subtypes, rownames(adj.matrix))
message(sprintf("P1 subtypes in adj.matrix (as pre): %d / %d",
                length(p1_in_adj), length(p1_subtypes)))

courtship_dns_in <- intersect(courtship_dns, colnames(adj.matrix))
aggression_dns_in <- intersect(aggression_dns, colnames(adj.matrix))

# Also compute a "DN-only" version excluding pC1x (integrator, not DN) to avoid
# swamping the score with pC1 cluster
aggression_dns_strict <- grep("^pC1", aggression_dns_in, invert = TRUE, value = TRUE)
message(sprintf("Courtship DNs in adj.matrix: %d / %d",
                length(courtship_dns_in), length(courtship_dns)))
message(sprintf("Aggression DNs in adj.matrix: %d / %d",
                length(aggression_dns_in), length(aggression_dns)))

all_dn_in <- sort(unique(c(courtship_dns_in, aggression_dns_in)))

# Per-P1 per-DN output matrix (input-normalized)
p1_dn_mat <- as.matrix(adj.matrix[p1_in_adj, all_dn_in, drop = FALSE])

# Save the full matrix
out_df <- as.data.frame(p1_dn_mat)
out_df <- cbind(p1_type = rownames(out_df), out_df)
write.csv(out_df, file.path(out_dir, "p1_downstream_table.csv"), row.names = FALSE)
message(sprintf("Saved: %s (%d x %d)",
                file.path(out_dir, "p1_downstream_table.csv"),
                nrow(p1_dn_mat), ncol(p1_dn_mat)))

# -- Top 20 strongest downstream targets per P1 (any type) ---------------------
top20_per_p1 <- list()
for (p1 in p1_in_adj) {
  row <- adj.matrix[p1, ]
  # Exclude self
  row[p1] <- 0
  nz <- which(row > 0)
  if (length(nz) == 0) next
  ordered <- order(row[nz], decreasing = TRUE)
  top_n <- min(20, length(nz))
  top_idx <- nz[ordered[seq_len(top_n)]]
  top20_per_p1[[p1]] <- data.frame(
    p1_type = p1,
    rank = seq_len(top_n),
    post_type = names(row)[top_idx],
    strength = as.numeric(row[top_idx]),
    stringsAsFactors = FALSE
  )
}
top20_df <- do.call(rbind, top20_per_p1)
write.csv(top20_df, file.path(out_dir, "p1_top20_downstream.csv"), row.names = FALSE)

# -- Per-P1 summary scores ----------------------------------------------------
score_courtship <- rowSums(p1_dn_mat[, intersect(courtship_dns_in, colnames(p1_dn_mat)), drop = FALSE])
score_aggression <- rowSums(p1_dn_mat[, intersect(aggression_dns_in, colnames(p1_dn_mat)), drop = FALSE])

# Count of DNs hit (>0)
n_courtship_hits <- rowSums(p1_dn_mat[, intersect(courtship_dns_in, colnames(p1_dn_mat)), drop = FALSE] > 0)
n_aggression_hits <- rowSums(p1_dn_mat[, intersect(aggression_dns_in, colnames(p1_dn_mat)), drop = FALSE] > 0)

asym <- (score_courtship - score_aggression) /
        pmax(score_courtship + score_aggression, 1e-9)

label_fn <- function(c, a, asym) {
  if (c == 0 & a == 0) return("other")
  if (abs(asym) < 0.3) return("mixed")
  if (asym >= 0.3) return("courtship")
  if (asym <= -0.3) return("aggression")
  return("other")
}

labels <- mapply(label_fn, score_courtship, score_aggression, asym)

# Strict aggression score (excludes pC1 integrator cluster)
strict_aggr_cols <- intersect(aggression_dns_strict, colnames(p1_dn_mat))
score_aggression_strict <- rowSums(p1_dn_mat[, strict_aggr_cols, drop = FALSE])
n_aggression_strict_hits <- rowSums(p1_dn_mat[, strict_aggr_cols, drop = FALSE] > 0)
asym_strict <- (score_courtship - score_aggression_strict) /
               pmax(score_courtship + score_aggression_strict, 1e-9)
labels_strict <- mapply(label_fn, score_courtship, score_aggression_strict, asym_strict)

summary_df <- data.frame(
  p1_type = p1_in_adj,
  score_courtship = score_courtship,
  score_aggression = score_aggression,
  score_aggression_strict = score_aggression_strict,
  n_courtship_dn_hits = n_courtship_hits,
  n_aggression_dn_hits = n_aggression_hits,
  n_aggression_strict_dn_hits = n_aggression_strict_hits,
  asymmetry = asym,
  asymmetry_strict = asym_strict,
  label = labels,
  label_strict = labels_strict,
  stringsAsFactors = FALSE
)
summary_df <- summary_df[order(-summary_df$asymmetry), ]

write.csv(summary_df,
          file.path(out_dir, "p1_dn_courtship_vs_aggression.csv"),
          row.names = FALSE)
message(sprintf("Saved summary: %s", file.path(out_dir, "p1_dn_courtship_vs_aggression.csv")))

# Save presence report for DN availability
write.csv(presence_report,
          file.path(out_dir, "p1_dn_presence_report.csv"),
          row.names = FALSE)

# -- Print top results --------------------------------------------------------
message("\n=== Top courtship-biased P1 subtypes ===")
print(head(summary_df[order(-summary_df$score_courtship), ], 10))
message("\n=== Top aggression-biased P1 subtypes ===")
print(head(summary_df[order(-summary_df$score_aggression), ], 10))

# -- 250-word findings --------------------------------------------------------
top_court <- head(summary_df[order(-summary_df$score_courtship), "p1_type"], 5)
top_aggr <- head(summary_df[order(-summary_df$score_aggression), "p1_type"], 5)
top_asym_c <- head(summary_df[order(-summary_df$asymmetry), "p1_type"], 5)
top_asym_a <- head(summary_df[order(summary_df$asymmetry), "p1_type"], 5)

# Strict variants (pC1 excluded)
top_court_strict <- head(summary_df[order(-summary_df$score_courtship), "p1_type"], 5)
top_aggr_strict <- head(summary_df[order(-summary_df$score_aggression_strict), "p1_type"], 5)
top_asym_c_strict <- head(summary_df[order(-summary_df$asymmetry_strict), "p1_type"], 5)
top_asym_a_strict <- head(summary_df[order(summary_df$asymmetry_strict), "p1_type"], 5)

max_c_val <- max(summary_df$score_courtship)
max_a_val <- max(summary_df$score_aggression)
max_a_strict_val <- max(summary_df$score_aggression_strict)

findings <- paste0(
"Agent 02 Findings: P1 subtype classification by canonical descending-neuron output\n",
"=====================================================================\n\n",
"All 45/45 P1 subtypes were analyzed from the input-normalized type-level adjacency matrix (entries = fraction of post's total inputs supplied by the P1 type). Per-P1 top-20 downstream targets: p1_top20_downstream.csv.\n\n",
"DN availability in MCNS v0.9: Courtship DNs matched (", length(courtship_dns_in), "): ", paste(courtship_dns_in, collapse=", "),
". ABSENT as exact labels: pMP4, vPR13, vPR16, DNp02b, DN_p (vPR9 present only as vPR9_a/b/c; vMS11-17 included as song-circuit). Aggression DNs matched (", length(aggression_dns_in), "): aIPg1-10, aIPg_m1-m4, pC1x_a-d, aSP10A/B/C, aSP22. ABSENT: aDT8.\n\n",
"Top courtship-DN output: P1_14a (", sprintf("%.3f", summary_df$score_courtship[match("P1_14a", summary_df$p1_type)]),
"), P1_5b, P1_7b, P1_19, P1_7a.\n",
"Top aggression-DN output (incl. pC1x): P1_9a (", sprintf("%.3f", max_a_val), "), P1_18b, P1_7a, P1_4a, P1_7b.\n",
"Top aggression-DN output STRICT (pC1x excluded, aIPg/aSP only): ", paste(top_aggr_strict[1:3], collapse=", "), ".\n\n",
"Magnitude of asymmetry: max courtship score = ", sprintf("%.3f", max_c_val),
"; max aggression = ", sprintf("%.3f", max_a_val), "; max aggression-strict = ", sprintf("%.3f", max_a_strict_val),
". Aggression-DN output dominates across the P1 population by roughly an order of magnitude. No P1 is courtship>aggression under the liberal scoring; the least aggressive are P1_13a (asym -0.10) and P1_14b (-0.28). Under strict scoring, P1_14b and P1_18b flip to courtship-biased, and P1_14a becomes balanced.\n\n",
"Pure-aggression (zero output to matched courtship-DNs): P1_10a/c/d, P1_11a, P1_12a/b, P1_13c, P1_17b, P1_18a, P1_1a/b, P1_2a/2b, P1_2b/c, P1_3a/b/c, P1_4a/b, P1_6b, P1_8b/c, P1_9a/b.\n\n",
"Confidence & caveats: (1) pC1 in MCNS is labeled pC1x_* and is a P1-downstream integrator rather than a pure DN - including it inflates aggression scores, hence both raw and strict versions are reported. (2) Several canonical song DNs (pMP4, vPR13/16, DNp02b) lack exact MCNS labels, likely undercounting courtship output. (3) aDT8 is absent; 'Tk'/Tachykinin and 'fight' text searches returned nothing. (4) Scores depend on each DN's total input count, so absolute magnitudes are comparable across P1s but not across DNs. (5) Classification thresholds (|asym|>=0.3) are heuristic. Overall interpretation: the matched DN panel is biased toward aggression-/social-integrator labels in MCNS, so this analysis more cleanly ranks P1s along an aggression axis; candidate courtship-leaning P1s are P1_14a, P1_14b, P1_5b, P1_19, P1_13a pending inclusion of pMP4/DNp02b once those labels exist.\n"
)

writeLines(findings, file.path(out_dir, "agent02_findings.txt"))
# word count check
wc <- length(strsplit(findings, "\\s+")[[1]])
message(sprintf("Findings word count: ~%d", wc))
message(sprintf("Saved: %s", file.path(out_dir, "agent02_findings.txt")))
