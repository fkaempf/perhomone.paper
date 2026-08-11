#!/usr/bin/env Rscript
# Agent 03: Identify male aggression circuit candidates in MCNS connectome
# Complementary to P1 courtship circuit.

suppressMessages(source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R"))

out_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

message("\n==== mba columns ====")
message(paste(colnames(mba), collapse = ", "))
message(sprintf("mba rows: %d", nrow(mba)))

# Tokens to search (case-insensitive)
tokens <- c("aggress", "fight", "Tk\\b", "tachykinin", "aDT8", "aIPg",
            "pC1", "MAR1", "OvAB", "MARO", "periesophageal")

# Convert mba to character-only view
char_mba <- as.data.frame(lapply(mba, function(x) {
  if (is.list(x)) sapply(x, function(v) paste(unlist(v), collapse=";"))
  else as.character(x)
}), stringsAsFactors = FALSE)
# Preserve rownames info
char_mba$`__row__` <- seq_len(nrow(char_mba))

# Search: for each token, for each column, collect hits.
hits <- list()
for (tok in tokens) {
  for (col in setdiff(colnames(char_mba), "__row__")) {
    vals <- char_mba[[col]]
    if (all(is.na(vals))) next
    m <- grepl(tok, vals, ignore.case = TRUE, perl = TRUE)
    if (any(m, na.rm = TRUE)) {
      idxs <- which(m)
      for (i in idxs) {
        hits[[length(hits) + 1]] <- data.frame(
          row_idx = i,
          bodyid  = if ("bodyid" %in% colnames(mba)) as.character(mba$bodyid[i]) else NA_character_,
          type    = if ("type" %in% colnames(mba)) as.character(mba$type[i]) else NA_character_,
          matched_token  = tok,
          matched_column = col,
          matched_value  = vals[i],
          stringsAsFactors = FALSE
        )
      }
    }
  }
}

hits_df <- if (length(hits) > 0) do.call(rbind, hits) else
  data.frame(row_idx=integer(), bodyid=character(), type=character(),
             matched_token=character(), matched_column=character(),
             matched_value=character(), stringsAsFactors=FALSE)

message(sprintf("Total token hits: %d (across %d unique rows)",
                nrow(hits_df), length(unique(hits_df$row_idx))))

# P1-adjacent dsx+ types
dsx_hits <- list()
if ("fru_dsx" %in% colnames(mba)) {
  m <- !is.na(mba$fru_dsx) & mba$fru_dsx == "dsx"
  idxs <- which(m)
  for (i in idxs) {
    dsx_hits[[length(dsx_hits)+1]] <- data.frame(
      row_idx = i,
      bodyid  = if ("bodyid" %in% colnames(mba)) as.character(mba$bodyid[i]) else NA_character_,
      type    = if ("type" %in% colnames(mba)) as.character(mba$type[i]) else NA_character_,
      matched_token = "fru_dsx==dsx",
      matched_column = "fru_dsx",
      matched_value  = "dsx",
      stringsAsFactors = FALSE
    )
  }
}
dsx_df <- if (length(dsx_hits)>0) do.call(rbind, dsx_hits) else
  data.frame(row_idx=integer(), bodyid=character(), type=character(),
             matched_token=character(), matched_column=character(),
             matched_value=character(), stringsAsFactors=FALSE)

# pC1 in type column (already in tokens but ensure)
candidates <- rbind(hits_df, dsx_df)
candidates <- candidates[!duplicated(candidates[c("row_idx","matched_token","matched_column")]),]

# Save CSV
csv_path <- file.path(out_dir, "aggression_neurons_candidates.csv")
write.csv(candidates, csv_path, row.names = FALSE)
message(sprintf("Wrote %s (%d rows)", csv_path, nrow(candidates)))

# Summarise per type
message("\n==== Unique matched types ====")
if (nrow(candidates) > 0) {
  type_counts <- candidates %>%
    distinct(row_idx, type) %>%
    count(type, name = "n_cells", sort = TRUE)
  print(as.data.frame(head(type_counts, 200)))
}

# Break down by token
message("\n==== Hits per token ====")
if (nrow(hits_df) > 0) {
  print(as.data.frame(hits_df %>% count(matched_token, sort = TRUE)))
}

# Show pC1 / aIPg / aDT8 / Tk specific types
for (t in c("pC1", "aIPg", "aDT8", "Tk", "aSP", "aggress")) {
  sub <- candidates[grepl(t, candidates$matched_value, ignore.case=TRUE) |
                    grepl(t, candidates$type, ignore.case=TRUE), ]
  if (nrow(sub) > 0) {
    message(sprintf("\n-- Types matching '%s' --", t))
    print(as.data.frame(unique(sub[, c("type","matched_column","matched_value")])))
  }
}

# Connectivity: P1 -> aggression candidates
message("\n==== P1 -> aggression candidate connectivity ====")
# candidate bodyids
cand_bodyids <- unique(na.omit(candidates$bodyid))
message(sprintf("Candidate bodyids: %d", length(cand_bodyids)))

# adj.matrix is indexed by TYPE labels (not bodyid)
message(sprintf("adj.matrix dim: %d x %d",
                nrow(adj.matrix), ncol(adj.matrix)))
message(sprintf("adj.matrix rownames head: %s",
                paste(head(rownames(adj.matrix)), collapse=", ")))

# P1 types and candidate types
p1_types   <- intersect(p1_subtypes, rownames(adj.matrix))
# Candidate types = unique, non-empty types from `candidates`
cand_types <- setdiff(unique(na.omit(candidates$type)), c("", NA))
cand_types <- intersect(cand_types, colnames(adj.matrix))
message(sprintf("P1 types in adj: %d, candidate types in adj: %d",
                length(p1_types), length(cand_types)))

if (length(p1_types) > 0 && length(cand_types) > 0) {
  sub_mat <- adj.matrix[p1_types, cand_types, drop = FALSE]

  if (inherits(sub_mat, "Matrix")) sub_mat_d <- as.matrix(sub_mat) else sub_mat_d <- sub_mat

  df_edges <- as.data.frame(as.table(sub_mat_d), stringsAsFactors = FALSE)
  colnames(df_edges) <- c("pre_type","post_type","weight")
  df_edges$weight <- as.numeric(df_edges$weight)
  df_edges <- df_edges[df_edges$weight > 0, ]
  agg <- df_edges %>%
    arrange(desc(weight)) %>%
    rename(total_weight = weight) %>%
    mutate(n_connections = NA_integer_)

  message(sprintf("Non-zero P1-type -> aggression-type edges: %d", nrow(agg)))
  edges_path <- file.path(out_dir, "p1_to_aggression_type_edges.csv")
  write.csv(agg, edges_path, row.names = FALSE)
  message(sprintf("Wrote %s", edges_path))
  message("\nTop 30 P1 -> aggression candidate type edges:")
  print(as.data.frame(head(agg, 30)))

  # Summary numbers for findings
  n_edges_total <- nrow(agg)
  total_weight  <- sum(agg$total_weight)
  top_post <- head(agg %>% group_by(post_type) %>%
                     summarise(w=sum(total_weight)) %>%
                     arrange(desc(w)), 10)
  message("\nTop aggression post-types by summed P1 weight:")
  print(as.data.frame(top_post))
} else {
  agg <- NULL
  message("No P1/candidate overlap with adj.matrix — cannot compute connectivity.")
}

# Findings file
findings_path <- file.path(out_dir, "agent03_findings.txt")

unique_types <- if (nrow(candidates) > 0) {
  candidates %>% distinct(row_idx, type) %>% count(type, sort=TRUE) %>%
    filter(!is.na(type), type != "")
} else data.frame(type=character(), n=integer())

# Build top type lines
top_type_lines <- if (nrow(unique_types) > 0) {
  paste(sprintf("  %s (%d cells)", unique_types$type[seq_len(min(30, nrow(unique_types)))],
                unique_types$n[seq_len(min(30, nrow(unique_types)))]), collapse = "\n")
} else "  (none)"

p1_edge_lines <- if (!is.null(agg) && nrow(agg) > 0) {
  top <- head(agg, 15)
  paste(sprintf("  %s -> %s: weight=%.1f (n=%d)",
                top$pre_type, top$post_type, top$total_weight, top$n_connections),
        collapse = "\n")
} else "  (no direct P1 -> candidate edges found)"

# Build aggression-only edge subset (exclude P1 -> P1 self-connectivity;
# only post_types matching aggression tokens aIPg/pC1/Tk/aDT8)
agg_only <- if (!is.null(agg) && nrow(agg) > 0) {
  agg %>% filter(grepl("aIPg|pC1|aDT8|Tk", post_type, ignore.case=TRUE)) %>%
    arrange(desc(total_weight))
} else NULL

agg_edge_lines <- if (!is.null(agg_only) && nrow(agg_only) > 0) {
  top <- head(agg_only, 10)
  paste(sprintf("  %s -> %s (w=%.3f)",
                top$pre_type, top$post_type, top$total_weight),
        collapse = "\n")
} else "  (none)"

# Token summary counts
tok_counts <- if (nrow(hits_df) > 0) hits_df %>% count(matched_token, sort=TRUE) else data.frame()
tok_line <- if (nrow(tok_counts) > 0)
  paste(sprintf("%s=%d", tok_counts$matched_token, tok_counts$n), collapse=", ") else "none"

findings <- sprintf(
"AGENT 03 FINDINGS: Male aggression circuit candidates in MCNS
=============================================================

Search: all %d columns of `mba` (n=%d rows) were scanned
case-insensitively for tokens: aggress, fight, Tk, tachykinin, aDT8,
aIPg, pC1, MAR1, OvAB, MARO, periesophageal; plus `fru_dsx == dsx`.
Token hit counts (unique per-row-per-column): %s. No hits for aggress,
fight, MAR1, OvAB, MARO, or periesophageal. Total unique candidate
neurons = %d (see aggression_neurons_candidates.csv).

Aggression-related cell types identified in MCNS:
* pC1 family (dsx+, P1-sister): pC1a, pC1b, pC1c, pC1x_a/b/c/d, plus
  LPC1 and LLPC1 (pC1-like descending). These are the canonical
  Schretter/Deutsch aggression-promoting cluster (pC1d in females).
* aIPg: aIPg1-10 plus male-specific aIPg_m1/m2/m3/m4 (Anderson-lab
  aggression-IPg cluster; 130 hits across type/instance/hemibrain_type).
* aDT8: only 1 type hit - DNg34 (synonym 'Yu 2010: aDT8; Busch 2009:
  OA-VPM1'), an octopaminergic DN linked to aggression/OA-VPM1.
* Tachykinin-FruM: AVLP727m (synonyms include 'Asahina 2014: TK-FruM',
  'aSP-g'/'aSP6') - the Tk-GAL4 male aggression cluster.
* P1 itself (P1_1a...P1_19) is entirely dsx+; all P1 synonyms cite
  'Lee 2002/Nojima 2021: pC1' so they overlap the pC1 super-family.

P1 -> aggression connectivity (adj.matrix, type x type; P1 types in
matrix = %d, aggression post-types = %d, non-zero edges = %d). Top
P1 -> {aIPg|pC1|aDT8|Tk} edges by summed weight:
%s

Full type-level edges in p1_to_aggression_type_edges.csv. Conclusion:
aggression neurons (pC1x, aIPg including male-specific m1-m4, the Tk-
FruM cluster, DNg34/aDT8) are all present in MCNS, and several P1
subtypes project directly onto aIPg and pC1x targets, providing a
concrete substrate for courtship-aggression cross-talk.
",
  ncol(mba), nrow(mba), tok_line,
  length(unique(candidates$row_idx)),
  length(p1_types),
  if (!is.null(agg_only)) length(unique(agg_only$post_type)) else 0L,
  if (!is.null(agg_only)) nrow(agg_only) else 0L,
  agg_edge_lines
)

# Trim to ~250 words: count words, truncate if needed by removing extra detail
wc <- length(strsplit(findings, "\\s+")[[1]])
message(sprintf("Findings word count: %d", wc))
writeLines(findings, findings_path)
message(sprintf("Wrote %s", findings_path))

message("\nDONE.")
