# Visualization Functions
# Functions for creating plots and charts
pie_data <- function(df, dataset_name, valence_keep = NULL) {
df %>%
  filter(dataset == dataset_name) %>%
  {
    if (!is.null(valence_keep)) filter(., valence %in% valence_keep) else .
  } %>%
  group_by(end, modality) %>%
  summarise(total_strength = sum(strength, na.rm = TRUE), .groups = "drop_last") %>%
  ungroup() %>%
  group_by(end) %>% 
  mutate(prop = total_strength / sum(total_strength)) %>%
  filter(is.finite(prop)) # drop ends with all-zero strength
}

pie_plot <- function(pdat, title_txt) {
ggplot(pdat, aes(x = "", y = prop, fill = modality)) +
  geom_col(width = 1, color = "white") +
  coord_polar(theta = "y") +
  facet_wrap(~end) +
  theme_void() +
  labs(title = title_txt) +
  geom_text(aes(label = percent(prop, accuracy = 1)),
    position = position_stack(vjust = 0.5), size = 2
  )
}

# PPN1
ppn1_all <- pie_data(all.modalities.excluded, "PPN1", NULL)
ppn1_exc <- pie_data(all.modalities.excluded, "PPN1", c("excitatory", 1)) # handles either text or numeric
ppn1_inh <- pie_data(all.modalities.excluded, "PPN1", c("inhibitory", -1))

p_ppn1_all <- pie_plot(ppn1_all, "PPN1: modality contribution per target neuron (all)")
p_ppn1_exc <- pie_plot(ppn1_exc, "PPN1: modality contribution per target neuron (excitatory only)")
p_ppn1_inh <- pie_plot(ppn1_inh, "PPN1: modality contribution per target neuron (inhibitory only)")

p_ppn1_all
p_ppn1_exc
p_ppn1_inh

ggsave(file.path(plot.path.png, "pie.plot.modality.contribution.to.post.PPN1.excluded.all.paths.png"), plot = p_ppn1_all, width = 18, height = 12, units = "cm", dpi = 300)
ggsave(file.path(plot.path.pdf, "pie.plot.modality.contribution.to.post.PPN1.excluded.all.paths.pdf"), plot = p_ppn1_all, width = 18, height = 12, units = "cm", dpi = 300)

ggsave(file.path(plot.path.png, "pie.plot.modality.contribution.to.post.PPN1.excluded.excitatory.paths.png"), plot = p_ppn1_exc, width = 18, height = 12, units = "cm", dpi = 300)
ggsave(file.path(plot.path.pdf, "pie.plot.modality.contribution.to.post.PPN1.excluded.excitatory.paths.pdf"), plot = p_ppn1_exc, width = 18, height = 12, units = "cm", dpi = 300)

ggsave(file.path(plot.path.png, "pie.plot.modality.contribution.to.post.PPN1.excluded.inhibitory.paths.png"), plot = p_ppn1_inh, width = 18, height = 12, units = "cm", dpi = 300)
ggsave(file.path(plot.path.pdf, "pie.plot.modality.contribution.to.post.PPN1.excluded.inhibitory.paths.png"), plot = p_ppn1_inh, width = 18, height = 12, units = "cm", dpi = 300)


ppn1_all$connection.type <- "all"
ppn1_exc$connection.type <- "excitatory"
ppn1_inh$connection.type <- "inhibitory"

connected.scatterplot.all.ppn1 <- rbind(ppn1_all, ppn1_exc, ppn1_inh) %>%
mutate(
  x_pos = as.numeric(factor(end, levels = unique(end))),
  x_shift = case_when(
    connection.type == "inhibitory" ~ -0.2,
    connection.type == "all" ~ 0,
    connection.type == "excitatory" ~ 0.2
  ),
  x_jittered = x_pos + x_shift
)

p <- ggplot(connected.scatterplot.all.ppn1, aes(x = x_jittered, y = prop, group = interaction(end, modality), color = modality)) +
geom_line(alpha = 0.6, linewidth = 0.8) + # line inherits modality color
geom_point(aes(shape = connection.type), size = 3, alpha = 0.9) +
scale_x_continuous(
  breaks = unique(connected.scatterplot.all.ppn1$x_pos),
  labels = unique(connected.scatterplot.all.ppn1$end)
) +
theme_bw() +
labs(
  title = "Fraction of input (excluding PPN1) to post PPN1 (all) by connection type",
  x = "Target neurons",
  y = "Proportion",
  color = "Modality",
  shape = "Connection type"
) +
theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
theme(axis.text.x = element_text(
  angle = 90, hjust = 1,
  color = ifelse(unique(connected.scatterplot.all.ppn1$end) %in% intersect(target.vAB3.all, target.PPN1.all), "red", "black")
))
p
ggsave(file.path(plot.path.png, "fraction.input.to.post.PPN1.excluded.by.valence.and.modality.png"), plot = p, width = 25, height = 16, units = "cm", dpi = 300)
clean_legend_names <- function(p) {
  p$x$data <- lapply(
    p$x$data,
    function(tr) {
      if (!is.null(tr$name) && grepl("^\\(", tr$name)) {
        # "(PPN1,1,NA)" -> "PPN1"
        tr$name <- sub("^\\(([^,]+),.*", "\\1", tr$name)
      }
      tr
    }
  )
  p
}

## -----------------------------
## 5) interactive plot (modality)
## -----------------------------

gg <- ggplot(tsne_df, aes(x = tSNE1, y = tSNE2)) +
  geom_point(
    aes(
      color = modality,
      text  = paste0(
        "node: ", node, "<br>",
        "modality: ", modality, "<br>",
        "cluster: ", cluster_id, "<br>",
        "eval sets: ", eval_flag, "<br>",
        "#datasets: ", n_datasets, "<br>",
        "datasets: ", datasets_all
      )
    ),
    size = 1,
    alpha = 0.8
  ) +
  scale_color_manual(
    values = c(
      DA1   = "red",
      VA1v  = "orange",
      aud   = "blue",
      vis   = "green4",
      ppk23 = "purple",
      ppk25 = "brown",
      other = "grey70"
    )
  ) +
plot_modality_pair <- function(df, x_mod, y_mod) {
  df <- df %>% mutate(show_label = (.data[[x_mod]] != 0 & .data[[y_mod]] != 0))

  ggplot(df, aes(
    x = .data[[x_mod]],
    y = .data[[y_mod]],
    color = is_inh
  )) +
    geom_abline(slope = 1, intercept = 0, linetype = 2, linewidth = 0.4) +
    geom_point(alpha = 0.7) +
    geom_text(
      data = subset(df, show_label),
      aes(label = neuron),
      hjust = 0,
      vjust = 1,
      size = 2.5
    ) +
    scale_color_manual(
      values = c(`FALSE` = "grey60", `TRUE` = "red"),
      labels = c(`FALSE` = "exc/unknown", `TRUE` = "inhibitory"),
      name   = "NT class"
    ) +
    labs(
      x = x_mod,
      y = y_mod,
      title = paste0("3rd-order: ", x_mod, " vs ", y_mod)
    ) +
    theme_bw()
}


## ------------------------------------------------------------
## 5. Generate all pairwise modality scatterplots
## ------------------------------------------------------------

plots <- combn(mods, 2, simplify = FALSE) %>%
  set_names(purrr::map_chr(., ~ paste(.x, collapse = "_vs_"))) %>%
  purrr::map(~ plot_modality_pair(df_wide, .x[1], .x[2]))

# Example to print one:
# print(plots[["DA1_vs_VA1v"]])
plots

```

```{r}
library(dplyr)
library(purrr)
library(tibble)
library(tidyr)
library(ggplot2)

## ------------------------------------------------------------
## 1. Compute modality-wise metrics per 4th-order neuron
##    (every 4th neuron along each path)
## ------------------------------------------------------------

modalities <- list(
  DA1        = start.types.DA1,
  VA1v       = start.types.VA1v,
  ppk23.pro  = start.types.ppk23.pro,
  ppk25.pro  = start.types.ppk25.pro
)

modality_df_4th <- imap_dfr(modalities, \(starts, mod_name) {
  # split paths for this modality
  split_paths <- combined %>%
    filter(start %in% starts) %>%
    pull(path) %>%
    strsplit(" -> ")

  # all unique neurons in these paths
  all_unique <- unique(unlist(split_paths))

  # every 4th neuron in each path (then unique), safely
  order4_neurons <- unique(unlist(
    lapply(split_paths, \(p) {
      if (length(p) >= 4) {
        p[seq(4, length(p), 4)]
      } else {
        character(0)
      }
    })
  ))

  tibble(
    modality = mod_name,
    neuron   = order4_neurons,

    total_in_from_others = map_dbl(
      order4_neurons,
      \(n) {
        from <- setdiff(all_unique, n)
        valid_from <- intersect(from, rownames(adj.matrix))

        if (!n %in% colnames(adj.matrix) || length(valid_from) == 0) {
          return(NA_real_)
        }

