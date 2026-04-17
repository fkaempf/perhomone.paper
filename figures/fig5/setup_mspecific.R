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

# Override save_panel_narrative to write to plots_mspecific.
# Mirrors panel_plot_dir: collapse "panel_X_*" names onto the parent "panel_X"
# directory so narratives land alongside the pdf/png outputs.
save_panel_narrative <- function(panel_name, narrative_text) {
  panel <- sub("^(panel_[A-Z])_.*", "\\1", panel_name)
  narr_dir <- file.path(fig5_dir, "plots_mspecific", panel)
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

# =============================================================================
# GABA sign-inverter set (Panel M)
# =============================================================================
# Operationally: any type matching AN05B|IN05 with consensus_nt == "gaba".
# Includes AN05B035 (the canonical example) and its distributed siblings
# (AN05B023b, AN05B025, IN05B002, IN05B011b, ...). Panel M figures treat
# this whole pool as the "GABA sign-inverter" that carries inhibition from
# ppk channels to mAL_m targets. mAL-lateral GABA is a separate circuit
# (covered in Panel G) and is NOT included here.
.gaba_type_pool <- mba %>%
  dplyr::select(type, consensus_nt) %>%
  dplyr::distinct() %>%
  dplyr::group_by(type) %>% dplyr::slice(1) %>% dplyr::ungroup() %>%
  dplyr::filter(!is.na(consensus_nt), consensus_nt == "gaba",
                grepl("^(AN05B|IN05)", type)) %>%
  dplyr::pull(type)

# Restrict to GABA cells that actually appear as interior relays on
# inhibitory ppk23/ppk25 -> mAL_m paths. This is the working pool.
.inh_interior_nodes <- mal_paths %>%
  dplyr::filter(valence == "inhibitory",
                modality %in% c("ppk23","ppk25"),
                end %in% mal_subtypes) %>%
  dplyr::pull(path) %>%
  lapply(function(p) {
    t <- strsplit(p, " -> ", fixed = TRUE)[[1]]
    if (length(t) <= 2) character(0) else t[-c(1, length(t))]
  }) %>%
  unlist() %>% unique()

gaba_sign_inverter_types <- intersect(.gaba_type_pool, .inh_interior_nodes)
rm(.gaba_type_pool, .inh_interior_nodes)

message(sprintf("  GABA sign-inverter types (Panel M pool): %d",
                length(gaba_sign_inverter_types)))
message(sprintf("    %s", paste(gaba_sign_inverter_types, collapse = ", ")))

# Helper: does a "A -> B -> ... -> Z" path string traverse any GABA SI?
# (Checks interior nodes only — first/last are source/target.)
path_via_gaba_si <- function(path_str) {
  toks <- strsplit(path_str, " -> ", fixed = TRUE)[[1]]
  if (length(toks) <= 2) return(FALSE)
  ints <- toks[-c(1, length(toks))]
  any(ints %in% gaba_sign_inverter_types)
}

# =============================================================================
# Panel M shared visual constants (harmonization pass 2026-04-15)
# =============================================================================
# Canonical palette used across every Panel M figure. Any figure that encodes
# these roles MUST reuse the same hex codes so the panel reads as a coherent
# story.
panel_M_palette <- c(
  ppk23        = "#C0272D",  # red — ppk23 (male contact pheromone) excitatory
  ppk25        = "#F4A261",  # orange — ppk25 (female contact pheromone) excitatory
  gaba_si      = "#1F4E79",  # dark blue — GABA sign-inverter pool (inhibitory)
  excitatory   = "#C0272D",  # alias for ppk23 excitatory routes
  inhibitory   = "#1F4E79",  # alias for inhibitory routes via SI pool
  mal_lateral  = "grey55",   # grey — mAL lateral GABA (covered in Panel G)
  other        = "grey85"    # faint — unclassified / residual
)

# Load the shared mAL_m subtype sort order exported by
# panel_M_inhibitory_sources.Rmd. Returns a character vector (top -> bottom)
# or NULL if the RDS is missing (first render has to produce it).
load_mal_sort_order <- function() {
  f <- file.path(fig5_dir, "plots_mspecific", "panel_M",
                 "panel_M_mal_sort_order.rds")
  if (!file.exists(f)) return(NULL)
  readRDS(f)
}

# Human-readable channel labeller used in facet_wrap/facet_grid.
panel_M_channel_labeller <- ggplot2::as_labeller(c(
  "ppk23" = "ppk23 channel (male contact pheromone)",
  "ppk25" = "ppk25 channel (female contact pheromone)"
))

# Collapse the SI pool list into a compact, scannable form:
#   AN05B023a, AN05B023b, AN05B023c, AN05B023d -> AN05B023a-d
#   IN05B011a, IN05B011b                       -> IN05B011a/b
.collapse_si_pool <- function(types) {
  types <- sort(unique(types))
  # Strip single lowercase suffix letter (a-z) to find the stem.
  stems <- sub("([a-z])$", "", types)
  suff  <- ifelse(stems == types, "", sub(".*([a-z])$", "\\1", types))
  out <- c(); i <- 1
  while (i <= length(types)) {
    stem <- stems[i]; letters_here <- suff[i]
    j <- i
    while (j + 1 <= length(types) && stems[j + 1] == stem && suff[j + 1] != "") {
      letters_here <- c(letters_here, suff[j + 1]); j <- j + 1
    }
    if (length(letters_here) >= 3 && all(letters_here != "")) {
      out <- c(out, paste0(stem, letters_here[1], "-", letters_here[length(letters_here)]))
    } else if (length(letters_here) == 2 && all(letters_here != "")) {
      out <- c(out, paste0(stem, letters_here[1], "/", letters_here[2]))
    } else {
      out <- c(out, types[i:j])
    }
    i <- j + 1
  }
  paste(out, collapse = ", ")
}

# One-line pool member list (for captions). Sectioned POOL tag.
panel_M_pool_caption <- paste0(
  "POOL (n=", length(gaba_sign_inverter_types), "): ",
  .collapse_si_pool(gaba_sign_inverter_types),
  "."
)

# Anatomical abbreviation legend (used by morphology caption). Single sectioned line.
panel_M_anatomy_legend <- paste0(
  "ANATOMY: T1 = thoracic leg neuromere 1 (VNC); ",
  "SEZ = subesophageal zone (brain, = GNG + PRW)."
)

message(sprintf("  Output directory: %s", file.path(fig5_dir, "plots_mspecific")))
message("  Theme: base_size=14, point size x1.5, heatmap fonts x1.6")
message("=== Male-specific setup complete ===\n")
