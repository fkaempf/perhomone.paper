# =============================================================================
# Figure 6: Multimodal Sensory Integration - Shared Setup
# =============================================================================
# Source this file at the top of each panel script:
#   source("/Users/fkampf/Documents/pheromone.paper/fig6/setup.R")
# =============================================================================

# -- Project root ----------------------------------------------------------
project_root <- "/Users/fkampf/Documents/pheromone.paper"
fig6_dir     <- file.path(project_root, "fig6")
feather_dir  <- file.path(project_root, "feather")
paths_dir    <- file.path(feather_dir, "strongest.paths")
plot_dir_png <- file.path(fig6_dir, "plots", "png")
plot_dir_pdf <- file.path(fig6_dir, "plots", "pdf")

dir.create(plot_dir_png, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir_pdf, recursive = TRUE, showWarnings = FALSE)

# -- Per-panel plot directory helper ----------------------------------------
# Extracts panel letter from "panel_X_..." name and returns plots/panel_X/{fmt}/
panel_plot_dir <- function(name, fmt = "png") {
  panel <- sub("^(panel_[A-K])_.*", "\\1", name)
  pdir <- file.path(fig6_dir, "plots", panel, fmt)
  dir.create(pdir, recursive = TRUE, showWarnings = FALSE)
  pdir
}

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

# -- Source helper functions ------------------------------------------------
source(file.path(project_root, "R", "utils.R"))
source(file.path(project_root, "R", "data_processing.R"))
source(file.path(project_root, "R", "path_analysis.R"))
source(file.path(project_root, "R", "visualization.R"))
source(file.path(project_root, "R", "neuroglancer.R"))

# -- Neuprint login --------------------------------------------------------
neuprint_login(server = "https://neuprint-cns.janelia.org")
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

# Modality groupings (for annotations)
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

# -- Load path feather files -----------------------------------------------

load_modality_paths <- function(target_name, n_paths = 50) {
  modalities <- c("DA1", "VA1v", "VA1d", "aud", "vis", "ppk23", "ppk25")
  modality_labels_map <- c(
    "DA1" = "DA1", "VA1v" = "VA1v", "VA1d" = "VA1d",
    "aud" = "auditory", "vis" = "visual",
    "ppk23" = "ppk23", "ppk25" = "ppk25"
  )

  dfs <- list()
  for (mod in modalities) {
    fname <- file.path(paths_dir,
      sprintf("strongest.%d.paths.%s.2.%s.feather", n_paths, mod, target_name))
    if (file.exists(fname)) {
      df <- read_feather(fname)
      df <- drop_list_cols(df)
      df$modality   <- modality_labels_map[[mod]]
      df$target_set <- target_name
      dfs[[mod]]    <- df
    }
  }
  bind_rows(dfs)
}

load_eval_paths <- function(target_name) {
  files_map <- list(
    DA1   = sprintf("strongest.1000.paths.DA1.2.%s.feather", target_name),
    VA1v  = sprintf("strongest.1000.paths.VA1v.2.%s.feather", target_name),
    VA1d  = sprintf("strongest.1000.paths.VA1d.2.%s.feather", target_name),
    aud   = sprintf("strongest.1000.paths.auditory.2.%s.feather", target_name),
    vis   = sprintf("strongest.1000.paths.visual.2.%s.feather", target_name),
    ppk23 = sprintf("strongest.1000.paths.ppk23.2.%s.included.feather", target_name),
    ppk25 = sprintf("strongest.1000.paths.ppk25.2.%s.included.feather", target_name)
  )
  modality_labels_map <- c(
    "DA1" = "DA1", "VA1v" = "VA1v", "VA1d" = "VA1d",
    "aud" = "auditory", "vis" = "visual",
    "ppk23" = "ppk23", "ppk25" = "ppk25"
  )

  dfs <- list()
  for (mod in names(files_map)) {
    fpath <- file.path(paths_dir, files_map[[mod]])
    if (file.exists(fpath)) {
      df <- read_feather(fpath)
      df <- drop_list_cols(df)
      df$modality   <- modality_labels_map[[mod]]
      df$target_set <- target_name
      dfs[[mod]]    <- df
    }
  }
  bind_rows(dfs)
}

# Load all path sets
paths.aspf <- load_modality_paths("aspf", 50)
paths.aspg <- load_modality_paths("aspg", 50)
paths.vab3 <- load_eval_paths("vAB3")
paths.ppn1 <- load_eval_paths("PPN1")

# Combined path dataframes
paths.aspf_aspg <- bind_rows(paths.aspf, paths.aspg)
paths.all       <- bind_rows(paths.aspf, paths.aspg, paths.vab3, paths.ppn1)

# -- Strength matrix computation -------------------------------------------

compute_strength_matrix <- function(paths_df, normalize = FALSE) {
  mat <- paths_df %>%
    group_by(end, modality) %>%
    summarise(total_strength = sum(strength, na.rm = TRUE), .groups = "drop") %>%
    pivot_wider(names_from = modality, values_from = total_strength, values_fill = 0) %>%
    column_to_rownames("end")

  # Ensure all modalities present
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

# Pre-compute key strength matrices
strength.aspf      <- compute_strength_matrix(paths.aspf)
strength.aspg      <- compute_strength_matrix(paths.aspg)
strength.aspf_aspg <- compute_strength_matrix(paths.aspf_aspg)

strength.aspf_aspg.exc <- compute_valence_strength(paths.aspf_aspg, "excitatory")
strength.aspf_aspg.inh <- compute_valence_strength(paths.aspf_aspg, "inhibitory")

strength.all     <- compute_strength_matrix(paths.all)
strength.all.exc <- compute_valence_strength(paths.all, "excitatory")
strength.all.inh <- compute_valence_strength(paths.all, "inhibitory")

# -- Shannon entropy -------------------------------------------------------
shannon_entropy <- function(x) {
  x <- x[x > 0]
  if (length(x) == 0) return(0)
  p <- x / sum(x)
  -sum(p * log2(p))
}

# -- Heatmap helper: fixed-width annotation bands --------------------------
# Draws a pheatmap then resizes row-annotation bands so they share a fixed
# total width.  With 4 bands each gets 1/4; with 2 each gets 1/2.
draw_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     total_annot_cm = 1.5, ...) {
  library(grid)
  library(gtable)
  n_bands <- ncol(row_annot)
  band_w  <- unit(total_annot_cm / n_bands, "cm")

  hm <- pheatmap(mat,
    annotation_row    = row_annot,
    annotation_col    = col_annot,
    annotation_colors = ann_colors,
    silent            = TRUE,
    ...
  )

  gt <- hm$gtable
  ann_idx <- grep("row_annotation", gt$layout$name)
  for (idx in ann_idx) {
    col_pos <- gt$layout$l[idx]
    gt$widths[col_pos] <- band_w
  }
  grid.newpage()
  grid.draw(gt)
  invisible(hm)
}

# -- Save heatmap with fixed annotations to file ---------------------------
save_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     filename, width = 8, height = 10,
                                     total_annot_cm = 1.5, ...) {
  library(grid)
  library(gtable)
  n_bands <- ncol(row_annot)
  band_w  <- unit(total_annot_cm / n_bands, "cm")

  is_pdf <- grepl("\\.pdf$", filename, ignore.case = TRUE)
  if (is_pdf) pdf(filename, width = width, height = height)
  else        png(filename, width = width, height = height, units = "in", res = 300)

  hm <- pheatmap(mat,
    annotation_row    = row_annot,
    annotation_col    = col_annot,
    annotation_colors = ann_colors,
    silent            = TRUE,
    ...
  )
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
# Produces both the standard orientation (neurons=rows, modalities=cols)
# and a transposed version (modalities=rows, neurons=cols).
# Saves 4 files: name.png, name.pdf, name_horizontal.png, name_horizontal.pdf
save_heatmap_both_orientations <- function(mat, row_annot, col_annot, ann_colors,
                                           name, width = 8, height = 10,
                                           total_annot_cm = 1.5, ...) {
  pdir_png <- panel_plot_dir(name, "png")
  pdir_pdf <- panel_plot_dir(name, "pdf")

  # --- Vertical (standard) ---
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

  # --- Horizontal (transposed): neurons=cols, modalities=rows ---
  mat_t <- t(mat)

  # Swap cluster_rows/cluster_cols in extra args
  dots <- list(...)
  cr <- dots$cluster_rows
  cc <- dots$cluster_cols
  if (!is.null(cr)) dots$cluster_cols <- cr
  if (!is.null(cc)) dots$cluster_rows <- cc

  # Horizontal dimensions: swap width/height
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
save_fig6_plot <- function(plot_obj, name, width = 10, height = 8) {
  pdir_png <- panel_plot_dir(name, "png")
  pdir_pdf <- panel_plot_dir(name, "pdf")
  ggsave(file.path(pdir_png, paste0(name, ".png")),
         plot = plot_obj, width = width, height = height, dpi = 300)
  ggsave(file.path(pdir_pdf, paste0(name, ".pdf")),
         plot = plot_obj, width = width, height = height)
}

# -- Summary ---------------------------------------------------------------
message("Figure 6 setup complete.")
message(sprintf("  aSP-f paths: %d rows, %d unique targets",
                nrow(paths.aspf), length(unique(paths.aspf$end))))
message(sprintf("  aSP-g paths: %d rows, %d unique targets",
                nrow(paths.aspg), length(unique(paths.aspg$end))))
message(sprintf("  vAB3 paths:  %d rows, %d unique targets",
                nrow(paths.vab3), length(unique(paths.vab3$end))))
message(sprintf("  PPN1 paths:  %d rows, %d unique targets",
                nrow(paths.ppn1), length(unique(paths.ppn1$end))))
