# Final target selection: male-cns:v1.0, UNTHRESHOLDED. Supersedes 01-03 (which used the
# path-analysis cache, thresholded at 5 synapses — wrong basis for predicting puncta ratios).
options(malecns.dataset = "male-cns:v1.0")
suppressMessages({library(dplyr); library(tidyr); library(tibble)})

D <- readRDS("receptor_typing_validation/data/design_matrix_v1.0.rds")
stopifnot(D$dataset == "male-cns:v1.0")
SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")

Fm <- D$Fm; tot <- D$tot; TY <- D$types; x0 <- setNames(D$x0, TY)
keep <- !rownames(Fm) %in% SENS
Fm <- Fm[keep,,drop=FALSE]; tot <- tot[keep]
R0 <- as.vector(Fm %*% x0)
fold <- pmax(R0, 1-R0) / pmin(R0, 1-R0)
wing <- rowSums(Fm[, c("WG3","WG4"), drop=FALSE])
leg  <- rowSums(Fm[, setdiff(TY, c("WG3","WG4")), drop=FALSE])

tb <- tibble(target=rownames(Fm), syn=tot, R0=round(R0,3), fold=round(fold,1),
             wing=round(wing,3), leg=round(leg,3))

cat("################ WING-ONLY TARGETS (wing >= 0.90) ################\n")
w <- tb %>% filter(wing >= 0.90, syn >= 150) %>% arrange(desc(fold))
print(as.data.frame(w %>% head(20)), row.names=FALSE)
cat("\n  usable (fold >= 3, syn >= 300):", sum(w$fold >= 3 & w$syn >= 300), "of", nrow(w), "\n")

cat("\n################ LEG-ONLY TARGETS (leg >= 0.90) ################\n")
l <- tb %>% filter(leg >= 0.90, syn >= 150) %>% arrange(desc(fold))
print(as.data.frame(l %>% head(15)), row.names=FALSE)

cat("\n################ BEST OVERALL (any mix, syn >= 500) ################\n")
print(as.data.frame(tb %>% filter(syn >= 500) %>% arrange(desc(fold)) %>% head(15)), row.names=FALSE)

cat("\n################ WG3 vs WG4 SEPARATION (wing assignment) ################\n")
# a target useful for the WING assignment must load WG3 and WG4 very unequally
wsep <- tb %>% mutate(wg3 = round(Fm[,"WG3"],3), wg4 = round(Fm[,"WG4"],3),
                      wg_ratio = round(pmax(wg3,wg4)/pmax(pmin(wg3,wg4),1e-4),1)) %>%
        filter(wing >= 0.50, syn >= 150) %>% arrange(desc(wg_ratio))
print(as.data.frame(wsep %>% select(target,syn,wing,wg3,wg4,wg_ratio,R0,fold) %>% head(15)), row.names=FALSE)

cat("\n################ PER-TYPE ISOLATORS ################\n")
iso <- lapply(TY, function(t){
  cand <- which(tot >= 150)
  i <- cand[which.max(Fm[cand, t])]
  f <- Fm[i,]
  tibble(type=t, target=rownames(Fm)[i], loading=round(f[[t]],3), syn=tot[i],
         R_if_ppk25=round(sum(f*replace(x0,t,1)),3), R_if_not=round(sum(f*replace(x0,t,0)),3))
}) %>% bind_rows() %>% mutate(delta=round(abs(R_if_ppk25-R_if_not),3))
print(as.data.frame(iso), row.names=FALSE)

write.csv(tb %>% arrange(desc(fold*sqrt(syn))),
          "receptor_typing_validation/data/targets_v1.0_final.csv", row.names=FALSE)
