# Render all Figure 6 (Bella's targets) panels
#
# PREREQUISITE: Run compute_paths.R first!
#   source("/Users/fkampf/Documents/pheromone.paper/figures/fig6_bella_targets/compute_paths.R")
#
# Then run this:
#   source("/Users/fkampf/Documents/pheromone.paper/figures/fig6_bella_targets/render_all.R")

fig6_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig6_bella_targets"

panels <- c(paste0("panel_", LETTERS[1:9], ".Rmd"), "panel_J.Rmd", "panel_K.Rmd")

for (p in panels) {
  message("\n========== Rendering ", p, " ==========\n")
  tryCatch(
    rmarkdown::render(
      file.path(fig6_dir, p),
      output_dir = file.path(fig6_dir, "html"),
      quiet = FALSE
    ),
    error = function(e) message("ERROR in ", p, ": ", e$message)
  )
  # Close any leaked graphics devices to prevent cascading failures
  try(graphics.off(), silent = TRUE)
}

message("\nDone! Plots in fig6_bella_targets/plots/panel_X/{png,pdf}/")
message("HTML reports in fig6_bella_targets/html/")


