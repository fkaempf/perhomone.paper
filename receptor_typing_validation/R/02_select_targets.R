# Pick a minimal target set that makes the GRASP inverse problem solvable.
# Greedy selection maximising log-det of F'F (D-optimality) over normalised rows.

suppressMessages({library(arrow); library(dplyr); library(tidyr); library(stringr)})

D <- readRDS("receptor_typing_validation/data/design_matrix.rds")
SENS <- c("WG1","WG2","WG3","WG4","LgLG1a","LgLG1b","LgLG2","LgLG5","LgLG6","LgLG7","LgLG8")

keep <- D$tot >= 500 & !rownames(D$Fm) %in% SENS
Fm <- D$Fm[keep, , drop = FALSE]; tot <- D$tot[keep]

# greedy D-optimal: add the target that most increases log-det(F'F + ridge)
greedy <- function(Fm, k) {
  sel <- integer(0); ridge <- diag(1e-6, ncol(Fm))
  for (step in seq_len(k)) {
    best <- NA_integer_; bestv <- -Inf
    for (i in setdiff(seq_len(nrow(Fm)), sel)) {
      S <- Fm[c(sel, i), , drop = FALSE]
      v <- determinant(t(S) %*% S + ridge, logarithm = TRUE)$modulus
      if (v > bestv) { bestv <- v; best <- i }
    }
    sel <- c(sel, best)
    cat(sprintf("%2d. %-12s ppk_syn=%6d  logdet=%8.2f\n",
                step, rownames(Fm)[best], tot[best], as.numeric(bestv)))
  }
  rownames(Fm)[sel]
}

cat("=== greedy D-optimal target set (8 unknown types) ===\n")
sel <- greedy(Fm, 8)

S <- Fm[sel, , drop = FALSE]
cat("\ncondition number of selected design:", round(kappa(S), 1), "\n")
cat("rank:", qr(S)$rank, "of", ncol(S), "\n")

# which types remain unconstrained by this set?
cat("\nmax loading per type across selected targets:\n")
print(round(apply(S, 2, max), 3))

saveRDS(sel, "receptor_typing_validation/data/selected_targets.rds")

# --- annotate the shortlist with known names / synonyms ---------------------
mba <- read_feather("feather/mba.feather",
                    col_select = c("type","synonyms","class","superclass",
                                   "predicted_nt","soma_neuromere"))
short <- unique(c(sel, rownames(Fm)[order(-abs(2*(Fm %*% D$x0)-1) * sqrt(tot))][1:12]))
ann <- mba %>% filter(type %in% short) %>%
  group_by(type) %>%
  summarise(n_bodies = n(),
            class = paste(unique(na.omit(class)), collapse="/"),
            nt = paste(unique(na.omit(predicted_nt)), collapse="/"),
            neuromere = paste(unique(na.omit(soma_neuromere)), collapse="/"),
            synonyms = paste(unique(na.omit(synonyms)), collapse=" | "),
            .groups="drop")
cat("\n=== shortlist annotation ===\n")
print(as.data.frame(ann), row.names = FALSE)
write.csv(ann, "receptor_typing_validation/data/shortlist_annotation.csv", row.names = FALSE)
