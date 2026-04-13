# =============================================================================
# Male-specific mAL subset: wraps setup.R, then filters to mAL_m* types only
# =============================================================================

source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")

message("\n=== Filtering to male-specific mAL subtypes only ===")

# Keep only male-specific subtypes (pattern-based: any mAL_m* type)
mal_subtypes <- mal_subtypes[grepl("^mAL_m", mal_subtypes)]
message(sprintf("  mAL subtypes after filter: %d", length(mal_subtypes)))

# Rebuild matrices for filtered subtypes
mal_strength     <- ensure_all_mal_types(mal_strength, mal_subtypes)
mal_strength_exc <- ensure_all_mal_types(mal_strength_exc, mal_subtypes)
mal_strength_inh <- ensure_all_mal_types(mal_strength_inh, mal_subtypes)
mal_activation_matrix <- mal_strength_exc - mal_strength_inh

# Filter annotation
mal_annot <- mal_annot[mal_subtypes, , drop = FALSE]
mal_nt <- mal_nt[mal_subtypes]
mal_dimorphism <- mal_dimorphism[mal_subtypes]

# Filter signal flow matrices
if (exists("sf_activation_matrix")) {
  common_sf <- intersect(rownames(sf_activation_matrix), mal_subtypes)
  sf_activation_matrix <- sf_activation_matrix[common_sf, , drop = FALSE]
}
if (exists("mal_sf_net_input_matrix")) {
  common_ni <- intersect(rownames(mal_sf_net_input_matrix), mal_subtypes)
  mal_sf_net_input_matrix <- mal_sf_net_input_matrix[common_ni, , drop = FALSE]
}

# Filter signal flow screen results
mal_screen <- mal_screen %>% filter(target_type %in% mal_subtypes)
mal_all_combos <- mal_all_combos %>% filter(target_type %in% mal_subtypes)
mal_ppk_interaction <- mal_ppk_interaction %>% filter(target_type %in% mal_subtypes)

# Override plot directory to write to plots_mspecific
panel_plot_dir <- function(name, fmt = "png", subdir = NULL) {
  panel <- sub("^(panel_[A-Z])_.*", "\\1", name)
  if (!is.null(subdir)) {
    pdir <- file.path(fig5_dir, "plots_mspecific", panel, subdir, fmt)
  } else {
    pdir <- file.path(fig5_dir, "plots_mspecific", panel, fmt)
  }
  dir.create(pdir, recursive = TRUE, showWarnings = FALSE)
  pdir
}

# Override save_panel_narrative to write to plots_mspecific
save_panel_narrative <- function(panel_name, narrative_text) {
  narr_dir <- file.path(fig5_dir, "plots_mspecific", panel_name)
  dir.create(narr_dir, recursive = TRUE, showWarnings = FALSE)
  fpath <- file.path(narr_dir, paste0(panel_name, "_narrative.txt"))
  writeLines(narrative_text, fpath)
  message(sprintf("  Narrative saved: %s", fpath))
  invisible(fpath)
}

# Override theme_pub with larger base size for readability
theme_pub <- function(base_size = 14) {
  theme_minimal(base_size = base_size) %+replace%
    theme(
      plot.title       = element_blank(),
      plot.subtitle    = element_blank(),
      plot.margin      = margin(4, 4, 4, 4),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(linewidth = 0.3, color = "grey90"),
      axis.title       = element_text(size = rel(1.1)),
      axis.text        = element_text(size = rel(0.9)),
      axis.text.x      = element_text(size = rel(0.9), angle = 30, hjust = 1),
      legend.title     = element_text(size = rel(1)),
      legend.text      = element_text(size = rel(0.9)),
      legend.key.size  = unit(0.5, "cm"),
      legend.margin    = margin(0, 0, 0, 0),
      legend.spacing   = unit(0.15, "cm"),
      strip.text       = element_text(size = rel(1), face = "bold")
    )
}

# Override save_fig5_plot to use larger theme and bump point sizes
save_fig5_plot <- function(plot_obj, name, width = 10, height = 8, subdir = NULL) {
  pdir_png <- panel_plot_dir(name, "png", subdir = subdir)
  pdir_pdf <- panel_plot_dir(name, "pdf", subdir = subdir)

  plot_obj <- plot_obj + theme_pub(base_size = 14)

  # Increase geom sizes globally
  for (i in seq_along(plot_obj$layers)) {
    layer <- plot_obj$layers[[i]]
    geom_class <- class(layer$geom)[1]
    if (geom_class == "GeomPoint") {
      if (!is.null(layer$aes_params$size)) {
        layer$aes_params$size <- layer$aes_params$size * 1.5
      } else if (is.null(layer$mapping$size)) {
        # Default point size — bump it
        layer$aes_params$size <- 4.5
      }
    }
  }

  ggsave(file.path(pdir_png, paste0(name, ".png")),
         plot = plot_obj, width = width, height = height, dpi = 300)
  ggsave(file.path(pdir_pdf, paste0(name, ".pdf")),
         plot = plot_obj, width = width, height = height)
}

# Override heatmap font sizes
save_heatmap_fixed_annot_orig <- save_heatmap_fixed_annot
save_heatmap_fixed_annot <- function(mat, row_annot, col_annot, ann_colors,
                                     filename, width = 8, height = 10,
                                     total_annot_cm = 1.5, ...) {
  dots <- list(...)
  # Bump fontsize defaults
  if (!is.null(dots$fontsize_row)) dots$fontsize_row <- dots$fontsize_row * 1.6
  if (!is.null(dots$fontsize_col)) dots$fontsize_col <- dots$fontsize_col * 1.6
  if (!is.null(dots$fontsize))     dots$fontsize     <- dots$fontsize * 1.4
  do.call(save_heatmap_fixed_annot_orig, c(list(
    mat = mat, row_annot = row_annot, col_annot = col_annot,
    ann_colors = ann_colors, filename = filename,
    width = width, height = height, total_annot_cm = total_annot_cm
  ), dots))
}

message(sprintf("  Output directory: %s", file.path(fig5_dir, "plots_mspecific")))
message("  Theme: base_size=14, point size x1.5, heatmap fonts x1.6")
message("=== Male-specific setup complete ===\n")
