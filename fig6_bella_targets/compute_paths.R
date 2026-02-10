# =============================================================================
# Figure 6 (Bella's targets): Compute strongest paths to third-order neurons
# =============================================================================
# Run this FIRST before any panel scripts.
# This computes 50 strongest paths from each of 7 modalities to Bella's
# third-order target neurons (downstream of M cells, F cells, IR cells).
#
# Usage:
#   source("/Users/fkampf/Documents/pheromone.paper/fig6_bella_targets/compute_paths.R")
#
# This will take ~10-30 minutes depending on your machine.
# Results are cached to feather files -- re-running skips already-computed paths.
# =============================================================================

project_root <- "/Users/fkampf/Documents/pheromone.paper"
feather_dir  <- file.path(project_root, "feather")
paths_dir    <- file.path(feather_dir, "strongest.paths")

# -- Libraries & helpers -------------------------------------------------------
library(arrow)
library(dplyr)
library(malecns)
library(neuprintr)
library(igraph)

source(file.path(project_root, "R", "utils.R"))
source(file.path(project_root, "R", "data_processing.R"))
source(file.path(project_root, "R", "path_analysis.R"))

# -- Login & load data ---------------------------------------------------------
neuprint_login(server = "https://neuprint-cns.janelia.org")
choose_mcns()

data <- load_all_data(
  cache_dir           = feather_dir,
  force_recompute     = FALSE,
  set_ppk25_glutamate = TRUE
)

mba            <- data$mba
graph.general  <- data$graph

# =============================================================================
# Define Bella's target neuron types
# =============================================================================
# From Bella's figure: third-order cell types downstream of M, F, IR cells
#
# We search mba for exact matches first, then fuzzy matches for any that
# don't match exactly. The type names in neuprint may differ slightly from
# the labels in the figure.
# =============================================================================

# Candidate type names from Bella's figure
bella_targets_raw <- list(
  M_downstream = c(
    "mAL_m1", "mAL_m5a", "mAL_m5b", "mAL_m5c",  # mAL_m5a-c expanded
    "mAL_m8", "mAL_m3c", "AVLP494m", "SIP105m",
    "AVLP711m", "IN05B002", "mAL_m6", "SIP119m",
    "VES206m"
  ),
  F_downstream = c(
    "mAL_m1", "mAL_m2b", "AVLP743m", "AVLP597",
    "P1_3c",
    "IN05B002",
    "IN23B006", "IN23B007", "IN23B009", "IN23B056",  # IN23B006,7,9,56
    "IN11A020"
  ),
  IR_downstream = c(
    "IN05B022", "LH004m", "AVLP743m", "mAL_m1",
    "LH007m", "DNd02"
  )
)

# -- Resolve type names against mba database -----------------------------------

all_mba_types <- unique(mba$type)

resolve_types <- function(candidates, mba_types, mba_df) {
  resolved <- character(0)
  unresolved <- character(0)

  for (cand in candidates) {
    # Exact match
    if (cand %in% mba_types) {
      resolved <- c(resolved, cand)
      next
    }

    # Try case-insensitive exact match
    ci_match <- mba_types[tolower(mba_types) == tolower(cand)]
    if (length(ci_match) > 0) {
      resolved <- c(resolved, ci_match)
      next
    }

    # Try grep match (the candidate as a fixed substring)
    grep_match <- mba_types[grepl(cand, mba_types, fixed = TRUE)]
    if (length(grep_match) > 0) {
      resolved <- c(resolved, grep_match)
      next
    }

    # Try matching without underscores (in case naming differs)
    cand_nounderscore <- gsub("_", "", cand)
    grep_match2 <- mba_types[grepl(cand_nounderscore, gsub("_", "", mba_types), fixed = TRUE)]
    if (length(grep_match2) > 0) {
      resolved <- c(resolved, grep_match2)
      next
    }

    # Try synonym search
    syn_match <- mba_df %>%
      filter(grepl(cand, synonyms, fixed = TRUE)) %>%
      pull(type) %>%
      unique()
    if (length(syn_match) > 0) {
      resolved <- c(resolved, syn_match)
      next
    }

    unresolved <- c(unresolved, cand)
  }

  list(resolved = unique(resolved), unresolved = unresolved)
}

message("\n====== Resolving Bella's target neuron types ======\n")

bella_targets <- list()
for (group_name in names(bella_targets_raw)) {
  result <- resolve_types(bella_targets_raw[[group_name]], all_mba_types, mba)
  bella_targets[[group_name]] <- result$resolved

  message(sprintf("\n--- %s ---", group_name))
  message(sprintf("  Resolved (%d): %s", length(result$resolved),
                  paste(result$resolved, collapse = ", ")))
  if (length(result$unresolved) > 0) {
    message(sprintf("  UNRESOLVED (%d): %s", length(result$unresolved),
                    paste(result$unresolved, collapse = ", ")))
  }
}

# All unique targets across groups
all_bella_types <- unique(unlist(bella_targets))
message(sprintf("\nTotal unique target types: %d", length(all_bella_types)))
message(paste(all_bella_types, collapse = ", "))

# Verify they exist as graph nodes
graph_nodes <- V(graph.general)$name
in_graph <- all_bella_types %in% graph_nodes
if (!all(in_graph)) {
  message(sprintf("\nWARNING: %d types not found as graph nodes: %s",
                  sum(!in_graph),
                  paste(all_bella_types[!in_graph], collapse = ", ")))
  message("These will be skipped in path computation.")
}

bella_types_in_graph <- all_bella_types[in_graph]
message(sprintf("\nTarget types available in graph: %d", length(bella_types_in_graph)))

# =============================================================================
# Define start (source) neuron types -- same 7 modalities as original fig6
# =============================================================================

start.types.DA1  <- c("ORN_DA1")
start.types.VA1v <- c("ORN_VA1v")
start.types.VA1d <- c("ORN_VA1d")
start.types.aud  <- "JO-B"
start.types.vis  <- mba %>%
  filter(grepl("LC10", type)) %>%
  pull(type) %>%
  unique()
start.types.ppk23 <- mba %>%
  filter(grepl("ppk23", receptor_type)) %>%
  pull(type) %>%
  unique()
start.types.ppk25 <- mba %>%
  filter(grepl("ppk25", receptor_type)) %>%
  pull(type) %>%
  unique()

modalities <- list(
  DA1   = start.types.DA1,
  VA1v  = start.types.VA1v,
  VA1d  = start.types.VA1d,
  aud   = start.types.aud,
  vis   = start.types.vis,
  ppk23 = start.types.ppk23,
  ppk25 = start.types.ppk25
)

# =============================================================================
# Compute paths: 50 strongest from each modality to bella targets
# =============================================================================

n_paths <- 50
target_label <- "bella"

message("\n====== Computing strongest paths ======\n")

for (mod_name in names(modalities)) {
  fname <- file.path(paths_dir,
    sprintf("strongest.%d.paths.%s.2.%s.feather", n_paths, mod_name, target_label))

  if (!load_or_execute(fname)) {
    message(sprintf("  [CACHED] %s -> %s: %s", mod_name, target_label, basename(fname)))
    next
  }

  message(sprintf("  [COMPUTING] %s -> %s (%d starts x %d targets)...",
                  mod_name, target_label,
                  length(modalities[[mod_name]]), length(bella_types_in_graph)))

  t0 <- Sys.time()
  res <- find_k_strongest_paths_yen(
    g       = graph.general,
    starts  = modalities[[mod_name]],
    targets = bella_types_in_graph,
    n_paths = n_paths,
    mba     = mba
  )
  elapsed <- round(difftime(Sys.time(), t0, units = "mins"), 1)

  res$df$dataset <- "bella"
  write_feather(res$df, fname)

  message(sprintf("    -> %d paths found in %s min, saved to %s",
                  nrow(res$df), elapsed, basename(fname)))
}

# =============================================================================
# Also save the target group membership for downstream use
# =============================================================================

bella_groups_df <- bind_rows(
  lapply(names(bella_targets), function(grp) {
    tibble(type = bella_targets[[grp]], target_group = grp)
  })
)
# Some types appear in multiple groups -- keep all memberships
saveRDS(bella_groups_df,
        file.path(paths_dir, "bella_target_groups.rds"))
saveRDS(bella_targets,
        file.path(paths_dir, "bella_targets_list.rds"))

message("\n====== Done! ======")
message("Path feather files saved in: ", paths_dir)
message("Target group metadata saved as: bella_target_groups.rds, bella_targets_list.rds")
message("\nNext step: source fig6_bella_targets/setup.R or render panel scripts.")
