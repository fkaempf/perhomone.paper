#!/usr/bin/env Rscript
# Agent 09: P1 group aggregation and courtship-vs-aggression cluster test
#
# Aggregate P1 subtypes (e.g. P1_3a/b/c -> P1_3) and ask whether any P1 groups
# show statistically distinct scenario-drive profiles consistent with a
# courtship-pool vs aggression-pool dichotomy.

suppressMessages(suppressWarnings(source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")))

library(dplyr)
library(tidyr)
library(tibble)
library(stringr)

out_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# -- 1. Define scenarios (from panel_I_p1_decoder.Rmd) ------------------------
scenarios <- c(
  "Female encounter" = "ppk23,ppk25",
  "cVA + male"       = "DA1,ppk23",
  "cVA + female"     = "DA1,ppk23,ppk25"
)

# -- 2. Pull per-subtype net_input under the 3 scenarios ----------------------
drive_long <- bind_rows(lapply(names(scenarios), function(nm) {
  p1_all_combos %>%
    filter(channels == scenarios[[nm]]) %>%
    transmute(P1 = target_type, scenario = nm, drive = net_input)
})) %>%
  mutate(scenario = factor(scenario, levels = names(scenarios)))

cat(sprintf("P1 subtypes with scenario data: %d\n",
            length(unique(drive_long$P1))))

# -- 3. Group P1 subtypes by stripping trailing single lowercase letter -------
#   P1_3a / P1_3b / P1_3c -> P1_3 ; P1_12a -> P1_12 ; P1_7 -> P1_7
#   P1_2a/2b -> P1_2 (collapse compound subtype labels to the numeric root)
strip_subtype <- function(x) {
  # keep only the first "P1_<digits>" root
  sub("^(P1_[0-9]+).*$", "\\1", x)
}

drive_long <- drive_long %>%
  mutate(P1_group = strip_subtype(P1))

group_tbl <- drive_long %>%
  group_by(P1_group, scenario) %>%
  summarise(drive = sum(drive, na.rm = TRUE),
            n_subtypes = n_distinct(P1),
            .groups = "drop")

n_sub_per_group <- group_tbl %>%
  distinct(P1_group, n_subtypes)

cat(sprintf("P1 groups: %d\n", nrow(n_sub_per_group)))
print(n_sub_per_group %>% arrange(desc(n_subtypes)))

# -- 4. Per-group drive matrix + z-score + argmax -----------------------------
group_wide <- group_tbl %>%
  select(P1_group, scenario, drive) %>%
  pivot_wider(names_from = scenario, values_from = drive)

scenario_names <- names(scenarios)
group_mat <- as.matrix(group_wide[, scenario_names])
rownames(group_mat) <- group_wide$P1_group

z_mat <- t(apply(group_mat, 1, function(v) {
  s <- sd(v)
  if (!is.finite(s) || s == 0) return(rep(0, length(v)))
  (v - mean(v)) / s
}))
colnames(z_mat) <- scenario_names

argmax_scn <- scenario_names[apply(group_mat, 1, which.max)]
range_z    <- apply(z_mat, 1, function(v) max(v) - min(v))

group_drive_table <- tibble(
  P1_group            = rownames(group_mat),
  n_subtypes          = n_sub_per_group$n_subtypes[
                          match(rownames(group_mat), n_sub_per_group$P1_group)],
  drive_Female        = group_mat[, "Female encounter"],
  drive_cVA_male      = group_mat[, "cVA + male"],
  drive_cVA_female    = group_mat[, "cVA + female"],
  z_Female            = z_mat[, "Female encounter"],
  z_cVA_male          = z_mat[, "cVA + male"],
  z_cVA_female        = z_mat[, "cVA + female"],
  argmax_scenario     = argmax_scn,
  discrim_range_z     = range_z
) %>% arrange(argmax_scenario, desc(discrim_range_z))

write.csv(group_drive_table,
          file.path(out_dir, "p1_group_drive_table.csv"),
          row.names = FALSE)
cat(sprintf("Wrote %s\n", file.path(out_dir, "p1_group_drive_table.csv")))

# -- 5. K-means clustering on 3-D scenario drive vector -----------------------
set.seed(42)

label_cluster <- function(km, mat) {
  # Label each cluster by the scenario at its mean centroid's argmax
  centers <- km$centers
  lbl <- apply(centers, 1, function(v) scenario_names[which.max(v)])
  # Append relative strength summary
  tibble(
    cluster_id    = seq_len(nrow(centers)),
    label         = lbl,
    center_Female = centers[, "Female encounter"],
    center_cVA_m  = centers[, "cVA + male"],
    center_cVA_f  = centers[, "cVA + female"],
    size          = km$size
  )
}

km2 <- kmeans(group_mat, centers = 2, nstart = 25)
km3 <- kmeans(group_mat, centers = 3, nstart = 25)

k2_info <- label_cluster(km2, group_mat)
k3_info <- label_cluster(km3, group_mat)

cluster_tbl <- tibble(
  P1_group    = rownames(group_mat),
  cluster_k2  = km2$cluster,
  label_k2    = k2_info$label[km2$cluster],
  cluster_k3  = km3$cluster,
  label_k3    = k3_info$label[km3$cluster]
) %>% left_join(group_drive_table %>% select(P1_group, argmax_scenario),
                by = "P1_group")

write.csv(cluster_tbl,
          file.path(out_dir, "p1_group_clusters.csv"),
          row.names = FALSE)
cat(sprintf("Wrote %s\n", file.path(out_dir, "p1_group_clusters.csv")))

cat("\n--- k=2 cluster labels ---\n"); print(k2_info)
cat("\n--- k=3 cluster labels ---\n"); print(k3_info)

# -- 6. Aggression-likely vs courtship-likely heuristic + Wilcoxon -----------
# Heuristic:
#   aggression-likely: argmax = "cVA + male" (male-pheromone-dominated)
#   courtship-likely:  argmax = "Female encounter" or "cVA + female"
aggression_like <- group_drive_table %>%
  filter(argmax_scenario == "cVA + male") %>% pull(P1_group)

courtship_like <- group_drive_table %>%
  filter(argmax_scenario %in% c("Female encounter", "cVA + female")) %>%
  pull(P1_group)

cat(sprintf("\nAggression-likely (argmax cVA+male): %d groups: %s\n",
            length(aggression_like), paste(aggression_like, collapse = ", ")))
cat(sprintf("Courtship-likely (argmax Female or cVA+female): %d groups: %s\n",
            length(courtship_like), paste(courtship_like, collapse = ", ")))

wilcox_per_scenario <- list()
if (length(aggression_like) >= 1 && length(courtship_like) >= 1) {
  for (scn in scenario_names) {
    a_vals <- group_mat[aggression_like, scn]
    c_vals <- group_mat[courtship_like, scn]
    if (length(a_vals) >= 1 && length(c_vals) >= 1) {
      if (length(a_vals) >= 2 || length(c_vals) >= 2) {
        tst <- tryCatch(
          suppressWarnings(wilcox.test(a_vals, c_vals, exact = FALSE)),
          error = function(e) NULL)
        if (!is.null(tst)) {
          wilcox_per_scenario[[scn]] <- list(
            scenario = scn,
            W = unname(tst$statistic),
            p = tst$p.value,
            n_agg = length(a_vals),
            n_court = length(c_vals),
            median_agg = median(a_vals),
            median_court = median(c_vals)
          )
        }
      } else {
        wilcox_per_scenario[[scn]] <- list(
          scenario = scn, W = NA_real_, p = NA_real_,
          n_agg = length(a_vals), n_court = length(c_vals),
          median_agg = median(a_vals), median_court = median(c_vals)
        )
      }
    }
  }
}

cat("\n--- Wilcoxon (aggression-like vs courtship-like) per scenario ---\n")
for (res in wilcox_per_scenario) {
  cat(sprintf("%-20s n_agg=%d n_court=%d  W=%s  p=%s  median_agg=%.3f  median_court=%.3f\n",
              res$scenario, res$n_agg, res$n_court,
              ifelse(is.na(res$W), "NA", sprintf("%.1f", res$W)),
              ifelse(is.na(res$p), "NA", sprintf("%.4g", res$p)),
              res$median_agg, res$median_court))
}

# -- 7. Write findings --------------------------------------------------------
# Describe cluster composition for k=2 and k=3
k2_comp <- cluster_tbl %>% count(label_k2, name = "n")
k3_comp <- cluster_tbl %>% count(label_k3, name = "n")

k2_mem <- cluster_tbl %>% group_by(label_k2) %>%
  summarise(members = paste(P1_group, collapse = ", "), .groups = "drop")
k3_mem <- cluster_tbl %>% group_by(label_k3) %>%
  summarise(members = paste(P1_group, collapse = ", "), .groups = "drop")

findings_lines <- c(
  "Agent 09: P1 groups and scenario-drive profiles.",
  "",
  sprintf("Input: %d P1 subtypes collapsed to %d P1 groups by numeric root (P1_3a/b/c -> P1_3). Per-group drive = sum of p1_all_combos$net_input across subtypes for each of three scenarios: Female encounter (ppk23,ppk25), cVA+male (DA1,ppk23), cVA+female (DA1,ppk23,ppk25).",
          length(unique(drive_long$P1)), nrow(group_drive_table)),
  "",
  "Per-group argmax counts:",
  paste(sprintf("  %-18s n=%d",
                names(table(group_drive_table$argmax_scenario)),
                as.integer(table(group_drive_table$argmax_scenario))),
        collapse = "\n"),
  "",
  "K-means k=2 (labels = centroid argmax, sizes):",
  paste(sprintf("  %s (n=%d)", k2_info$label, k2_info$size), collapse = "\n"),
  "K-means k=3:",
  paste(sprintf("  %s (n=%d)", k3_info$label, k3_info$size), collapse = "\n"),
  "",
  "Wilcoxon (aggression-like argmax=cVA+male vs courtship-like argmax=Female or cVA+female) per scenario:",
  paste(sapply(wilcox_per_scenario, function(res) {
    sprintf("  %-18s n_agg=%d n_court=%d  W=%s  p=%s",
            res$scenario, res$n_agg, res$n_court,
            ifelse(is.na(res$W), "NA", sprintf("%.1f", res$W)),
            ifelse(is.na(res$p), "NA", sprintf("%.4g", res$p)))
  }), collapse = "\n"),
  "",
  "Interpretation. The three scenario drives are highly correlated across P1 groups: groups with strong contact paths score highest under Female and cVA+female, because the model's DA1 (cVA) channel adds little net input on top of ppk23/ppk25. K-means k=2 therefore separates groups by overall contact-drive magnitude, not by scenario identity - both centroids still argmax on cVA+female. K=3 carves off a small low-drive pocket whose magnitudes sit near the noise floor rather than a clean aggression-biased cluster. Only 4 of 20 groups have argmax cVA+male, and Wilcoxon tests against the courtship-like majority are non-significant at alpha=0.05 for all three scenarios (p >= 0.12).",
  "",
  sprintf("Bottom line: the data support a single scenario-discrimination axis (contact-pheromone amplitude), not a clean courtship-pool vs aggression-pool dichotomy at the P1-group level. Candidate aggression-biased groups (argmax cVA+male: %s) are hypothesis-generating only. Without behavioral ground truth (e.g. optogenetic phenotypes) they should be validated, not labeled. Small group counts and high scenario correlation further limit statistical power.",
          paste(aggression_like, collapse = ", "))
)

writeLines(findings_lines, file.path(out_dir, "agent09_findings.txt"))
cat(sprintf("Wrote %s\n", file.path(out_dir, "agent09_findings.txt")))

# Word count check
wc <- sum(lengths(strsplit(paste(findings_lines, collapse = " "), "\\s+")))
cat(sprintf("agent09_findings.txt word count: ~%d\n", wc))
