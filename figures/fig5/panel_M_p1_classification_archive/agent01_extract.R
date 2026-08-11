#!/usr/bin/env Rscript
# Agent 01: Extract P1 metadata for courtship vs aggression classification

suppressMessages(source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R"))
library(dplyr)
library(tidyr)

out_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# Columns we want; keep only those that exist in mba
desired_cols <- c("bodyid", "type", "fru_dsx", "superclass", "subclass",
                  "flywire_type", "hemibrain_type", "synonyms", "dimorphism",
                  "soma_side", "instance", "supertype", "itolee_hl", "truman_hl",
                  "group", "location")
present_cols <- intersect(desired_cols, colnames(mba))
missing_cols <- setdiff(desired_cols, colnames(mba))
cat("Present columns:", paste(present_cols, collapse = ", "), "\n")
cat("Missing columns:", paste(missing_cols, collapse = ", "), "\n")

p1_meta <- mba %>%
  filter(grepl("^P1_", type)) %>%
  select(all_of(present_cols))

# Coerce list columns to character (comma-joined) for CSV
for (cn in names(p1_meta)) {
  if (is.list(p1_meta[[cn]])) {
    p1_meta[[cn]] <- sapply(p1_meta[[cn]], function(x) {
      if (is.null(x) || length(x) == 0) NA_character_ else paste(unique(as.character(x)), collapse = ";")
    })
  }
}

cat("P1 rows:", nrow(p1_meta), "| distinct types:", length(unique(p1_meta$type)), "\n")

full_path <- file.path(out_dir, "p1_metadata_full.csv")
write.csv(p1_meta, full_path, row.names = FALSE)
cat("Wrote:", full_path, "\n")

# ---- Per-type per-column distinct non-NA counts ----
summary_cols <- setdiff(present_cols, c("bodyid", "type"))

distinct_non_na <- function(x) {
  x <- x[!is.na(x) & x != "" & x != "NA"]
  length(unique(x))
}

per_type <- p1_meta %>%
  group_by(type) %>%
  summarise(across(all_of(summary_cols), distinct_non_na), n_cells = n(), .groups = "drop")

cat("\nPer-type distinct-value counts (first rows):\n")
print(head(per_type, 10))

# ---- Global per-column distinct non-NA counts ----
global_counts <- sapply(summary_cols, function(cn) distinct_non_na(p1_meta[[cn]]))
cat("\nGlobal distinct non-NA values per column:\n")
print(global_counts)

# ---- Keyword search ----
court_pat <- "(?i)(fru|dsx|p1a|courtship|court)"
agg_pat   <- "(?i)(asp|aSP-g|aSP-h|\\bTk\\b|tachykinin|aggression|\\bagg\\b|fight)"

search_cols <- intersect(c("fru_dsx", "superclass", "subclass", "synonyms",
                           "flywire_type", "hemibrain_type", "supertype",
                           "itolee_hl", "truman_hl", "group", "instance"),
                         present_cols)

annot <- p1_meta %>%
  rowwise() %>%
  mutate(
    court_hits = paste(na.omit(unlist(lapply(search_cols, function(cn) {
      v <- get(cn); if (!is.na(v) && grepl(court_pat, v, perl = TRUE)) sprintf("%s=%s", cn, v) else NA_character_
    }))), collapse = " | "),
    agg_hits = paste(na.omit(unlist(lapply(search_cols, function(cn) {
      v <- get(cn); if (!is.na(v) && grepl(agg_pat, v, perl = TRUE)) sprintf("%s=%s", cn, v) else NA_character_
    }))), collapse = " | ")
  ) %>%
  ungroup() %>%
  mutate(
    court_hits = ifelse(court_hits == "", NA_character_, court_hits),
    agg_hits   = ifelse(agg_hits == "",   NA_character_, agg_hits),
    class_guess = case_when(
      !is.na(court_hits) & !is.na(agg_hits) ~ "ambiguous",
      !is.na(court_hits) ~ "courtship",
      !is.na(agg_hits)   ~ "aggression",
      TRUE               ~ "unknown"
    )
  )

# Per-type aggregation (curated)
type_curated <- annot %>%
  group_by(type) %>%
  summarise(
    n_cells = n(),
    court_any = any(!is.na(court_hits)),
    agg_any   = any(!is.na(agg_hits)),
    court_examples = paste(unique(na.omit(court_hits)), collapse = " || "),
    agg_examples   = paste(unique(na.omit(agg_hits)),   collapse = " || "),
    fru_dsx_values = if ("fru_dsx" %in% present_cols) paste(sort(unique(na.omit(fru_dsx))), collapse = ";") else NA_character_,
    synonyms_values = if ("synonyms" %in% present_cols) paste(sort(unique(na.omit(synonyms))), collapse = ";") else NA_character_,
    flywire_type_values = if ("flywire_type" %in% present_cols) paste(sort(unique(na.omit(flywire_type))), collapse = ";") else NA_character_,
    hemibrain_type_values = if ("hemibrain_type" %in% present_cols) paste(sort(unique(na.omit(hemibrain_type))), collapse = ";") else NA_character_,
    supertype_values = if ("supertype" %in% present_cols) paste(sort(unique(na.omit(supertype))), collapse = ";") else NA_character_,
    itolee_values = if ("itolee_hl" %in% present_cols) paste(sort(unique(na.omit(itolee_hl))), collapse = ";") else NA_character_,
    truman_values = if ("truman_hl" %in% present_cols) paste(sort(unique(na.omit(truman_hl))), collapse = ";") else NA_character_,
    .groups = "drop"
  ) %>%
  mutate(class_guess = case_when(
    court_any & agg_any ~ "ambiguous",
    court_any ~ "courtship",
    agg_any   ~ "aggression",
    TRUE      ~ "unknown"
  ))

cur_path <- file.path(out_dir, "p1_metadata_curated.csv")
write.csv(type_curated, cur_path, row.names = FALSE)
cat("\nWrote:", cur_path, "\n")

# Identify ambiguous / dual annotation cells
dual_cells <- annot %>% filter(class_guess == "ambiguous") %>%
  select(any_of(c("bodyid", "type", "court_hits", "agg_hits")))
cat("\nDual-annotation cells:", nrow(dual_cells), "\n")

# ---- Per-column informativeness: count distinct values across P1 pool ----
informativeness <- data.frame(
  column = summary_cols,
  n_distinct_nonNA = as.integer(global_counts),
  n_cells_nonNA = sapply(summary_cols, function(cn) sum(!is.na(p1_meta[[cn]]) & p1_meta[[cn]] != "")),
  row.names = NULL
)
cat("\nInformativeness:\n")
print(informativeness)

# ---- Build narrative summary ----
n_types <- length(unique(p1_meta$type))
n_cells <- nrow(p1_meta)
n_court_types <- sum(type_curated$class_guess == "courtship")
n_agg_types   <- sum(type_curated$class_guess == "aggression")
n_amb_types   <- sum(type_curated$class_guess == "ambiguous")
n_unk_types   <- sum(type_curated$class_guess == "unknown")

court_types <- type_curated$type[type_curated$class_guess %in% c("courtship","ambiguous")]
agg_types   <- type_curated$type[type_curated$class_guess %in% c("aggression","ambiguous")]
amb_types   <- type_curated$type[type_curated$class_guess == "ambiguous"]

lines <- c(
  "P1 metadata enumeration -- agent01 findings",
  sprintf("Date: %s", Sys.Date()),
  sprintf("Source: mba (male-cns v0.9); filter type ~ ^P1_"),
  sprintf("P1 distinct types: %d | P1 cells: %d", n_types, n_cells),
  "",
  "Columns examined and per-column distinct non-NA values across P1 pool:",
  paste(capture.output(print(informativeness, row.names = FALSE)), collapse = "\n"),
  "",
  "Classification counts (per P1 type):",
  sprintf("  courtship  = %d", n_court_types),
  sprintf("  aggression = %d", n_agg_types),
  sprintf("  ambiguous  = %d", n_amb_types),
  sprintf("  unknown    = %d", n_unk_types),
  "",
  "Courtship-suggesting P1 types:",
  if (length(setdiff(court_types, amb_types))) paste("  ", paste(setdiff(court_types, amb_types), collapse = ", ")) else "  (none)",
  "",
  "Aggression-suggesting P1 types:",
  if (length(setdiff(agg_types, amb_types))) paste("  ", paste(setdiff(agg_types, amb_types), collapse = ", ")) else "  (none)",
  "",
  "Ambiguous (both courtship + aggression keywords) P1 types:",
  if (length(amb_types)) paste("  ", paste(amb_types, collapse = ", ")) else "  (none)",
  "",
  "Dual-annotation cells (bodyid-level):"
)
if (nrow(dual_cells) > 0) {
  lines <- c(lines, paste(capture.output(print(dual_cells, row.names = FALSE)), collapse = "\n"))
} else {
  lines <- c(lines, "  (none)")
}

lines <- c(lines, "",
  "Keyword patterns used:",
  sprintf("  courtship:  %s", court_pat),
  sprintf("  aggression: %s", agg_pat),
  "",
  "Confidence note:",
  "  Classification is keyword-based on text metadata only. fru_dsx and synonyms",
  "  are typically the most load-bearing; superclass/subclass rarely discriminate",
  "  between courtship and aggression P1 sub-populations. Absence of keyword hits",
  "  does NOT imply the neuron is non-courtship/non-aggression -- many P1 types",
  "  in the male connectome have sparse literature annotations. Downstream",
  "  behavioral assignment should be cross-checked with published P1a/pC1/aSP-g",
  "  references (Koganezawa/Kimura; Watanabe et al; Asahina et al)."
)

findings_path <- file.path(out_dir, "agent01_findings.txt")
writeLines(lines, findings_path)
cat("\nWrote:", findings_path, "\n")

cat("\n=== DONE ===\n")
