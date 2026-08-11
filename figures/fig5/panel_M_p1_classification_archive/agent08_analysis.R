#!/usr/bin/env Rscript
# Agent 08: P1 scenario discriminability analysis
# Scenarios: Female (ppk23+ppk25), cVA+male (DA1+ppk23), cVA+female (DA1+ppk23+ppk25)

suppressMessages(source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R"))
suppressMessages({
  library(dplyr)
  library(tidyr)
})

out_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

set.seed(42)

# ---- Scenario definitions --------------------------------------------------
scenario_labels <- c(
  "female"      = "ppk23+ppk25",
  "cVA_male"    = "DA1+ppk23",
  "cVA_female"  = "DA1+ppk23+ppk25"
)

stopifnot(all(scenario_labels %in% p1_all_combos$combination))

# ---- Extract per-P1 drive under each scenario ------------------------------
scenario_df <- p1_all_combos %>%
  filter(combination %in% scenario_labels) %>%
  select(target_type, combination, net_input)

# Wide: rows = P1, cols = scenarios
scenario_wide <- scenario_df %>%
  pivot_wider(names_from = combination, values_from = net_input) %>%
  as.data.frame()

# Ensure all three columns present
for (sc in scenario_labels) {
  if (!sc %in% colnames(scenario_wide)) scenario_wide[[sc]] <- NA_real_
}
# Reorder
scenario_wide <- scenario_wide[, c("target_type", scenario_labels)]

# Drop P1 with any missing scenario
complete_idx <- complete.cases(scenario_wide[, scenario_labels])
scenario_wide <- scenario_wide[complete_idx, , drop = FALSE]

cat("P1 types with all 3 scenarios:", nrow(scenario_wide), "\n")

# ---- Metrics ---------------------------------------------------------------
drive_mat <- as.matrix(scenario_wide[, scenario_labels])
rownames(drive_mat) <- scenario_wide$target_type

compute_metrics <- function(drive_mat, scenario_labels) {
  abs_mat <- abs(drive_mat)
  total_drive <- rowSums(abs_mat)
  spread      <- apply(drive_mat, 1, function(x) max(x) - min(x))
  mean_abs    <- rowMeans(abs_mat)
  sd_drive    <- apply(drive_mat, 1, sd)
  cv          <- ifelse(mean_abs > 0, sd_drive / mean_abs, NA_real_)
  argmax_idx  <- apply(drive_mat, 1, which.max)
  argmax_lbl  <- names(scenario_labels)[argmax_idx]
  argmax_comb <- scenario_labels[argmax_idx]
  # chi-squared-like distance from uniform: sum((x - mean(x))^2 / |mean(x)|)
  chi_uniform <- apply(drive_mat, 1, function(x) {
    mu <- mean(x)
    if (abs(mu) < .Machine$double.eps) return(sum((x - mu)^2))
    sum((x - mu)^2 / abs(mu))
  })
  data.frame(
    target_type    = rownames(drive_mat),
    drive_female   = drive_mat[, scenario_labels["female"]],
    drive_cVA_male = drive_mat[, scenario_labels["cVA_male"]],
    drive_cVA_fem  = drive_mat[, scenario_labels["cVA_female"]],
    total_drive    = total_drive,
    spread         = spread,
    mean_abs_drive = mean_abs,
    sd_drive       = sd_drive,
    cv             = cv,
    argmax_scenario = argmax_lbl,
    argmax_combination = unname(argmax_comb),
    chi_sq_uniform = chi_uniform,
    row.names = NULL,
    stringsAsFactors = FALSE
  )
}

metrics <- compute_metrics(drive_mat, scenario_labels)

# ---- Permutation null: shuffle the channel-combo assignments per P1 --------
# For each P1 we sample 3 combinations uniformly (without replacement) from
# the full set of combinations present in p1_all_combos for that P1, recompute
# the spread, and compare to observed.

n_perm <- 1000

# Pool of net_input values per P1 across all combinations (the "channel-combo
# assignments" to shuffle). We shuffle which 3 combinations are treated as the
# 3 scenarios for each P1.
p1_pool <- p1_all_combos %>%
  filter(target_type %in% scenario_wide$target_type) %>%
  select(target_type, combination, net_input)

pool_by_p1 <- split(p1_pool$net_input, p1_pool$target_type)

p_values <- numeric(nrow(metrics))
null_spread_mean <- numeric(nrow(metrics))
null_spread_sd   <- numeric(nrow(metrics))
for (i in seq_len(nrow(metrics))) {
  p1 <- metrics$target_type[i]
  pool <- pool_by_p1[[p1]]
  if (length(pool) < 3) {
    p_values[i] <- NA_real_
    null_spread_mean[i] <- NA_real_
    null_spread_sd[i]   <- NA_real_
    next
  }
  null_spreads <- replicate(n_perm, {
    v <- sample(pool, 3, replace = FALSE)
    max(v) - min(v)
  })
  obs <- metrics$spread[i]
  # One-sided: observed > null
  p_values[i] <- (sum(null_spreads >= obs) + 1) / (n_perm + 1)
  null_spread_mean[i] <- mean(null_spreads)
  null_spread_sd[i]   <- sd(null_spreads)
}

metrics$perm_p_value       <- p_values
metrics$null_spread_mean   <- null_spread_mean
metrics$null_spread_sd     <- null_spread_sd

# FDR across all P1 for the full table (informative but reported separately)
metrics$fdr_bh <- p.adjust(metrics$perm_p_value, method = "BH")

# Sort by spread descending
metrics <- metrics[order(-metrics$spread), ]

full_path <- file.path(out_dir, "p1_discriminability_stats.csv")
write.csv(metrics, full_path, row.names = FALSE)
cat("Wrote:", full_path, "\n")

# ---- Top 10 most-discriminating -------------------------------------------
top10 <- head(metrics, 10)
# Re-compute FDR within the top-10 for a "local" view, plus keep global FDR
top10$fdr_bh_top10 <- p.adjust(top10$perm_p_value, method = "BH")

top_path <- file.path(out_dir, "p1_top_discriminators.csv")
write.csv(top10, top_path, row.names = FALSE)
cat("Wrote:", top_path, "\n")

# ---- Summary stats --------------------------------------------------------
n_fdr05   <- sum(metrics$fdr_bh < 0.05, na.rm = TRUE)
n_fdr01   <- sum(metrics$fdr_bh < 0.01, na.rm = TRUE)
n_raw05   <- sum(metrics$perm_p_value < 0.05, na.rm = TRUE)
spread_rng <- range(metrics$spread, na.rm = TRUE)
spread_med <- median(metrics$spread, na.rm = TRUE)
spread_iqr <- IQR(metrics$spread, na.rm = TRUE)

argmax_tab <- table(metrics$argmax_scenario)

cat(sprintf("\nP1 types analyzed: %d\n", nrow(metrics)))
cat(sprintf("Permutations: %d\n", n_perm))
cat(sprintf("Pass FDR<0.05: %d | FDR<0.01: %d | raw p<0.05: %d\n",
            n_fdr05, n_fdr01, n_raw05))
cat(sprintf("Spread range: [%.4f, %.4f] | median %.4f | IQR %.4f\n",
            spread_rng[1], spread_rng[2], spread_med, spread_iqr))
cat("Argmax scenario distribution:\n"); print(argmax_tab)

# ---- Narrative (~250 words) -----------------------------------------------
# Compose a descriptive narrative.
top3 <- head(metrics[, c("target_type", "spread", "perm_p_value", "fdr_bh",
                         "argmax_scenario")], 3)
top3_str <- paste(sprintf("%s (spread=%.3f, p=%.4f, best=%s)",
                          top3$target_type, top3$spread, top3$perm_p_value,
                          top3$argmax_scenario), collapse = "; ")

narrative <- sprintf(
"Agent 08 -- P1 scenario-discriminability findings
Date: %s

Design. For every P1 subtype with signal-flow net_input values for all three
behavioural scenarios (Female = ppk23+ppk25; cVA+male = DA1+ppk23; cVA+female
= DA1+ppk23+ppk25), we extracted the drive from p1_all_combos and computed
five discriminability metrics: total |drive| summed across the three
scenarios, spread (max-min), coefficient of variation (sd / mean(|drive|)),
the argmax scenario, and a chi-squared-like deviation from a flat profile
(sum((x-mu)^2/|mu|)). A one-sided permutation null was built per P1 by
resampling three combinations without replacement from that P1's full
combinatorial screen (127 combinations) and recomputing the spread; the
p-value is the fraction of null spreads >= observed (+1/+1 correction), with
1000 permutations. P-values were BH-adjusted across all P1s.

Sample. %d P1 subtypes had complete data for the three scenarios.

Significance. %d P1 types pass FDR<0.05 for scenario discriminability and
%d pass FDR<0.01; %d have raw p<0.05. The spread metric ranges from
%.3f to %.3f (median %.3f, IQR %.3f), so the dynamic range spans roughly
%.1fx between the flattest and most-selective subtype.

Top discriminators. %s.

Argmax distribution: %s.

Robustness. Results rest on the single-population signal-flow model and the
per-P1 null pool of 127 combinations. The permutation null is conservative
because the three target scenarios contain three of the strongest channels,
so any P1 with a genuine ppk/cVA preference will show up as significant;
conversely, P1 types whose drive is dominated by visual/auditory channels
look undiscriminating here even if they are selective elsewhere. FDR was
computed globally; permutation p-values are floor-bounded at 1/(B+1) =
9.99e-4, so the smallest attainable FDR depends on the number of P1s tested.
",
  Sys.Date(),
  nrow(metrics),
  n_fdr05, n_fdr01, n_raw05,
  spread_rng[1], spread_rng[2], spread_med, spread_iqr,
  if (spread_rng[1] > 0) spread_rng[2] / spread_rng[1] else spread_rng[2] / .Machine$double.eps,
  top3_str,
  paste(sprintf("%s=%d", names(argmax_tab), as.integer(argmax_tab)),
        collapse = ", ")
)

# Trim/check word count
wc <- length(strsplit(narrative, "\\s+")[[1]])
cat(sprintf("\nNarrative word count: %d\n", wc))

findings_path <- file.path(out_dir, "agent08_findings.txt")
writeLines(narrative, findings_path)
cat("Wrote:", findings_path, "\n")

cat("\n=== DONE ===\n")
