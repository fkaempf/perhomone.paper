# Threshold-sensitivity sweep for the GRASP design matrix.
#
# R_j = sum_i x_i * C[i,j] / sum_i C[i,j]   ;  fold = max(R,1-R) / min(R,1-R)
#
# The threshold is applied where neuprint applies it: to each individual
# bodyid -> bodyid edge, BEFORE aggregating to type level. That is exactly what
# fetch_connectivity(synapse_threshold = 5) and neuprint_connection_table(threshold=)
# do, so the sweep is like-for-like with both the old cache and the v1.0 fetch.

suppressMessages({library(dplyr); library(tidyr); library(tibble); library(purrr)})

D    <- "/Users/fkampf/Documents/pheromone.paper/receptor_typing_validation/data"
PPK  <- c("WG3","WG4","LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")
H0   <- c("WG3","LgLG1b","LgLG5","LgLG8")          # ppk25+ under H0
x0   <- setNames(as.numeric(PPK %in% H0), PPK)
SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")
THR  <- c(0, 1, 2, 3, 5, 10)

TARGETS <- c(
  # wing-heavy
  "AN17A003","AN05B096","AN05B107","AN09B013","INXXX238","INXXX044","IN11A032_a","IN11A022",
  # leg-only
  "AN01B004","DNpe029","IN23B025","AN09B017b","IN23B020","AN09B017g","IN17A013","IN01B065",
  # mixed
  "AN05B023c","AN05B023b","IN05B002","AN13B002","ANXXX093","AN05B102a")

# ---- core: edge list + threshold -> per-target table --------------------------------
design_at <- function(edges, t) {
  keep_w <- if (t <= 0) 1L else as.integer(t)      # no zero-weight edges exist in neuprint
  M <- edges %>%
    filter(!is.na(post_type), post_type != "", weight >= keep_w) %>%
    group_by(post_type, pre_type) %>%
    summarise(w = sum(weight), .groups = "drop") %>%
    pivot_wider(names_from = pre_type, values_from = w, values_fill = 0)
  for (p in PPK) if (!p %in% names(M)) M[[p]] <- 0
  Mm <- as.matrix(M[, PPK]); rownames(Mm) <- M$post_type
  Mm <- Mm[!rownames(Mm) %in% SENS, , drop = FALSE]
  tot <- rowSums(Mm)
  Mm <- Mm[tot > 0, , drop = FALSE]; tot <- tot[tot > 0]
  Fm <- Mm / tot
  R0 <- as.vector(Fm %*% x0)
  tibble(threshold = t, target = rownames(Fm), syn = as.integer(tot),
         R0 = R0,
         fold = pmax(R0, 1 - R0) / pmin(R0, 1 - R0),
         wing = rowSums(Fm[, c("WG3","WG4"), drop = FALSE]),
         WG3  = Fm[,"WG3"], WG4 = Fm[,"WG4"])
}

sweep_all <- function(edges) map_dfr(THR, ~design_at(edges, .x))

e10 <- readRDS(file.path(D, "raw_edges_v1.0.rds"))
e09 <- readRDS(file.path(D, "raw_edges_v0.9.rds"))
s10 <- sweep_all(e10)
s09 <- sweep_all(e09)
saveRDS(list(v1.0 = s10, v0.9 = s09, thresholds = THR, targets = TARGETS),
        file.path(D, "threshold_sweep.rds"))

fmt <- function(x, d = 3) formatC(x, format = "f", digits = d)
wide <- function(tb, col, d) {
  tb %>% filter(target %in% TARGETS) %>%
    select(target, threshold, v = all_of(col)) %>%
    mutate(v = fmt(v, d)) %>%
    pivot_wider(names_from = threshold, values_from = v,
                names_prefix = "t", values_fill = "  --") %>%
    mutate(target = factor(target, levels = TARGETS)) %>% arrange(target) %>%
    as.data.frame()
}

# =========================== 1. REPRODUCTION CHECK ==================================
cat("################ 1. REPRODUCE THE CLAIMED v1.0 UNTHRESHOLDED NUMBERS ################\n")
claim <- tribble(
  ~target, ~syn_c, ~R0_c, ~fold_c,
  "AN17A003",   584, 0.983, 57.4, "AN05B096",   217, 0.982, 53.2,
  "AN05B107",   231, 0.974, 37.5, "AN09B013",   242, 0.955, 21.0,
  "INXXX238",   448, 0.900,  9.0, "INXXX044",   863, 0.783,  3.6,
  "IN11A032_a", 494, 0.251,  3.0, "IN11A022",  2233, 0.312,  2.2,
  "AN01B004",   178, 0.966, 28.7, "DNpe029",    814, 0.934, 14.1,
  "IN23B025",   405, 0.928, 13.0, "AN09B017b", 1091, 0.090, 10.1,
  "IN23B020",   662, 0.899,  8.9, "AN09B017g", 1960, 0.896,  8.6,
  "IN17A013",  1711, 0.129,  6.7, "IN01B065",  1847, 0.153,  5.5,
  "AN05B023c", 6142, 0.929, 13.1, "AN05B023b",12667, 0.088, 10.3,
  "IN05B002", 19674, 0.155,  5.5, "AN13B002",  6787, 0.819,  4.5,
  "ANXXX093",  7540, 0.824,  4.7, "AN05B102a",27267, 0.406,  1.5)
rep_chk <- s10 %>% filter(threshold == 1, target %in% TARGETS) %>%
  select(target, syn, R0, fold) %>%
  right_join(claim, by = "target") %>%
  mutate(dsyn = syn - syn_c, dR0 = round(R0 - R0_c, 4),
         R0 = round(R0,3), fold = round(fold,1),
         match = ifelse(abs(dR0) <= 0.0015 & dsyn == 0, "ok", "MISMATCH")) %>%
  mutate(target = factor(target, levels = TARGETS)) %>% arrange(target)
print(as.data.frame(rep_chk %>% select(target, syn, syn_c, dsyn, R0, R0_c, dR0, fold, fold_c, match)),
      row.names = FALSE)
cat("\nreproduced exactly:", sum(rep_chk$match == "ok"), "of", nrow(rep_chk), "\n")

# =========================== 2. THE TABLES ==========================================
cat("\n\n################ 2a. R0 BY THRESHOLD (male-cns:v1.0) ################\n")
print(wide(s10, "R0", 3), row.names = FALSE)
cat("\n################ 2b. FOLD BY THRESHOLD (male-cns:v1.0) ################\n")
print(wide(s10, "fold", 1), row.names = FALSE)
cat("\n################ 2c. ppk-family SYNAPSES SURVIVING EACH THRESHOLD ################\n")
print(wide(s10, "syn", 0), row.names = FALSE)

# =========================== 3. STABLE vs FRAGILE ===================================
cat("\n\n################ 3. STABILITY CLASSIFICATION ################\n")
cat("side  = sign(R0 - 0.5): which hypothesis arm the target's puncta ratio points to\n")
cat("usable(3x) = fold >= 3 (a ratio a GRASP experiment can actually resolve)\n\n")
stab <- s10 %>% filter(target %in% TARGETS) %>%
  group_by(target) %>%
  summarise(R0_min = min(R0), R0_max = max(R0), R0_range = R0_max - R0_min,
            fold_min = min(fold), fold_max = max(fold), fold_ratio = fold_max / fold_min,
            side_flips = n_distinct(R0 > 0.5),
            usable_at = sum(fold >= 3), n_thr = n(),
            syn_t10 = syn[threshold == 10], syn_t0 = syn[threshold == 0],
            .groups = "drop") %>%
  mutate(verdict = case_when(
    side_flips > 1                              ~ "FRAGILE (side flips)",
    usable_at != n_thr & usable_at != 0         ~ "FRAGILE (crosses 3x usability)",
    fold_ratio >= 3                             ~ "FRAGILE (fold moves >=3x)",
    fold_ratio >= 1.75                          ~ "SOFT (fold moves 1.75-3x)",
    TRUE                                        ~ "STABLE"),
    across(c(R0_min,R0_max,R0_range), ~round(.x,3)),
    across(c(fold_min,fold_max,fold_ratio), ~round(.x,1)),
    target = factor(target, levels = TARGETS)) %>% arrange(target)
print(as.data.frame(stab %>% select(target, syn_t0, syn_t10, R0_min, R0_max, R0_range,
                                    fold_min, fold_max, fold_ratio, usable_at, verdict)),
      row.names = FALSE)
cat("\n")
print(stab %>% count(verdict) %>% as.data.frame(), row.names = FALSE)

# =========================== 4. AN17A003 IN DEPTH ===================================
cat("\n\n################ 4. AN17A003: DOES IT STAY THE BEST TARGET? ################\n")
an17 <- s10 %>% filter(target == "AN17A003") %>%
  mutate(R0 = round(R0,3), fold = round(fold,1), wing = round(wing,3),
         WG3 = round(WG3,3), WG4 = round(WG4,3))
print(as.data.frame(an17 %>% select(threshold, syn, R0, fold, wing, WG3, WG4)), row.names = FALSE)

rank_of <- function(tb, tgt, min_syn) {
  map_dfr(THR, function(t) {
    p <- tb %>% filter(threshold == t, syn >= min_syn) %>% arrange(desc(fold))
    i <- match(tgt, p$target)
    tibble(threshold = t, n_pool = nrow(p),
           rank = ifelse(is.na(i), NA_integer_, i),
           fold = ifelse(is.na(i), NA_real_, round(p$fold[i],1)),
           best = p$target[1], best_fold = round(p$fold[1],1), best_syn = p$syn[1])
  })
}
cat("\n-- rank by fold among ALL non-sensory targets with >=150 surviving ppk synapses --\n")
print(as.data.frame(rank_of(s10, "AN17A003", 150)), row.names = FALSE)
cat("\n-- rank by fold among ALL non-sensory targets with >=300 surviving ppk synapses --\n")
print(as.data.frame(rank_of(s10, "AN17A003", 300)), row.names = FALSE)
cat("\n-- rank by fold within the 22 listed candidate targets --\n")
print(as.data.frame(rank_of(s10 %>% filter(target %in% TARGETS), "AN17A003", 0)), row.names = FALSE)

cat("\n-- what actually happens to AN17A003's WG4 input as the threshold rises --\n")
an17_edges <- e10 %>% filter(post_type == "AN17A003") %>%
  group_by(pre_type) %>%
  summarise(n_edges = n(), syn = sum(weight), max_w = max(weight),
            med_w = median(weight), syn_ge3 = sum(weight[weight>=3]),
            syn_ge5 = sum(weight[weight>=5]), .groups="drop") %>% arrange(desc(syn))
print(as.data.frame(an17_edges), row.names = FALSE)

# =========================== 5. VERSION vs THRESHOLD ================================
cat("\n\n################ 5. v0.9 vs v1.0, INDEPENDENTLY, AT EACH THRESHOLD ################\n")
cat("If the shift was caused by the THRESHOLD and not the VERSION, then at a matched\n")
cat("threshold the two versions must agree, and the t=5 vs t=1 gap must be large.\n\n")
ver <- s10 %>% select(target, threshold, R0_v10 = R0, syn_v10 = syn) %>%
  full_join(s09 %>% select(target, threshold, R0_v09 = R0, syn_v09 = syn),
            by = c("target","threshold")) %>%
  filter(target %in% TARGETS) %>%
  mutate(dR0_version = R0_v10 - R0_v09)
cat("-- |dR0| between versions, at each matched threshold --\n")
print(ver %>% select(target, threshold, dR0_version) %>%
        mutate(dR0_version = round(dR0_version, 4)) %>%
        pivot_wider(names_from = threshold, values_from = dR0_version, names_prefix = "t") %>%
        mutate(target = factor(target, levels = TARGETS)) %>% arrange(target) %>%
        as.data.frame(), row.names = FALSE)
cat("\nmax |dR0(version)| at t=0 across all", length(TARGETS), "targets:",
    round(max(abs(ver$dR0_version[ver$threshold == 0]), na.rm = TRUE), 4), "\n")
cat("max |dR0(version)| at t=0 across ALL targets with >=150 syn: ")
allv <- s10 %>% filter(threshold == 0, syn >= 150) %>% select(target, R0_v10 = R0) %>%
  inner_join(s09 %>% filter(threshold == 0) %>% select(target, R0_v09 = R0), by = "target")
cat(round(max(abs(allv$R0_v10 - allv$R0_v09)), 4), " (n =", nrow(allv), "targets)\n")

cat("\n-- head-to-head: version effect vs threshold effect, same targets --\n")
eff <- s10 %>% filter(target %in% TARGETS, threshold %in% c(0,5)) %>%
  select(target, threshold, R0) %>%
  pivot_wider(names_from = threshold, values_from = R0, names_prefix = "R0_t") %>%
  left_join(ver %>% filter(threshold == 0) %>% select(target, dR0_version), by = "target") %>%
  mutate(dR0_threshold = R0_t5 - R0_t0,
         ratio = abs(dR0_threshold) / pmax(abs(dR0_version), 1e-4)) %>%
  mutate(across(where(is.numeric), ~round(.x, 4)),
         target = factor(target, levels = TARGETS)) %>% arrange(target)
print(as.data.frame(eff %>% select(target, R0_t0, R0_t5, dR0_threshold, dR0_version, ratio)),
      row.names = FALSE)
cat("\nmedian |dR0| from threshold 0->5 :", round(median(abs(eff$dR0_threshold)), 4), "\n")
cat("median |dR0| from version 0.9->1.0:", round(median(abs(eff$dR0_version)), 4), "\n")

# =========================== 6. WHAT THE THRESHOLD REMOVES ==========================
cat("\n\n################ 6. WEIGHT SPECTRUM OF ppk-FAMILY EDGES (v1.0) ################\n")
spec <- e10 %>% filter(!is.na(post_type), post_type != "") %>%
  mutate(bin = cut(weight, c(0,1,2,3,4,5,9,Inf),
                   labels = c("1","2","3","4","5","6-9","10+"))) %>%
  group_by(bin) %>% summarise(n_edges = n(), syn = sum(weight), .groups="drop") %>%
  mutate(pct_edges = round(100*n_edges/sum(n_edges),1), pct_syn = round(100*syn/sum(syn),1))
print(as.data.frame(spec), row.names = FALSE)
cat("\nfraction of ALL ppk-family synapses removed at each threshold:\n")
tot_all <- sum(e10$weight[!is.na(e10$post_type) & e10$post_type != ""])
for (t in THR) {
  kept <- sum(e10$weight[!is.na(e10$post_type) & e10$post_type != "" &
                           e10$weight >= max(t,1)])
  cat(sprintf("  t=%-2d  kept %6d syn (%5.1f%%)  removed %5.1f%% of synapses, %5.1f%% of edges\n",
              t, kept, 100*kept/tot_all, 100*(1-kept/tot_all),
              100*mean(e10$weight[!is.na(e10$post_type) & e10$post_type != ""] < max(t,1))))
}

cat("\n-- per-sensory-type weight profile: does thresholding hit types unequally? --\n")
byt <- e10 %>% filter(!is.na(post_type), post_type != "") %>%
  group_by(pre_type) %>%
  summarise(n_edges = n(), syn = sum(weight), mean_w = round(mean(weight),2),
            med_w = median(weight), pct_syn_lost_t5 = round(100*sum(weight[weight<5])/sum(weight),1),
            pct_syn_lost_t3 = round(100*sum(weight[weight<3])/sum(weight),1),
            .groups = "drop") %>% arrange(desc(syn))
print(as.data.frame(byt), row.names = FALSE)

cat("\nDONE\n")
