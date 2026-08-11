# Rebuild the GRASP design matrix directly from male-cns:v1.0 (not the v0.9 feather cache).
options(malecns.dataset = "male-cns:v1.0")

suppressMessages({library(neuprintr); library(dplyr); library(tidyr); library(stringr); library(tibble)})

DS  <- getOption("malecns.dataset")
OUT <- "receptor_typing_validation/data"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
neuprint_login(server = "https://neuprint-cns.janelia.org", dataset = DS)
message("dataset: ", DS)

PPK_TYPES <- c("WG3","WG4","LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")
H0_PPK25  <- c("WG3","LgLG1b","LgLG5","LgLG8")

# bodyids per sensory type
ids <- lapply(PPK_TYPES, function(t) {
  m <- neuprint_search(sprintf("^%s$", t), field = "type", dataset = DS, all_segments = FALSE)
  if (is.null(m) || !nrow(m)) return(NULL)
  tibble(pre_type = t, bodyid = m$bodyid)
}) %>% bind_rows()
message(sprintf("sensory neurons: %d across %d types", nrow(ids), n_distinct(ids$pre_type)))

# their downstream partners
ct <- neuprint_connection_table(ids$bodyid, prepost = "POST", dataset = DS,
                                details = TRUE, progress = TRUE)
ct <- ct %>% left_join(ids, by = c("bodyid" = "bodyid"))

post_meta <- neuprint_get_meta(unique(ct$partner), dataset = DS)
ct <- ct %>% left_join(post_meta %>% select(bodyid, post_type = type),
                       by = c("partner" = "bodyid"))

C <- ct %>%
  filter(!is.na(post_type), post_type != "") %>%
  group_by(post_type, pre_type) %>%
  summarise(w = sum(weight), .groups = "drop") %>%
  pivot_wider(names_from = pre_type, values_from = w, values_fill = 0)
for (t in PPK_TYPES) if (!t %in% names(C)) C[[t]] <- 0
C <- C %>% select(post_type, all_of(PPK_TYPES))

M <- as.matrix(C[, PPK_TYPES]); rownames(M) <- C$post_type
tot <- rowSums(M); Fm <- M / tot
x0 <- as.numeric(PPK_TYPES %in% H0_PPK25)
R0 <- as.vector(Fm %*% x0)

res <- tibble(target = C$post_type, ppk_syn = tot, R0 = round(R0, 3),
              sep_swap = round(abs(2*R0 - 1), 3)) %>%
       bind_cols(as_tibble(round(Fm, 3)))
write.csv(res %>% arrange(desc(sep_swap * sqrt(tot))),
          file.path(OUT, "design_matrix_v1.0.csv"), row.names = FALSE)
saveRDS(list(M = M, Fm = Fm, tot = tot, types = PPK_TYPES, x0 = x0, dataset = DS),
        file.path(OUT, "design_matrix_v1.0.rds"))

SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")
keep <- tot >= 500 & !rownames(Fm) %in% SENS
Fk <- Fm[keep,,drop=FALSE]; tk <- tot[keep]

greedy <- function(Fm, k) {
  sel <- integer(0); ridge <- diag(1e-6, ncol(Fm))
  for (s in seq_len(k)) {
    best <- NA; bestv <- -Inf
    for (i in setdiff(seq_len(nrow(Fm)), sel)) {
      S <- Fm[c(sel, i), , drop = FALSE]
      v <- as.numeric(determinant(t(S) %*% S + ridge, logarithm = TRUE)$modulus)
      if (v > bestv) { bestv <- v; best <- i }
    }
    sel <- c(sel, best)
  }
  rownames(Fm)[sel]
}
sel <- greedy(Fk, 8); S <- Fk[sel,,drop=FALSE]
cat("\n=== v1.0 D-optimal set ===\n"); print(sel)
cat("rank:", qr(S)$rank, "of", ncol(S), "  condition:", round(kappa(S), 1), "\n")

cat("\n=== v1.0 vs v0.9 on the shortlist ===\n")
old <- read.csv(file.path(OUT, "design_matrix_full.csv"))
key <- c("AN05B023b","AN05B023c","IN01B065","IN05B002","ANXXX093","AN13B002",
         "IN11A022","INXXX044","AN09B017b","AN09B017g","AN05B102a")
cmp <- res %>% filter(target %in% key) %>% select(target, ppk_syn_v1 = ppk_syn, R0_v1 = R0) %>%
  left_join(old %>% select(target, ppk_syn_v09 = ppk_syn, R0_v09 = R0), by = "target") %>%
  mutate(dR0 = round(R0_v1 - R0_v09, 3),
         fold_v1 = round(pmax(R0_v1, 1-R0_v1) / pmin(R0_v1, 1-R0_v1), 1)) %>%
  arrange(desc(abs(2*R0_v1 - 1)))
print(as.data.frame(cmp), row.names = FALSE)
