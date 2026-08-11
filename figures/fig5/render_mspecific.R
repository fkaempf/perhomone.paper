# =============================================================================
# Render all panels with male-specific mAL subset
# =============================================================================

panels <- c(
  "panel_A.Rmd", "panel_B.Rmd", "panel_C.Rmd", "panel_D.Rmd",
  "panel_E.Rmd", "panel_F.Rmd", "panel_G.Rmd", "panel_I.Rmd",
  "panel_J.Rmd", "panel_K.Rmd", "panel_L.Rmd"
)

fig5_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5"
rmd_dir  <- file.path(fig5_dir, "rmd")
tmp_dir  <- file.path(fig5_dir, ".tmp_mspecific")
dir.create(tmp_dir, showWarnings = FALSE)

# Write all temp Rmds first
for (panel in panels) {
  src <- file.path(rmd_dir, panel)
  if (!file.exists(src)) next

  lines <- readLines(src)
  lines <- gsub(
    'source\\(".*/setup\\.R"\\)',
    sprintf('source("%s/setup_mspecific.R")', fig5_dir),
    lines
  )
  writeLines(lines, file.path(tmp_dir, panel))
}

# Render each in a fresh R process to avoid working directory issues
for (panel in panels) {
  tmp_rmd <- file.path(tmp_dir, panel)
  if (!file.exists(tmp_rmd)) {
    message(sprintf("SKIP: %s not found", panel))
    next
  }

  message(sprintf("\n========== Rendering %s (male-specific) ==========", panel))
  # Use system() to run in a fresh R process
  cmd <- sprintf(
    'Rscript -e \'rmarkdown::render("%s", output_dir = "%s", quiet = TRUE)\'',
    tmp_rmd, tmp_dir
  )
  ret <- system(cmd, intern = FALSE, ignore.stdout = TRUE, ignore.stderr = TRUE)
  if (ret == 0) {
    message(sprintf("  OK: %s", panel))
  } else {
    message(sprintf("  FAILED: %s (exit code %d)", panel, ret))
  }
}

# Clean up temp dir
unlink(tmp_dir, recursive = TRUE)
message("\nDone. Plots in: fig5/plots_mspecific/")
