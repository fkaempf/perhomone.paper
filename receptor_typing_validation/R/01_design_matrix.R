# Design matrix for GRASP-based receptor-type inference.
#
# Each candidate postsynaptic target j gives one equation
#     R_j = sum_i x_i * C[i,j] / sum_i C[i,j]
# where x_i = 1 if sensory type i is ppk25+, C = connectome synapse counts.
# Targets are useful only if their normalised rows span the space of x.

suppressMessages({library(arrow); library(dplyr); library(tidyr); library(stringr)})

OUT <- "receptor_typing_validation/data"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)

# ppk-family sensory types whose receptor identity is in question
PPK_TYPES <- c("WG3", "WG4", "LgLG1a", "LgLG1b",
               "LgLG5", "LgLG6", "LgLG7", "LgLG8")
# current assignment (setup.R:269-274): which are ppk23+/ppk25+ ("F")
H0_PPK25 <- c("WG3", "LgLG1b", "LgLG5", "LgLG8")

conn <- open_dataset("feather/connectivity.feather", format = "feather")

# collapse nerve suffixes: "WG3 _ADMN" -> "WG3"
edges <- conn %>%
  select(pre_type, post_type, weight, prepost) %>%
  filter(prepost == 1) %>%
  collect() %>%
  mutate(pre_base = str_trim(str_replace(pre_type, "\\s*_[A-Za-z0-9]+$", "")))

C <- edges %>%
  filter(pre_base %in% PPK_TYPES, !is.na(post_type), post_type != "") %>%
  group_by(post_type, pre_base) %>%
  summarise(w = sum(weight), .groups = "drop") %>%
  pivot_wider(names_from = pre_base, values_from = w, values_fill = 0)

for (t in PPK_TYPES) if (!t %in% names(C)) C[[t]] <- 0
C <- C %>% select(post_type, all_of(PPK_TYPES))

M <- as.matrix(C[, PPK_TYPES])
rownames(M) <- C$post_type
tot <- rowSums(M)
Fm <- M / tot                                   # normalised rows

x0 <- as.numeric(PPK_TYPES %in% H0_PPK25)       # current assignment
R0 <- as.vector(Fm %*% x0)                      # predicted ppk25 fraction, H0
# global swap hypothesis is the complement
sep_swap <- abs(2 * R0 - 1)

res <- tibble(
  target      = C$post_type,
  ppk_syn     = tot,
  R0          = round(R0, 3),
  sep_swap    = round(sep_swap, 3),
  # crude power proxy: separation weighted by signal
  score       = round(sep_swap * sqrt(tot), 1)
) %>% bind_cols(as_tibble(round(Fm, 3)))

write.csv(res %>% arrange(desc(score)), file.path(OUT, "design_matrix_full.csv"), row.names = FALSE)
saveRDS(list(M = M, Fm = Fm, tot = tot, types = PPK_TYPES, x0 = x0),
        file.path(OUT, "design_matrix.rds"))

cat("candidate targets with >=200 ppk-family synapses:",
    sum(tot >= 200), "of", nrow(M), "\n\n")
cat("=== top 25 by score (separation x sqrt signal), >=200 syn ===\n")
print(as.data.frame(res %>% filter(ppk_syn >= 200) %>% arrange(desc(score)) %>% head(25)))
