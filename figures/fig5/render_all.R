# =============================================================================
# Figure 5: Render all panels
# =============================================================================
# Run this script to render all Figure 5 panels sequentially.
# Each panel is rendered to HTML in fig5/html/
# Selected variants are auto-copied to fig5/selection/
# =============================================================================

fig5_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5"
html_dir <- file.path(fig5_dir, "html")
dir.create(html_dir, recursive = TRUE, showWarnings = FALSE)

panels <- c(
  "panel_A.Rmd",
  "panel_B.Rmd",
  "panel_C.Rmd",
  "panel_D.Rmd",
  "panel_E.Rmd",
  "panel_F.Rmd",
  "panel_G.Rmd",
  "panel_H.Rmd",
  "panel_I.Rmd",
  "panel_J.Rmd",
  "panel_K.Rmd",
  "panel_L.Rmd"
)

for (panel in panels) {
  panel_path <- file.path(fig5_dir, panel)
  if (!file.exists(panel_path)) {
    message(sprintf("SKIP: %s not found", panel))
    next
  }

  message(sprintf("\n=== Rendering %s ===", panel))
  tryCatch({
    rmarkdown::render(
      input       = panel_path,
      output_dir  = html_dir,
      output_format = "html_document",
      quiet       = FALSE
    )
    message(sprintf("  OK: %s rendered successfully", panel))
  }, error = function(e) {
    message(sprintf("  FAIL: %s -- %s", panel, conditionMessage(e)))
  }, finally = {
    # Close any lingering graphics devices
    while (dev.cur() > 1) graphics.off()
  })
}

message("\n=== All panels rendered ===")
message(sprintf("HTML output: %s", html_dir))
message(sprintf("Plot output: %s/plots/", fig5_dir))

# =============================================================================
# Auto-generate selection folder with recommended variants
# =============================================================================

selection_dir <- file.path(fig5_dir, "selection")
dir.create(selection_dir, recursive = TRUE, showWarnings = FALSE)

# Map: panel letter -> recommended plot variant (relative to fig5/plots/)
selection_map <- list(
  panel_A = "panel_A/pdf/panel_A_input_profiles_raw.pdf",
  panel_B = "panel_B/pdf/panel_B_combined.pdf",
  panel_C = "panel_C/pdf/panel_C_ppk23_vs_ppk25_scatter.pdf",
  panel_D = "panel_D/pdf/panel_D_mal_to_p1.pdf",
  panel_E = "panel_E/pdf/panel_E_combined.pdf",
  panel_F = "panel_F/pdf/panel_F_combined.pdf",
  panel_G = "panel_G/pdf/panel_G_combined.pdf",
  panel_H = "panel_H/pdf/panel_H_dimorphism_boxplots.pdf",
  panel_I = "panel_I/pdf/panel_I_scenario_heatmap.pdf",
  panel_J = "panel_J/pdf/panel_J_combined.pdf",
  panel_K = "panel_K/pdf/panel_K_combined.pdf",
  panel_L = "panel_L/pdf/panel_L_mal_ppk_selectivity.pdf"
)

message("\n=== Copying selected variants to selection/ ===")
plots_dir <- file.path(fig5_dir, "plots")

for (panel_name in names(selection_map)) {
  src <- file.path(plots_dir, selection_map[[panel_name]])
  dst <- file.path(selection_dir, paste0(panel_name, ".pdf"))

  if (file.exists(src)) {
    file.copy(src, dst, overwrite = TRUE)
    message(sprintf("  OK: %s -> %s", basename(src), basename(dst)))
  } else {
    message(sprintf("  MISS: %s not found", selection_map[[panel_name]]))
  }
}

message(sprintf("\nSelection output: %s", selection_dir))
