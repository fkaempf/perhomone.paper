# =============================================================================
# Figure 5: Sensory Specialization of mAL Subtypes - Shared Setup
# =============================================================================
# Source this file at the top of each panel script:
#   source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")
# =============================================================================

# -- Project root ----------------------------------------------------------
project_root <- "/Users/fkampf/Documents/pheromone.paper"
fig5_dir     <- file.path(project_root, "figures", "fig5")
feather_dir  <- file.path(project_root, "feather")
paths_dir    <- file.path(feather_dir, "strongest.paths")

# -- Publication mode ---------------------------------------------------------
pub_mode <- TRUE

# -- Per-panel plot directory helper ----------------------------------------
panel_plot_dir <- function(name, fmt = "png", subdir = NULL) {
  panel <- sub("^(panel_[A-Z])_.*", "\\1", name)
  if (!is.null(subdir)) {
    pdir <- file.path(fig5_dir, "plots", panel, subdir, fmt)
  } else {
    pdir <- file.path(fig5_dir, "plots", panel, fmt)
  }
  dir.create(pdir, recursive = TRUE, showWarnings = FALSE)
  pdir
}

# -- Suppress RGL display warning (no X11 needed for 2D plots) -------------
options(rgl.useNULL = TRUE)

# -- Libraries -------------------------------------------------------------
library(arrow)
library(dplyr)
library(purrr)
library(tidyr)
library(tibble)
library(stringr)
library(reshape2)

library(ggplot2)
library(ggpubr)
library(ggExtra)
library(cowplot)
library(patchwork)
library(pheatmap)
library(RColorBrewer)
library(viridisLite)
library(scales)

library(igraph)
library(coconatfly)
library(fafbseg)
library(malecns)
library(neuprintr)

library(Matrix)

# -- Publication theme for ggplot ---------------------------------------------
theme_pub <- function(base_size = 8) {
  theme_minimal(base_size = base_size) %+replace%
    theme(
      plot.title       = element_blank(),
      plot.subtitle    = element_blank(),
      plot.margin      = margin(2, 2, 2, 2),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(linewidth = 0.3, color = "grey90"),
      axis.title       = element_text(size = rel(1)),
      axis.text        = element_text(size = rel(0.85)),
      axis.text.x      = element_text(size = rel(0.85), angle = 30, hjust = 1),
      legend.title     = element_text(size = rel(0.9)),
      legend.text      = element_text(size = rel(0.8)),
      legend.key.size  = unit(0.35, "cm"),
      legend.margin    = margin(0, 0, 0, 0),
      legend.spacing   = unit(0.1, "cm"),
      strip.text       = element_text(size = rel(0.9), face = "bold")
    )
}

# -- Source helper functions ------------------------------------------------
source(file.path(project_root, "R", "utils.R"))
source(file.path(project_root, "R", "data_processing.R"))
source(file.path(project_root, "R", "path_analysis.R"))
source(file.path(project_root, "R", "visualization.R"))
source(file.path(project_root, "R", "neuroglancer.R"))

# -- Neuprint login --------------------------------------------------------
neuprint_login(server = "https://neuprint-cns.janelia.org", dataset = "male-cns:v0.9")
choose_mcns()

# -- Load core data --------------------------------------------------------
data <- load_all_data(
  cache_dir           = feather_dir,
  force_recompute     = FALSE,
  set_ppk25_glutamate = TRUE
)

mba            <- data$mba
conn           <- data$conn
adj.matrix     <- data$adj.matrix
adj.matrix.pre <- data$adj.matrix.pre
adj.matrix.raw <- data$adj.matrix.raw
graph.general  <- data$graph

# -- Helper: drop list columns for safe row-binding ------------------------
drop_list_cols <- function(df) {
  list_cols <- names(df)[sapply(df, is.list)]
  if (length(list_cols) > 0) df <- df %>% dplyr::select(-all_of(list_cols))
  df
}

# -- Modality color palette ------------------------------------------------
modality_colors <- c(
  "DA1"      = "#66C2A5",
  "VA1v"     = "#FC8D62",
  "VA1d"     = "#8DA0CB",
  "auditory" = "#E78AC3",
  "visual"   = "#A6D854",
  "ppk23"    = "#FFD92F",
  "ppk25"    = "#E5C494"
)

modality_order <- c("DA1", "VA1v", "VA1d", "auditory", "visual", "ppk23", "ppk25")

modality_group <- c(
  "DA1" = "olfactory", "VA1v" = "olfactory", "VA1d" = "olfactory",
  "auditory" = "auditory", "visual" = "visual",
  "ppk23" = "contact", "ppk25" = "contact"
)

modality_group_colors <- c(
  "olfactory" = "#7FC97F",
  "auditory"  = "#E78AC3",
  "visual"    = "#A6D854",
  "contact"   = "#FDB462"
)

# =============================================================================
# mAL and P1 type discovery (data-driven)
# =============================================================================

# -- Discover ALL mAL types from connectome ----------------------------------
mal_subtypes <- mba %>%
  filter(grepl("^mAL", type)) %>%
  pull(type) %>%
  unique() %>%
  sort()

# Reference list of male-specific subtypes (for dimorphism annotation)
mal_m_subtypes <- c("mAL_m1", "mAL_m2a", "mAL_m2b", "mAL_m3a", "mAL_m3b",
                    "mAL_m3c", "mAL_m4", "mAL_m5a", "mAL_m5b", "mAL_m5c",
                    "mAL_m6", "mAL_m7", "mAL_m8", "mAL_m9", "mAL_m10")

message(sprintf("  mAL types discovered: %d (%d male-specific, %d shared)",
                length(mal_subtypes),
                sum(mal_subtypes %in% mal_m_subtypes),
                sum(!mal_subtypes %in% mal_m_subtypes)))

# -- Discover ALL P1 types from connectome -----------------------------------
# Search both mba and conn to catch all P1-prefixed types
p1_from_mba <- mba %>%
  filter(grepl("^P1", type)) %>%
  pull(type) %>% unique()

p1_from_conn <- unique(c(
  conn$pre_type[grepl("^P1", conn$pre_type)],
  conn$post_type[grepl("^P1", conn$post_type)]
))

p1_subtypes <- sort(unique(c(p1_from_mba, p1_from_conn)))

message(sprintf("  P1 types discovered: %d (%s)",
                length(p1_subtypes), paste(p1_subtypes, collapse = ", ")))
if (length(setdiff(p1_from_conn, p1_from_mba)) > 0) {
  message(sprintf("  P1 types in conn but not mba: %s",
                  paste(setdiff(p1_from_conn, p1_from_mba), collapse = ", ")))
}

# -- Neurotransmitter identity per mAL type -----------------------------------
# Curated values for male-specific types
mal_nt_curated <- c(
  "mAL_m1"  = "GABA",    "mAL_m2a" = "unclear", "mAL_m2b" = "GABA",
  "mAL_m3a" = "unclear", "mAL_m3b" = "unclear", "mAL_m3c" = "GABA",
  "mAL_m4"  = "GABA",    "mAL_m5a" = "GABA",    "mAL_m5b" = "GABA",
  "mAL_m5c" = "GABA",    "mAL_m6"  = "unclear", "mAL_m7"  = "GABA",
  "mAL_m8"  = "GABA",    "mAL_m9"  = "GABA",    "mAL_m10" = "GABA"
)

# Normalize NT strings to our canonical names
normalize_nt <- function(nt_str) {
  nt_lower <- tolower(trimws(nt_str))
  case_when(
    nt_lower %in% c("gaba", "gabaergic")                          ~ "GABA",
    nt_lower %in% c("ach", "acetylcholine", "cholinergic")        ~ "ACh",
    nt_lower %in% c("glut", "glutamate", "glutamatergic")         ~ "Glut",
    nt_lower %in% c("da", "dopamine", "dopaminergic")             ~ "DA",
    nt_lower %in% c("5ht", "serotonin", "serotonergic")           ~ "5HT",
    nt_lower %in% c("oct", "octopamine", "octopaminergic")        ~ "Oct",
    nt_lower %in% c("unclear", "mixed")                           ~ "unclear",
    nt_lower %in% c("unknown", "", "na")                          ~ "unknown",
    TRUE                                                           ~ nt_str
  )
}

# Build NT for all types: lookup from mba, override with curated
mal_nt <- setNames(rep("unknown", length(mal_subtypes)), mal_subtypes)
# Try mba lookup (top_nt column if available)
nt_col <- intersect(c("top_nt", "predicted_nt", "nt_type"), colnames(mba))
if (length(nt_col) > 0) {
  mba_nt_lookup <- mba %>%
    filter(type %in% mal_subtypes, !is.na(.data[[nt_col[1]]]), .data[[nt_col[1]]] != "") %>%
    group_by(type) %>%
    summarise(nt = names(sort(table(.data[[nt_col[1]]]), decreasing = TRUE))[1],
              .groups = "drop")
  for (i in seq_len(nrow(mba_nt_lookup))) {
    mal_nt[mba_nt_lookup$type[i]] <- normalize_nt(mba_nt_lookup$nt[i])
  }
}
# Override with curated values (higher confidence)
for (t in names(mal_nt_curated)) {
  if (t %in% names(mal_nt)) mal_nt[t] <- mal_nt_curated[t]
}

message(sprintf("  NT values: %s",
  paste(sprintf("%s=%d", names(table(mal_nt)), as.integer(table(mal_nt))),
        collapse = ", ")))

# -- Dimorphism class ---------------------------------------------------------
mal_dimorphism <- setNames(
  ifelse(mal_subtypes %in% mal_m_subtypes, "male_specific", "shared"),
  mal_subtypes
)

# -- Color palettes for annotations ------------------------------------------
nt_colors <- c(
  "GABA"    = "#984EA3",
  "ACh"     = "#E41A1C",
  "Glut"    = "#4DAF4A",
  "DA"      = "#FF7F00",
  "5HT"     = "#A65628",
  "Oct"     = "#F781BF",
  "unknown" = "#BDBDBD",
  "unclear" = "#999999"
)

# Ensure all NT values in mal_nt have a color entry
for (nt_val in unique(mal_nt)) {
  if (!nt_val %in% names(nt_colors)) {
    message(sprintf("  WARNING: NT value '%s' has no color -- assigning grey", nt_val))
    nt_colors[nt_val] <- "#BDBDBD"
  }
}

dimorphism_colors <- c(
  "male_specific" = "#FF7F00",
  "shared"        = "#A6CEE3"
)

# =============================================================================
# Sensory channel definitions (from channels.json)
# =============================================================================

channel_neurons <- list(
  DA1      = c("ORN_DA1"),
  VA1v     = c("ORN_VA1v"),
  VA1d     = c("ORN_VA1d"),
  auditory = c("JO-B"),
  visual   = c("LC10c-2", "LC10e", "LC10b", "LC10a", "LC10d", "LC10_unclear", "LC10c-1"),
  ppk23    = c("WG4 _ADMN", "LgLG1a _MesoLN", "LgLG7 _ProLN", "LgLG1a",
               "LgLG1a _ProLN", "LgLG7", "LgLG1a _MetaLN", "LgLG6 _ProLN",
               "LgLG6", "WG4"),
  ppk25    = c("LgLG1b", "WG3 _ADMN", "LgLG5", "LgLG5 _ProLN",
               "LgLG1b _MesoLN", "LgLG1b _ProLN", "LgLG1b _MetaLN",
               "WG3", "LgLG8", "LgLG8 _ProLN")
)

# Short modality labels for feather file naming
modality_file_labels <- c(
  "DA1" = "DA1", "VA1v" = "VA1v", "VA1d" = "VA1d",
  "auditory" = "aud", "visual" = "vis",
  "ppk23" = "ppk23", "ppk25" = "ppk25"
)

# =============================================================================
# Load or compute path strengths (K strongest paths per modality -> mAL)
# =============================================================================

n_paths_mal <- 50
target_name_mal <- "mAL_all"

# -- Helper to load cached paths for one modality ---------------------------
load_mal_modality_paths <- function(mod_label, target_name, n_paths) {
  fname <- file.path(paths_dir,
    sprintf("strongest.%d.paths.%s.2.%s.feather", n_paths, mod_label, target_name))
  if (file.exists(fname)) {
    df <- read_feather(fname)
    df <- drop_list_cols(df)
    return(df)
  }
  return(NULL)
}

# -- Compute and cache paths if not already present -------------------------
compute_and_cache_mal_paths <- function() {
  modality_labels_map <- c(
    "DA1" = "DA1", "VA1v" = "VA1v", "VA1d" = "VA1d",
    "aud" = "auditory", "vis" = "visual",
    "ppk23" = "ppk23", "ppk25" = "ppk25"
  )

  dfs <- list()
  for (mod in modality_order) {
    mod_file_label <- modality_file_labels[[mod]]
    cached <- load_mal_modality_paths(mod_file_label, target_name_mal, n_paths_mal)

    if (!is.null(cached)) {
      # Validate that cache covers the current target set
      cached_targets <- unique(cached$end)
      expected_targets <- mal_subtypes[mal_subtypes %in% V(graph.general)$name]
      missing_targets <- setdiff(expected_targets, cached_targets)

      if (length(missing_targets) > 0) {
        message(sprintf("  Cache stale for %s: missing %d targets (%s). Recomputing...",
                        mod, length(missing_targets),
                        paste(head(missing_targets, 5), collapse = ", ")))
        cached <- NULL  # Force recompute
      } else {
        cached$modality <- mod
        cached$target_set <- target_name_mal
        dfs[[mod]] <- cached
        message(sprintf("  Loaded cached paths: %s -> mAL (%d paths, %d targets)",
                        mod, nrow(cached), length(cached_targets)))
      }
    }

    if (is.null(cached)) {
      message(sprintf("  Computing %d strongest paths: %s -> mAL ...", n_paths_mal, mod))
      starts <- channel_neurons[[mod]]
      # Filter starts to those present in graph
      starts <- starts[starts %in% V(graph.general)$name]
      targets <- mal_subtypes[mal_subtypes %in% V(graph.general)$name]

      if (length(starts) == 0 || length(targets) == 0) {
        message(sprintf("    SKIP: no valid starts/targets for %s", mod))
        next
      }

      # Add log_weight to graph edges
      g <- graph.general
      w <- E(g)$weight
      w[!is.finite(w) | w <= 0] <- .Machine$double.eps
      E(g)$log_weight <- -log(w)

      result <- find_k_strongest_paths_yen(
        g       = g,
        starts  = starts,
        targets = targets,
        mba     = mba,
        n_paths = n_paths_mal
      )

      df <- result$df
      if (nrow(df) > 0) {
        df$modality <- mod
        df$target_set <- target_name_mal
        # Cache to feather
        fname <- file.path(paths_dir,
          sprintf("strongest.%d.paths.%s.2.%s.feather", n_paths_mal, mod_file_label, target_name_mal))
        write_feather(df, fname)
        dfs[[mod]] <- df
        message(sprintf("    Cached %d paths to %s", nrow(df), basename(fname)))
      } else {
        message(sprintf("    No paths found for %s", mod))
      }
    }
  }
  bind_rows(dfs)
}

message("Loading/computing mAL path strengths...")
mal_paths <- compute_and_cache_mal_paths()

# =============================================================================
# Build strength matrices from paths (same approach as fig6)
# =============================================================================

compute_strength_matrix <- function(paths_df, normalize = FALSE) {
  mat <- paths_df %>%
    group_by(end, modality) %>%
    summarise(total_strength = sum(strength, na.rm = TRUE), .groups = "drop") %>%
    pivot_wider(names_from = modality, values_from = total_strength, values_fill = 0) %>%
    column_to_rownames("end")
  for (mod in modality_order) {
    if (!mod %in% colnames(mat)) mat[[mod]] <- 0
  }
  mat <- mat[, intersect(modality_order, colnames(mat))]
  if (normalize) {
    col_max <- apply(mat, 2, max, na.rm = TRUE)
    col_max[col_max == 0] <- 1
    mat <- sweep(mat, 2, col_max, "/")
  }
  as.matrix(mat)
}

compute_valence_strength <- function(paths_df, val) {
  paths_df %>%
    filter(valence == val) %>%
    group_by(end, modality) %>%
    summarise(total_strength = sum(strength, na.rm = TRUE), .groups = "drop") %>%
    pivot_wider(names_from = modality, values_from = total_strength, values_fill = 0) %>%
    column_to_rownames("end") %>%
    { m <- .
      for (mod in modality_order) if (!mod %in% colnames(m)) m[[mod]] <- 0
      m <- m[, intersect(modality_order, colnames(m))]
      as.matrix(m)
    }
}

# Raw strength (sum of all path strengths regardless of valence)
mal_strength     <- compute_strength_matrix(mal_paths)
mal_strength_exc <- compute_valence_strength(mal_paths, "excitatory")
mal_strength_inh <- compute_valence_strength(mal_paths, "inhibitory")

# Ensure all mAL types present in matrices (add zero rows if missing)
ensure_all_mal_types <- function(mat, types) {
  missing <- setdiff(types, rownames(mat))
  if (length(missing) > 0) {
    zero_rows <- matrix(0, nrow = length(missing), ncol = ncol(mat),
                        dimnames = list(missing, colnames(mat)))
    mat <- rbind(mat, zero_rows)
  }
  mat[intersect(types, rownames(mat)), , drop = FALSE]
}

# Build matrices for ALL mAL types
mal_strength     <- ensure_all_mal_types(mal_strength, mal_subtypes)
mal_strength_exc <- ensure_all_mal_types(mal_strength_exc, mal_subtypes)
mal_strength_inh <- ensure_all_mal_types(mal_strength_inh, mal_subtypes)

# Signed activation = excitatory - inhibitory
mal_activation_matrix <- mal_strength_exc - mal_strength_inh

# -- Build mAL annotation dataframe ------------------------------------------
mal_annot <- data.frame(
  subtype          = mal_subtypes,
  neurotransmitter = mal_nt[mal_subtypes],
  dimorphism       = mal_dimorphism[mal_subtypes],
  row.names        = mal_subtypes,
  stringsAsFactors = FALSE
)

# =============================================================================
# Load signal flow model results (for Panel I comparison)
# =============================================================================

sf_plots_dir <- file.path(project_root, "analyses", "combinatorial_signal_flow", "plots", "sigmoid_rectified")

screen_results <- read.csv(file.path(sf_plots_dir, "screen_results.csv"),
                           stringsAsFactors = FALSE)

mal_screen <- screen_results %>%
  filter(target_group == "mAL_all",
         target_type %in% mal_subtypes,
         n_channels == 1)

mal_all_combos <- screen_results %>%
  filter(target_group == "mAL_all",
         target_type %in% mal_subtypes)

pairwise_interactions <- read.csv(file.path(sf_plots_dir, "pairwise_interactions.csv"),
                                  stringsAsFactors = FALSE)

mal_ppk_interaction <- pairwise_interactions %>%
  filter(target_group == "mAL_all",
         target_type %in% mal_subtypes,
         ch1 == "ppk23", ch2 == "ppk25")

# Build signal flow activation matrix (for Panel I comparison with path-based)
sf_activation_matrix <- mal_screen %>%
  select(target_type, combination, activation) %>%
  pivot_wider(names_from = combination, values_from = activation, values_fill = 0) %>%
  column_to_rownames("target_type")
for (mod in modality_order) {
  if (!mod %in% colnames(sf_activation_matrix)) sf_activation_matrix[[mod]] <- 0
}
sf_activation_matrix <- as.matrix(sf_activation_matrix[, modality_order])

# -- P1 signal flow data -------------------------------------------------------
p1_screen <- screen_results %>%
  filter(target_group == "P1_all",
         target_type %in% p1_subtypes,
         n_channels == 1)

p1_all_combos <- screen_results %>%
  filter(target_group == "P1_all",
         target_type %in% p1_subtypes)

# Build P1 signal flow activation matrix (single-channel net_input)
p1_sf_activation_matrix <- p1_screen %>%
  select(target_type, combination, net_input) %>%
  pivot_wider(names_from = combination, values_from = net_input, values_fill = 0) %>%
  column_to_rownames("target_type")
for (mod in modality_order) {
  if (!mod %in% colnames(p1_sf_activation_matrix)) p1_sf_activation_matrix[[mod]] <- 0
}
p1_sf_activation_matrix <- as.matrix(p1_sf_activation_matrix[, modality_order])

# Build mAL signal flow net_input matrix (pre-nonlinearity, for Panel L)
mal_sf_net_input_matrix <- mal_screen %>%
  select(target_type, combination, net_input) %>%
  pivot_wider(names_from = combination, values_from = net_input, values_fill = 0) %>%
  column_to_rownames("target_type")
for (mod in modality_order) {
  if (!mod %in% colnames(mal_sf_net_input_matrix)) mal_sf_net_input_matrix[[mod]] <- 0
}
mal_sf_net_input_matrix <- as.matrix(mal_sf_net_input_matrix[, modality_order])

# =============================================================================
# Save plot helpers (identical to fig6)
# =============================================================================

# -- Save heatmap with fixed annotations to file ---------------------------
save_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     filename, width = 8, height = 10,
                                     total_annot_cm = 1.5, ...) {
  library(grid)
  library(gtable)

  # Convert empty annotation data.frames (0 columns) to NA for pheatmap
  if (is.data.frame(row_annot) && ncol(row_annot) == 0) row_annot <- NA
  if (is.data.frame(col_annot) && ncol(col_annot) == 0) col_annot <- NA

  n_bands <- if (is.data.frame(row_annot)) ncol(row_annot) else 0
  band_w  <- if (n_bands > 0) unit(total_annot_cm / n_bands, "cm") else unit(0, "cm")

  dots <- list(...)
  if (pub_mode) {
    dots$main <- ""
    if (!is.null(dots$fontsize_row) && dots$fontsize_row > 5) dots$fontsize_row <- 5
    if (!is.null(dots$fontsize_col) && dots$fontsize_col > 8) dots$fontsize_col <- 8
  }

  is_pdf <- grepl("\\.pdf$", filename, ignore.case = TRUE)
  if (is_pdf) pdf(filename, width = width, height = height)
  else        png(filename, width = width, height = height, units = "in", res = 300)

  hm <- do.call(pheatmap, c(list(
    mat               = mat,
    annotation_row    = row_annot,
    annotation_col    = col_annot,
    annotation_colors = ann_colors,
    silent            = TRUE
  ), dots))

  gt <- hm$gtable
  ann_idx <- grep("row_annotation", gt$layout$name)
  for (idx in ann_idx) {
    col_pos <- gt$layout$l[idx]
    gt$widths[col_pos] <- band_w
  }
  grid.newpage()
  grid.draw(gt)
  dev.off()
  invisible(hm)
}

# -- Save heatmap in BOTH orientations (vertical + horizontal) -------------
save_heatmap_both_orientations <- function(mat, row_annot, col_annot, ann_colors,
                                           name, width = 8, height = 10,
                                           total_annot_cm = 1.5, subdir = NULL, ...) {
  pdir_png <- panel_plot_dir(name, "png", subdir = subdir)
  pdir_pdf <- panel_plot_dir(name, "pdf", subdir = subdir)

  save_heatmap_fixed_annot(
    mat, row_annot, col_annot, ann_colors,
    filename = file.path(pdir_png, paste0(name, ".png")),
    width = width, height = height, total_annot_cm = total_annot_cm, ...
  )
  save_heatmap_fixed_annot(
    mat, row_annot, col_annot, ann_colors,
    filename = file.path(pdir_pdf, paste0(name, ".pdf")),
    width = width, height = height, total_annot_cm = total_annot_cm, ...
  )

  # Horizontal (transposed)
  mat_t <- t(mat)
  dots <- list(...)
  cr <- dots$cluster_rows
  cc <- dots$cluster_cols
  if (!is.null(cr)) dots$cluster_cols <- cr
  if (!is.null(cc)) dots$cluster_rows <- cc
  h_width  <- max(width, height)
  h_height <- min(width, height)

  do.call(save_heatmap_fixed_annot, c(list(
    mat = mat_t, row_annot = col_annot, col_annot = row_annot,
    ann_colors = ann_colors,
    filename = file.path(pdir_png, paste0(name, "_horizontal.png")),
    width = h_width, height = h_height, total_annot_cm = total_annot_cm
  ), dots))

  do.call(save_heatmap_fixed_annot, c(list(
    mat = mat_t, row_annot = col_annot, col_annot = row_annot,
    ann_colors = ann_colors,
    filename = file.path(pdir_pdf, paste0(name, "_horizontal.pdf")),
    width = h_width, height = h_height, total_annot_cm = total_annot_cm
  ), dots))
}

# -- Save plot helper ------------------------------------------------------
save_fig5_plot <- function(plot_obj, name, width = 10, height = 8, subdir = NULL) {
  pdir_png <- panel_plot_dir(name, "png", subdir = subdir)
  pdir_pdf <- panel_plot_dir(name, "pdf", subdir = subdir)

  if (pub_mode) {
    plot_obj <- plot_obj + theme_pub()
  }

  ggsave(file.path(pdir_png, paste0(name, ".png")),
         plot = plot_obj, width = width, height = height, dpi = 300)
  ggsave(file.path(pdir_pdf, paste0(name, ".pdf")),
         plot = plot_obj, width = width, height = height)
}

# -- Save panel narrative --------------------------------------------------
# Writes a detailed explanation of the panel to a text file in the panel's
# plot directory. Called at the end of each panel Rmd with data-driven text.
save_panel_narrative <- function(panel_name, narrative_text) {
  narr_dir <- file.path(fig5_dir, "plots", panel_name)
  dir.create(narr_dir, recursive = TRUE, showWarnings = FALSE)
  fpath <- file.path(narr_dir, paste0(panel_name, "_narrative.txt"))
  writeLines(narrative_text, fpath)
  message(sprintf("  Narrative saved: %s", fpath))
  invisible(fpath)
}

# -- Shannon entropy -------------------------------------------------------
shannon_entropy <- function(x) {
  x <- x[x > 0]
  if (length(x) == 0) return(0)
  p <- x / sum(x)
  -sum(p * log2(p))
}

# -- Summary ---------------------------------------------------------------
message("Figure 5 setup complete.")
message(sprintf("  mAL types: %d (%d male-specific, %d shared)",
                length(mal_subtypes),
                sum(mal_dimorphism == "male_specific"),
                sum(mal_dimorphism == "shared")))
message(sprintf("  P1 types: %d", length(p1_subtypes)))
message(sprintf("  Path data: %d total paths across %d modalities",
                nrow(mal_paths), length(unique(mal_paths$modality))))
message(sprintf("  Strength matrix: %d x %d",
                nrow(mal_strength), ncol(mal_strength)))
message(sprintf("  Signed activation matrix: %d x %d",
                nrow(mal_activation_matrix), ncol(mal_activation_matrix)))
message(sprintf("  Signal flow screen results: %d rows for mAL",
                nrow(mal_screen)))
message(sprintf("  Signal flow all combos: %d rows",
                nrow(mal_all_combos)))
message(sprintf("  Pairwise ppk23+ppk25 interactions: %d mAL entries",
                nrow(mal_ppk_interaction)))
message(sprintf("  P1 signal flow screen results: %d rows",
                nrow(p1_screen)))
message(sprintf("  P1 signal flow all combos: %d rows",
                nrow(p1_all_combos)))
