# =============================================================================
# Combinatorial Signal Flow Analysis: Data Export for Python
# =============================================================================
# Exports cached adjacency matrices and metadata to Python-compatible formats.
# Run once before the Python pipeline:
#   Rscript export_for_python.R
# =============================================================================

library(dplyr)
library(arrow)
library(Matrix)
library(jsonlite)

# -- Paths -------------------------------------------------------------------
project_root <- "/Users/fkampf/Documents/pheromone.paper"
export_dir   <- file.path(project_root, "analyses", "combinatorial_signal_flow", "data")
feather_dir  <- file.path(project_root, "feather")

dir.create(export_dir, recursive = TRUE, showWarnings = FALSE)

# -- Source helpers ----------------------------------------------------------
source(file.path(project_root, "R", "utils.R"))
source(file.path(project_root, "R", "data_processing.R"))

# -- Load core data from cache -----------------------------------------------
message("Loading cached data...")
data <- load_all_data(
  cache_dir           = feather_dir,
  force_recompute     = FALSE,
  set_ppk25_glutamate = TRUE
)

mba            <- data$mba
adj.matrix     <- data$adj.matrix       # post-normalized (col sums ~1)
adj.matrix.pre <- data$adj.matrix.pre   # pre-normalized  (row sums ~1)
adj.matrix.raw <- data$adj.matrix.raw   # raw synapse counts

# =============================================================================
# 1. Export sparse adjacency matrices as Matrix Market (.mtx)
# =============================================================================
message("Exporting adjacency matrices...")

writeMM(adj.matrix,     file.path(export_dir, "adj_matrix_post.mtx"))
writeMM(adj.matrix.pre, file.path(export_dir, "adj_matrix_pre.mtx"))
writeMM(adj.matrix.raw, file.path(export_dir, "adj_matrix_raw.mtx"))

message(sprintf("  Matrix dimensions: %d x %d", nrow(adj.matrix), ncol(adj.matrix)))
message(sprintf("  Non-zero entries:  %d", nnzero(adj.matrix)))

# =============================================================================
# 2. Export type name mapping (shared dimnames for all matrices)
# =============================================================================
message("Exporting type names...")

type_names <- data.frame(
  index = seq_len(nrow(adj.matrix)) - 1L,   # 0-based for Python
  type  = rownames(adj.matrix),
  stringsAsFactors = FALSE
)
write.csv(type_names, file.path(export_dir, "type_names.csv"), row.names = FALSE)

message(sprintf("  %d type names exported", nrow(type_names)))

# =============================================================================
# 3. Define and export sensory input channels
# =============================================================================
message("Defining sensory input channels...")

channels <- list(
  DA1      = c("ORN_DA1"),
  VA1v     = c("ORN_VA1v"),
  VA1d     = c("ORN_VA1d"),
  auditory = c("JO-B"),
  visual   = mba %>% filter(grepl("LC10", type)) %>% pull(type) %>% unique(),
  ppk23    = mba %>% filter(grepl("ppk23", receptor_type)) %>% pull(type) %>% unique(),
  ppk25    = mba %>% filter(grepl("ppk25", receptor_type)) %>% pull(type) %>% unique()
)

# Validate: check which types exist in the adjacency matrix
all_types <- rownames(adj.matrix)
for (ch in names(channels)) {
  present <- channels[[ch]][channels[[ch]] %in% all_types]
  missing <- channels[[ch]][!channels[[ch]] %in% all_types]
  if (length(missing) > 0) {
    message(sprintf("  WARNING: %s has %d types not in adj matrix: %s",
                    ch, length(missing), paste(missing, collapse = ", ")))
  }
  message(sprintf("  %s: %d types (%d in matrix)", ch, length(channels[[ch]]), length(present)))
}

write_json(channels, file.path(export_dir, "channels.json"),
           pretty = TRUE, auto_unbox = FALSE)

# =============================================================================
# 4. Define and export target neuron sets
# =============================================================================
message("Defining target neuron sets...")

targets <- list(
  aspf = mba %>%
    filter(grepl("aSP-f", synonyms)) %>%
    pull(type) %>%
    unique() %>%
    sort(),
  aspg = mba %>%
    filter(grepl("aSP-g", synonyms)) %>%
    pull(type) %>%
    unique() %>%
    sort()
)

# Load PPN1 / vAB3 downstream targets from cached RDS
ppn1_rds <- file.path(feather_dir, "target.PPN1.rds")
vab3_rds <- file.path(feather_dir, "target.vAB3.rds")

if (file.exists(ppn1_rds) && file.exists(vab3_rds)) {
  ppn1_targets <- readRDS(ppn1_rds)
  if (is.data.frame(ppn1_targets)) {
    ppn1_targets <- ppn1_targets$type %||% ppn1_targets[[1]]
  }
  ppn1_targets <- as.character(ppn1_targets)

  vab3_targets <- readRDS(vab3_rds)
  if (is.data.frame(vab3_targets)) {
    vab3_targets <- vab3_targets$type %||% vab3_targets[[1]]
  }
  vab3_targets <- as.character(vab3_targets)

  # Top 10 + first 3 shared (matching R analysis)
  shared <- intersect(vab3_targets, ppn1_targets)
  targets$PPN1_downstream <- unique(c(ppn1_targets[1:10], shared[1:3]))
  targets$vAB3_downstream <- unique(c(vab3_targets[1:10], shared[1:3]))

  # Full downstream sets
  targets$PPN1_downstream_all <- ppn1_targets
  targets$vAB3_downstream_all <- vab3_targets

  message(sprintf("  PPN1_downstream: %d types (top 10 + %d shared)",
                  length(targets$PPN1_downstream), min(3, length(shared))))
  message(sprintf("  vAB3_downstream: %d types (top 10 + %d shared)",
                  length(targets$vAB3_downstream), min(3, length(shared))))
  message(sprintf("  PPN1_downstream_all: %d types", length(targets$PPN1_downstream_all)))
  message(sprintf("  vAB3_downstream_all: %d types", length(targets$vAB3_downstream_all)))
  message(sprintf("  Shared types: %s", paste(head(shared, 3), collapse = ", ")))
} else {
  if (!file.exists(ppn1_rds))
    message("  WARNING: target.PPN1.rds not found — skipping PPN1 downstream targets")
  if (!file.exists(vab3_rds))
    message("  WARNING: target.vAB3.rds not found — skipping vAB3 downstream targets")
}

# Add mAL_all target group: all mAL types in the adjacency matrix
mal_all_types <- sort(all_types[grepl("^mAL", all_types)])
targets$mAL_all <- mal_all_types
# Add P1_all target group: all P1 types in the adjacency matrix
p1_all_types <- sort(all_types[grepl("^pC1", all_types)])
targets$P1_all <- p1_all_types
message(sprintf("  mAL_all: %d types", length(mal_all_types)))
message(sprintf("  P1_all: %d types", length(p1_all_types)))

message(sprintf("  aspf: %d types", length(targets$aspf)))
message(sprintf("  aspg: %d types", length(targets$aspg)))

# Validate targets against adj matrix
for (tg in names(targets)) {
  present <- targets[[tg]][targets[[tg]] %in% all_types]
  missing <- targets[[tg]][!targets[[tg]] %in% all_types]
  if (length(missing) > 0) {
    message(sprintf("  WARNING: %s has %d types not in adj matrix: %s",
                    tg, length(missing),
                    paste(head(missing, 5), collapse = ", ")))
  }
}

write_json(targets, file.path(export_dir, "targets.json"),
           pretty = TRUE, auto_unbox = FALSE)

# =============================================================================
# 5. Export neurotransmitter mapping per type
# =============================================================================
message("Exporting neurotransmitter mapping...")

inhibitory_nts <- c("gaba", "glycine", "histamine")

nt_mapping <- mba %>%
  filter(!is.na(type), type != "") %>%
  select(type, consensus_nt) %>%
  distinct(type, .keep_all = TRUE) %>%
  mutate(
    is_inhibitory = tolower(consensus_nt) %in% inhibitory_nts
  ) %>%
  arrange(type)

write.csv(nt_mapping, file.path(export_dir, "neurotransmitter_mapping.csv"),
          row.names = FALSE)

message(sprintf("  %d types with NT info (%d inhibitory)",
                nrow(nt_mapping), sum(nt_mapping$is_inhibitory, na.rm = TRUE)))

# =============================================================================
# 6. Export modality color palette
# =============================================================================
message("Exporting color palette...")

palette <- list(
  colors = list(
    DA1      = "#66C2A5",
    VA1v     = "#FC8D62",
    VA1d     = "#8DA0CB",
    auditory = "#E78AC3",
    visual   = "#A6D854",
    ppk23    = "#FFD92F",
    ppk25    = "#E5C494"
  ),
  order = c("DA1", "VA1v", "VA1d", "auditory", "visual", "ppk23", "ppk25"),
  group = list(
    DA1      = "olfactory",
    VA1v     = "olfactory",
    VA1d     = "olfactory",
    auditory = "auditory",
    visual   = "visual",
    ppk23    = "contact",
    ppk25    = "contact"
  ),
  group_colors = list(
    olfactory = "#7FC97F",
    auditory  = "#E78AC3",
    visual    = "#A6D854",
    contact   = "#FDB462"
  ),
  target_colors = list(
    aspf                 = "#E41A1C",
    aspg                 = "#377EB8",
    PPN1_downstream      = "#FF7F00",
    vAB3_downstream      = "#4DAF4A",
    PPN1_downstream_all  = "#FDBF6F",
    vAB3_downstream_all  = "#B2DF8A",
    mAL_all              = "#984EA3",
    P1_all               = "#E41A1C"
  )
)

write_json(palette, file.path(export_dir, "modality_colors.json"),
           pretty = TRUE, auto_unbox = TRUE)

# =============================================================================
message("\nExport complete!")
message(sprintf("Data exported to: %s", export_dir))
message("Files:")
message(paste(" ", list.files(export_dir), collapse = "\n"))
