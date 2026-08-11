# Diagnostics for the threshold sweep.
#
# 07b showed fold -> Inf for many targets at t>=2. That is a degenerate metric: it happens
# the moment the minority arm's synapse count hits exactly zero, which for a target whose
# minority input is a handful of 1-synapse edges happens for purely arithmetic reasons.
# Here we (a) regularise fold, (b) count what is actually in the minority arm, (c) ask
# whether the synapse-count model of GRASP is even the right one, and (d) bootstrap.

suppressMessages({library(dplyr); library(tidyr); library(tibble); library(purrr)})
set.seed(1)

D    <- "/Users/fkampf/Documents/pheromone.paper/receptor_typing_validation/data"
PPK  <- c("WG3","WG4","LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")
H0   <- c("WG3","LgLG1b","LgLG5","LgLG8")
SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")
THR  <- c(0,1,2,3,5,10)
TARGETS <- c("AN17A003","AN05B096","AN05B107","AN09B013","INXXX238","INXXX044","IN11A032_a",
             "IN11A022","AN01B004","DNpe029","IN23B025","AN09B017b","IN23B020","AN09B017g",
             "IN17A013","IN01B065","AN05B023c","AN05B023b","IN05B002","AN13B002","ANXXX093",
             "AN05B102a")

e10 <- readRDS(file.path(D, "raw_edges_v1.0.rds")) %>%
  filter(!is.na(post_type), post_type != "", !post_type %in% SENS) %>%
  mutate(is25 = pre_type %in% H0)

# ---- 1. regularised fold + minority-arm audit --------------------------------------
tab <- map_dfr(THR, function(t) {
  e10 %>% filter(weight >= max(t,1)) %>%
    group_by(post_type) %>%
    summarise(syn = sum(weight),
              n25 = sum(weight[is25]), n23 = sum(weight[!is25]),
              e25 = sum(is25), e23 = sum(!is25),
              .groups = "drop") %>%
    mutate(threshold = t, R0 = n25/syn,
           n_min   = pmin(n25, n23),
           e_min   = ifelse(n25 < n23, e25, e23),
           fold    = pmax(R0,1-R0)/pmin(R0,1-R0),
           fold_adj = pmax(n25,n23) / (pmin(n25,n23) + 1))   # +1 pseudocount, never Inf
})

pv <- function(col, d) tab %>% filter(post_type %in% TARGETS) %>%
  select(post_type, threshold, v = all_of(col)) %>%
  mutate(v = formatC(v, format="f", digits=d)) %>%
  pivot_wider(names_from = threshold, values_from = v, names_prefix = "t", values_fill = "  --") %>%
  mutate(post_type = factor(post_type, levels = TARGETS)) %>% arrange(post_type) %>% as.data.frame()

cat("################ 1a. REGULARISED FOLD  max(n25,n23)/(min+1)  ################\n")
cat("Replaces the Inf entries in 07b. Ranking by this is meaningful at every threshold.\n\n")
print(pv("fold_adj", 1), row.names = FALSE)

cat("\n################ 1b. MINORITY-ARM SYNAPSE COUNT (what the fold is dividing by) ################\n")
print(pv("n_min", 0), row.names = FALSE)

cat("\n################ 1c. MINORITY-ARM EDGE COUNT ################\n")
print(pv("e_min", 0), row.names = FALSE)

cat("\n################ 1d. RANK BY REGULARISED FOLD, pool = syn >= 150 at that threshold ################\n")
rk <- map_dfr(THR, function(t) {
  p <- tab %>% filter(threshold == t, syn >= 150) %>% arrange(desc(fold_adj))
  i <- match("AN17A003", p$post_type)
  tibble(threshold = t, n_pool = nrow(p),
         AN17A003_rank = i, AN17A003_foldadj = round(p$fold_adj[i],1),
         AN17A003_syn = p$syn[i],
         top1 = p$post_type[1], top1_foldadj = round(p$fold_adj[1],1), top1_syn = p$syn[1],
         top2 = p$post_type[2], top2_foldadj = round(p$fold_adj[2],1), top2_syn = p$syn[2],
         top3 = p$post_type[3], top3_foldadj = round(p$fold_adj[3],1), top3_syn = p$syn[3])
})
print(as.data.frame(rk), row.names = FALSE)

# ---- 2. is the synapse-count model of GRASP the right one? -------------------------
cat("\n\n################ 2. THREE MODELS OF WHAT A GRASP PUNCTUM COUNTS ################\n")
cat("syn  : R = sum of synapse weights          (puncta proportional to synapse number)\n")
cat("edge : R = count of contacting neuron pairs (one punctum per apposition site)\n")
cat("cell : R = count of distinct labelled presynaptic neurons touching the target\n")
cat("The spread across these three is the model uncertainty the threshold sweep sits inside.\n\n")
models <- map_dfr(THR, function(t) {
  x <- e10 %>% filter(weight >= max(t,1))
  syn  <- x %>% group_by(post_type) %>% summarise(R_syn  = sum(weight[is25])/sum(weight), .groups="drop")
  edg  <- x %>% group_by(post_type) %>% summarise(R_edge = sum(is25)/n(), .groups="drop")
  cel  <- x %>% distinct(post_type, pre_id, is25) %>% group_by(post_type) %>%
          summarise(R_cell = sum(is25)/n(), .groups="drop")
  syn %>% left_join(edg, by="post_type") %>% left_join(cel, by="post_type") %>% mutate(threshold = t)
})
m0 <- models %>% filter(threshold %in% c(0,3,5), post_type %in% TARGETS) %>%
  mutate(across(starts_with("R_"), ~round(.x,3))) %>%
  pivot_wider(names_from = threshold, values_from = c(R_syn, R_edge, R_cell)) %>%
  select(post_type, R_syn_0, R_edge_0, R_cell_0, R_syn_3, R_edge_3, R_cell_3,
         R_syn_5, R_edge_5, R_cell_5) %>%
  mutate(post_type = factor(post_type, levels = TARGETS)) %>% arrange(post_type)
print(as.data.frame(m0), row.names = FALSE)

sprd <- models %>% filter(threshold == 0, post_type %in% TARGETS) %>%
  rowwise() %>% mutate(model_spread = max(c(R_syn,R_edge,R_cell)) - min(c(R_syn,R_edge,R_cell))) %>%
  ungroup()
thr_sp <- tab %>% filter(post_type %in% TARGETS) %>% group_by(post_type) %>%
  summarise(thr_spread = max(R0) - min(R0), .groups="drop")
cmp <- sprd %>% select(post_type, model_spread) %>% left_join(thr_sp, by="post_type") %>%
  mutate(across(where(is.numeric), ~round(.x,3)),
         bigger = ifelse(model_spread > thr_spread, "MODEL", "THRESHOLD"),
         post_type = factor(post_type, levels=TARGETS)) %>% arrange(post_type)
cat("\n-- model spread (at t=0) vs threshold spread (t=0..10), same target --\n")
print(as.data.frame(cmp), row.names = FALSE)
cat("\nmedian model spread:", round(median(cmp$model_spread),3),
    "  median threshold spread:", round(median(cmp$thr_spread),3), "\n")

# ---- 3. bootstrap over presynaptic neurons ----------------------------------------
cat("\n\n################ 3. BOOTSTRAP OVER PRESYNAPTIC NEURONS (t=0 and t=3) ################\n")
cat("Resample sensory neurons within type with replacement, 2000x. This is the sampling\n")
cat("noise from having only ~96 WG3 / ~96 WG4 / ~13-21 LgLG neurons reconstructed.\n\n")
ids <- e10 %>% distinct(pre_id, pre_type)
boot_one <- function(t, B = 2000) {
  x <- e10 %>% filter(weight >= max(t,1))
  by_pre <- split(x, x$pre_id)
  bytype <- split(ids$pre_id, ids$pre_type)
  res <- map_dfr(seq_len(B), function(b) {
    samp <- unlist(lapply(bytype, function(v) sample(v, length(v), replace = TRUE)))
    xb <- bind_rows(by_pre[as.character(samp)])
    xb %>% filter(post_type %in% TARGETS) %>% group_by(post_type) %>%
      summarise(R = sum(weight[is25])/sum(weight), .groups="drop")
  })
  res %>% group_by(post_type) %>%
    summarise(lo = quantile(R, .025), hi = quantile(R, .975), .groups="drop") %>%
    mutate(threshold = t)
}
bt <- bind_rows(boot_one(0), boot_one(3))
bo <- tab %>% filter(post_type %in% TARGETS, threshold %in% c(0,3)) %>%
  select(post_type, threshold, R0, n_min) %>% left_join(bt, by=c("post_type","threshold")) %>%
  mutate(across(c(R0,lo,hi), ~round(.x,3)), ci = paste0("[",lo,", ",hi,"]")) %>%
  select(post_type, threshold, R0, ci, n_min) %>%
  pivot_wider(names_from=threshold, values_from=c(R0,ci,n_min)) %>%
  mutate(post_type = factor(post_type, levels=TARGETS)) %>% arrange(post_type)
print(as.data.frame(bo), row.names = FALSE)

cat("\n-- does the t=0 bootstrap CI contain the t=5 point estimate? --\n")
t5 <- tab %>% filter(threshold == 5, post_type %in% TARGETS) %>% select(post_type, R0_t5 = R0)
ov <- bt %>% filter(threshold == 0) %>% left_join(t5, by="post_type") %>%
  mutate(inside = R0_t5 >= lo & R0_t5 <= hi,
         across(c(lo,hi,R0_t5), ~round(.x,3)),
         post_type = factor(post_type, levels=TARGETS)) %>% arrange(post_type)
print(as.data.frame(ov %>% select(post_type, lo, hi, R0_t5, inside)), row.names = FALSE)
cat("\nt=5 estimate lies OUTSIDE the t=0 sampling CI for ",
    sum(!ov$inside, na.rm=TRUE), " of ", sum(!is.na(ov$inside)),
    " targets -> the threshold shift is not sampling noise, it is a systematic bias.\n", sep="")

saveRDS(list(tab = tab, models = models, boot = bt), file.path(D, "sweep_diagnostics.rds"))
cat("\nDONE\n")
