# Fetch every input synapse on the target bodies of the selected case (see _paths.R).
# Cached, so rerunning is free.

suppressMessages({
  library(neuprintr); library(malecns); library(nat)
  library(arrow); library(dplyr)
})
options(rgl.useNULL = TRUE)   # rgl cannot init headless on this machine

source("/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R")
neuprint_login(server = MCNS_SERVER, dataset = MCNS_DATASET)

mba <- read_feather(file.path(PAPER, "feather", "mba.feather"))

targets <- mba %>%
  filter(type %in% TARGET_TYPES) %>%
  select(bodyid, type, soma_side) %>%
  arrange(type, bodyid)

cat("--- target bodies ---\n"); print(as.data.frame(targets))
stopifnot(nrow(targets) > 0)

ids <- targets$bodyid

cache <- SYN_RAW
if (file.exists(cache)) {
  syn <- read_feather(cache)
  cat("\nread from cache:", cache, "\n")
} else {
  syn_list <- lapply(seq_along(ids), function(i) {
    cat(sprintf("fetching %d/%d: %s\n", i, length(ids), ids[i]))
    s <- neuprint_get_synapses(ids[i], dataset = MCNS_DATASET)
    s[s$prepost == 1, , drop = FALSE]        # prepost == 1 -> this body is POST
  })
  syn <- bind_rows(syn_list)
  write_feather(syn, cache)
  cat("\nwrote:", cache, "\n")
}

cat("\ninput synapses:", nrow(syn), "across", n_distinct(syn$bodyid), "bodies\n")
print(syn %>% count(bodyid, name = "input_syn") %>%
        left_join(targets, by = "bodyid") %>%
        select(type, bodyid, soma_side, input_syn) %>% as.data.frame())
cat("\ncoordinate range (8 nm voxels)\n")
cat("  x:", range(syn$x), "\n  y:", range(syn$y), "\n  z:", range(syn$z), "\n")
