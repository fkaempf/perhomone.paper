# Per-body consistency for the leg-arm candidates. A type whose R is carried by one
# body is useless for GRASP: a driver labels the whole type and the signal dilutes.
options(malecns.dataset = "male-cns:v1.0")
suppressMessages({library(neuprintr); library(dplyr); library(tidyr); library(tibble)})
DS <- "male-cns:v1.0"; neuprint_login(server="https://neuprint-cns.janelia.org", dataset=DS)

PPK <- c("WG3","WG4","LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")
LEG <- c("LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")
H0  <- c("WG3","LgLG1b","LgLG5","LgLG8")
TARGETS <- c("DNpe029","IN23B025","IN23B020","AN17A024","IN17A013","IN07B010",
             "IN01B065","AN17A013","AN09B017b","AN09B017g","AN09B017c","AN05B023b","AN05B023c")

ids <- lapply(PPK, function(t){
  m <- neuprint_search(sprintf("^%s$",t), field="type", dataset=DS, all_segments=FALSE)
  tibble(pre_type=t, bodyid=m$bodyid)}) %>% bind_rows()
ct <- neuprint_connection_table(ids$bodyid, prepost="POST", dataset=DS, details=TRUE,
                                threshold=1L, progress=FALSE) %>% left_join(ids, by="bodyid")
pm <- neuprint_get_meta(unique(ct$partner), dataset=DS)
ct <- ct %>% left_join(pm %>% select(bodyid, post_type=type), by=c("partner"="bodyid"))

cat("=== per-body leg-arm R, all bodies of each type ===\n")
for (tg in TARGETS) {
  bodies <- pm %>% filter(type == tg) %>% pull(bodyid)
  rows <- ct %>% filter(partner %in% bodies, pre_type %in% LEG)
  per <- rows %>% group_by(partner) %>%
    summarise(leg_syn = sum(weight),
              R = sum(weight[pre_type %in% H0]) / sum(weight), .groups="drop")
  miss <- setdiff(bodies, per$partner)
  per <- bind_rows(per, tibble(partner=miss, leg_syn=0, R=NA_real_)) %>% arrange(desc(leg_syn))
  pooled <- sum(rows$weight[rows$pre_type %in% H0]) / max(sum(rows$weight),1)
  drop1  <- {p2 <- per %>% slice(-1) %>% filter(leg_syn>0)
             if (!nrow(p2)) NA else sum(p2$R*p2$leg_syn)/sum(p2$leg_syn)}
  cat(sprintf("\n%-11s bodies=%d  with_input=%d  pooled_R=%.3f  drop-largest_R=%s  SD=%s\n",
      tg, length(bodies), sum(per$leg_syn>0), pooled,
      ifelse(is.na(drop1),"n/a",sprintf("%.3f",drop1)),
      ifelse(sum(per$leg_syn>0)<2,"n/a",sprintf("%.3f",sd(per$R[per$leg_syn>0])))))
  cat("   ", paste(sprintf("%d:%.0fsyn/R=%s", per$partner, per$leg_syn,
        ifelse(is.na(per$R),"--",sprintf("%.2f",per$R))), collapse="  "), "\n")
}
