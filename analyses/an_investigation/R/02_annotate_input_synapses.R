# Attach the presynaptic partner's type to every input synapse, and collapse the
# local nerve-suffix variants onto the four bare focus names.

suppressMessages({
  library(arrow); library(dplyr)
})

source("/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R")

mba <- read_feather(file.path(PAPER, "feather", "mba.feather"))
syn <- read_feather(SYN_RAW)

syn <- syn %>%
  left_join(mba %>% select(bodyid, type, class, superclass) %>%
              rename(partner_type       = type,
                     partner_class      = class,
                     partner_superclass = superclass),
            by = c("partner" = "bodyid")) %>%
  left_join(mba %>% select(bodyid, type, soma_side) %>%
              rename(target_type = type),
            by = "bodyid") %>%
  mutate(partner_group = bare_type(partner_type),
         is_focus      = partner_group %in% FOCUS)

# Guard against the silent-empty failure mode: if the collapse ever stops
# matching, fail loudly here rather than producing an empty scene later.
n_focus <- sum(syn$is_focus, na.rm = TRUE)
if (n_focus == 0) {
  stop("no synapse matched FOCUS after bare_type() - check the suffix regex in _paths.R")
}

cat("--- focus synapses per target type ---\n")
tab <- syn %>%
  filter(is_focus) %>%
  count(target_type, partner_group) %>%
  tidyr::pivot_wider(names_from = partner_group, values_from = n, values_fill = 0)
print(as.data.frame(tab))

cat("\n--- focus share of all input, per body ---\n")
print(syn %>%
        group_by(target_type, bodyid, soma_side) %>%
        summarise(input_syn = n(), focus_syn = sum(is_focus, na.rm = TRUE),
                  pct_focus = round(100 * focus_syn / input_syn, 1),
                  .groups = "drop") %>%
        as.data.frame())

cat("\n--- suffix variants actually seen (collapsed away) ---\n")
print(syn %>% filter(is_focus) %>% count(partner_group, partner_type) %>% as.data.frame())

cat("\n--- top non-focus inputs ---\n")
print(syn %>% filter(!is_focus) %>% count(target_type, partner_type, sort = TRUE) %>%
        group_by(target_type) %>% slice_head(n = 8) %>% as.data.frame())

out <- SYN_ANN
write_feather(syn, out)
cat("\nwrote:", out, "\n")
