# Final shortlist: per-type isolator targets + predicted GRASP readouts.
suppressMessages({library(dplyr); library(tidyr); library(tibble)})

D   <- readRDS("receptor_typing_validation/data/design_matrix.rds")
SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")
keep <- D$tot >= 500 & !rownames(D$Fm) %in% SENS
Fm <- D$Fm[keep, , drop=FALSE]; tot <- D$tot[keep]
x0 <- setNames(D$x0, D$types)

cat("=== best isolator per sensory type ===\n")
iso <- lapply(D$types, function(t) {
  i <- which.max(Fm[, t])
  f <- Fm[i, ]
  tibble(type = t, best_target = rownames(Fm)[i], loading = round(f[[t]], 3),
         ppk_syn = tot[i],
         R_if_ppk25 = round(sum(f * replace(x0, t, 1)), 3),
         R_if_not   = round(sum(f * replace(x0, t, 0)), 3))
}) %>% bind_rows() %>% mutate(delta = round(abs(R_if_ppk25 - R_if_not), 3))
print(as.data.frame(iso), row.names = FALSE)

cat("\n=== minimal 3-target core set for the M/F swap ===\n")
R0 <- as.vector(Fm %*% x0)
core <- tibble(target = rownames(Fm), ppk_syn = tot,
               R_H0 = round(R0,3), R_H1_swap = round(1-R0,3),
               fold = round(pmax(R0,1-R0)/pmin(R0,1-R0),1)) %>%
  filter(target %in% c("AN05B023b","AN05B023c","IN11A020","IN11A022",
                       "IN01B065","ANXXX093","AN13B002","AN05B102a","IN05B002"))
print(as.data.frame(core), row.names = FALSE)

cat("\n=== wing-only vs leg-only targets (separate the two assignments) ===\n")
wing <- rowSums(Fm[, c("WG3","WG4"), drop=FALSE])
leg  <- rowSums(Fm[, c("LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8"), drop=FALSE])
purity <- tibble(target=rownames(Fm), ppk_syn=tot,
                 wing=round(wing,3), leg=round(leg,3), R_H0=round(R0,3)) %>%
  filter(pmax(wing,leg) >= 0.95, ppk_syn >= 500) %>% arrange(desc(abs(2*R_H0-1)))
print(as.data.frame(head(purity, 14)), row.names = FALSE)
