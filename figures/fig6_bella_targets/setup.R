# =============================================================================
# Figure 6 (Bella's targets): Shared Setup
# =============================================================================
# Source this file at the top of each panel script:
#   source("/Users/fkampf/Documents/pheromone.paper/figures/fig6_bella_targets/setup.R")
#
# PREREQUISITE: Run compute_paths.R first to generate feather files!
# =============================================================================

# -- Project root ----------------------------------------------------------
project_root <- "/Users/fkampf/Documents/pheromone.paper"
fig6_dir     <- file.path(project_root, "figures", "fig6_bella_targets")
feather_dir  <- file.path(project_root, "feather")
paths_dir    <- file.path(feather_dir, "strongest.paths")
plot_dir_png <- file.path(fig6_dir, "plots", "png")
plot_dir_pdf <- file.path(fig6_dir, "plots", "pdf")

dir.create(plot_dir_png, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir_pdf, recursive = TRUE, showWarnings = FALSE)

# -- Publication mode ---------------------------------------------------------
# Set to TRUE for compact, title-free plots suitable for multi-panel figures
pub_mode <- TRUE

# -- Per-panel plot directory helper ----------------------------------------
panel_plot_dir <- function(name, fmt = "png", subdir = NULL) {
  panel <- sub("^(panel_[A-K])_.*", "\\1", name)
  if (!is.null(subdir)) {
    pdir <- file.path(fig6_dir, "plots", panel, subdir, fmt)
  } else {
    pdir <- file.path(fig6_dir, "plots", panel, fmt)
  }
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
options(malecns.dataset = "male-cns:v1.0")   # malecns helpers ignore MCNS_DATASET
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

# -- Target group definitions & colors -------------------------------------
# Load the target group metadata saved by compute_paths.R
bella_groups_df  <- readRDS(file.path(paths_dir, "bella_target_groups.rds"))
bella_targets    <- readRDS(file.path(paths_dir, "bella_targets_list.rds"))

target_set_colors <- c(
  "M_downstream"  = "#E41A1C",
  "F_downstream"  = "#377EB8",
  "IR_downstream" = "#4DAF4A"
)

target_set_labels <- c(
  "M_downstream"  = "M cells",
  "F_downstream"  = "F cells",
  "IR_downstream" = "IR cells"
)

# -- Load path feather files -----------------------------------------------

load_bella_paths <- function(n_paths = 50) {
  modalities <- c("DA1", "VA1v", "VA1d", "aud", "vis", "ppk23", "ppk25")
  modality_labels_map <- c(
    "DA1" = "DA1", "VA1v" = "VA1v", "VA1d" = "VA1d",
    "aud" = "auditory", "vis" = "visual",
    "ppk23" = "ppk23", "ppk25" = "ppk25"
  )

  dfs <- list()
  for (mod in modalities) {
    fname <- file.path(paths_dir,
      sprintf("strongest.%d.paths.%s.2.bella.feather", n_paths, mod))
    if (file.exists(fname)) {
      df <- read_feather(fname)
      df <- drop_list_cols(df)
      df$modality <- modality_labels_map[[mod]]
      dfs[[mod]]  <- df
    } else {
      warning(sprintf("Missing path file: %s", basename(fname)))
    }
  }
  bind_rows(dfs)
}

# Load all paths
paths.bella <- load_bella_paths(50)

# Add target_group annotation to each path based on its 'end' type
# A neuron can belong to multiple groups; assign primary group by first match
assign_target_group <- function(paths_df, groups_df) {
  # For neurons in multiple groups, pick the first one alphabetically
  primary_group <- groups_df %>%
    group_by(type) %>%
    summarise(target_set = first(target_group), .groups = "drop")

  paths_df %>%
    left_join(primary_group, by = c("end" = "type")) %>%
    mutate(target_set = ifelse(is.na(target_set), "other", target_set))
}

paths.bella <- assign_target_group(paths.bella, bella_groups_df)

# Split by target group
paths.M  <- paths.bella %>% filter(end %in% bella_targets$M_downstream)
paths.F  <- paths.bella %>% filter(end %in% bella_targets$F_downstream)
paths.IR <- paths.bella %>% filter(end %in% bella_targets$IR_downstream)

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
strength.bella     <- compute_strength_matrix(paths.bella)
strength.bella.exc <- compute_valence_strength(paths.bella, "excitatory")
strength.bella.inh <- compute_valence_strength(paths.bella, "inhibitory")

# Per-group strength matrices
strength.M  <- compute_strength_matrix(paths.M)
strength.F  <- compute_strength_matrix(paths.F)
strength.IR <- compute_strength_matrix(paths.IR)

# -- Shannon entropy -------------------------------------------------------
shannon_entropy <- function(x) {
  x <- x[x > 0]
  if (length(x) == 0) return(0)
  p <- x / sum(x)
  -sum(p * log2(p))
}

# -- Heatmap helper: fixed-width annotation bands --------------------------
draw_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     total_annot_cm = 1.5, ...) {
  library(grid)
  library(gtable)
  n_bands <- ncol(row_annot)
  band_w  <- unit(total_annot_cm / n_bands, "cm")

  dots <- list(...)
  if (pub_mode) {
    dots$main <- ""
    if (!is.null(dots$fontsize_row) && dots$fontsize_row > 5) dots$fontsize_row <- 5
    if (!is.null(dots$fontsize_col) && dots$fontsize_col > 8) dots$fontsize_col <- 8
  }

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
  invisible(hm)
}

save_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     filename, width = 8, height = 10,
                                     total_annot_cm = 1.5, ...) {
  library(grid)
  library(gtable)
  n_bands <- ncol(row_annot)
  band_w  <- unit(total_annot_cm / n_bands, "cm")

  # Capture extra args and apply pub_mode overrides
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
save_fig6_plot <- function(plot_obj, name, width = 10, height = 8, subdir = NULL) {
  pdir_png <- panel_plot_dir(name, "png", subdir = subdir)
  pdir_pdf <- panel_plot_dir(name, "pdf", subdir = subdir)

  # Apply publication theme if pub_mode is on
  if (pub_mode) {
    plot_obj <- plot_obj + theme_pub()
  }

  ggsave(file.path(pdir_png, paste0(name, ".png")),
         plot = plot_obj, width = width, height = height, dpi = 300)
  ggsave(file.path(pdir_pdf, paste0(name, ".pdf")),
         plot = plot_obj, width = width, height = height)
}

# -- Summary ---------------------------------------------------------------
message("Figure 6 (Bella's targets) setup complete.")
message(sprintf("  Total paths: %d rows, %d unique targets",
                nrow(paths.bella), length(unique(paths.bella$end))))
message(sprintf("  M downstream:  %d rows, %d unique targets",
                nrow(paths.M), length(unique(paths.M$end))))
message(sprintf("  F downstream:  %d rows, %d unique targets",
                nrow(paths.F), length(unique(paths.F$end))))
message(sprintf("  IR downstream: %d rows, %d unique targets",
                nrow(paths.IR), length(unique(paths.IR$end))))
message(sprintf("  Strength matrix: %d neurons x %d modalities",
                nrow(strength.bella), ncol(strength.bella)))
