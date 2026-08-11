# Fetch the RAW per-bodyid-pair edge list from the ppk-family sensory types to all
# downstream partners, for both male-cns:v1.0 and male-cns:v1.0.
#
# Everything downstream (threshold sweep, version comparison) is derived from these
# two objects, so the fetch happens exactly once and the sweep is guaranteed to be
# like-for-like across thresholds and versions.
#
# NOTE ON "THRESHOLD 0": neuprint stores no zero-weight edges. The smallest possible
# fetch is threshold = 1 (>= 1 synapse). Threshold 0 and threshold 1 are therefore the
# same population by construction; we fetch at 1 and report 0 == 1.

suppressMessages({library(neuprintr); library(dplyr); library(tibble)})
Sys.setenv(neuprint_token = Sys.getenv("NEUPRINT_TOKEN"))

OUT <- "/Users/fkampf/Documents/pheromone.paper/receptor_typing_validation/data"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)

PPK_TYPES <- c("WG3","WG4","LgLG1a","LgLG1b","LgLG5","LgLG6","LgLG7","LgLG8")

fetch_one <- function(DS) {
  message("\n########## ", DS, " ##########")
  neuprint_login(server = "https://neuprint-cns.janelia.org", dataset = DS)

  # sensory bodyids per type (exact type match, as in 05_design_matrix_v1.R)
  ids <- lapply(PPK_TYPES, function(t) {
    m <- neuprint_search(sprintf("^%s$", t), field = "type", dataset = DS,
                         all_segments = FALSE)
    if (is.null(m) || !nrow(m)) return(NULL)
    tibble(pre_type = t, pre_id = m$bodyid)
  }) %>% bind_rows()
  message(sprintf("sensory neurons: %d across %d types", nrow(ids), n_distinct(ids$pre_type)))
  print(ids %>% count(pre_type), n = 20)

  # RAW downstream edges, threshold = 1 (minimum possible)
  ct <- neuprint_connection_table(ids$pre_id, prepost = "POST", dataset = DS,
                                  threshold = 1L, details = FALSE, progress = TRUE)
  message("raw edges: ", nrow(ct), "  weight range: ",
          min(ct$weight), "-", max(ct$weight))

  post_meta <- neuprint_get_meta(unique(ct$partner), dataset = DS)

  edges <- ct %>%
    as_tibble() %>%
    select(pre_id = bodyid, post_id = partner, weight) %>%
    left_join(ids, by = "pre_id") %>%
    left_join(post_meta %>% select(bodyid, post_type = type),
              by = c("post_id" = "bodyid"))

  message("edges with a typed postsynaptic partner: ",
          sum(!is.na(edges$post_type) & edges$post_type != ""), " / ", nrow(edges))
  edges
}

e10 <- fetch_one("male-cns:v1.0")
saveRDS(e10, file.path(OUT, "raw_edges_v1.0.rds"))

e09 <- fetch_one("male-cns:v1.0")
saveRDS(e09, file.path(OUT, "raw_edges_v0.9.rds"))

cat("\nDONE. saved raw_edges_v1.0.rds and raw_edges_v0.9.rds\n")
