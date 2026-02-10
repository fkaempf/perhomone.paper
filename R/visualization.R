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

plot_modality_pair <- function(df, x_mod, y_mod, order_label = "3rd-order") {
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
      title = paste0(order_label, ": ", x_mod, " vs ", y_mod)
    ) +
    theme_bw()
}

#' Generate all pairwise modality comparison plots
#' @param df_wide Wide dataframe with modality columns
#' @param modality_cols Character vector of modality column names
#' @param order_label Label for the order (e.g., "3rd-order", "4th-order")
#' @return List of ggplot objects
generate_modality_comparisons <- function(df_wide, modality_cols, order_label = "3rd-order") {
  combos <- combn(modality_cols, 2, simplify = FALSE)
  lapply(combos, function(pair) {
    plot_modality_pair(df_wide, pair[1], pair[2], order_label)
  })
}

#' Create strength boxplot with statistical annotations
#' @param df Dataframe with path data
#' @param ann_df Annotation dataframe from compute_valence_annotations
#' @param title Plot title
#' @return ggplot object
plot_strength_boxplot <- function(df, ann_df, title = "") {
  ggplot(df, aes(x = dataset, y = strength, fill = valence)) +
    geom_boxplot() +
    facet_wrap(~valence) +
    stat_pvalue_manual(ann_df, label = "p", tip.length = 0) +
    labs(title = title, y = "Path Strength", x = "Target") +
    theme_bw() +
    theme(legend.position = "none")
}

#' Create hop count boxplot
#' @param df Dataframe with path data
#' @param title Plot title
#' @return ggplot object
plot_hops_boxplot <- function(df, title = "") {
  ggplot(df, aes(x = dataset, y = hops, fill = valence)) +
    geom_boxplot() +
    facet_wrap(~valence) +
    labs(title = title, y = "Number of Hops", x = "Target") +
    theme_bw() +
    theme(legend.position = "none")
}

#' Create radar/spider plot for modality strengths
#' @param df Dataframe with modality strength columns
#' @param neuron_col Column name for neuron identifiers
#' @param strength_cols Vector of column names for strengths (one per modality)
#' @param title Plot title
#' @param normalize If TRUE, normalize values to 0-1 range
#' @return ggplot object
make_radar_plot <- function(df, neuron_col = "end", strength_cols,
                            title = "Modality Strengths", normalize = TRUE) {
  # Prepare data for radar
  radar_df <- df %>%
    select(all_of(c(neuron_col, strength_cols))) %>%
    tidyr::pivot_longer(
      cols = all_of(strength_cols),
      names_to = "modality",
      values_to = "value"
    ) %>%
    mutate(modality = gsub("_strength$", "", modality))

  if (normalize) {
    radar_df <- radar_df %>%
      group_by(modality) %>%
      mutate(value = (value - min(value, na.rm = TRUE)) /
               (max(value, na.rm = TRUE) - min(value, na.rm = TRUE))) %>%
      ungroup()
  }

  # Create radar chart using coord_polar
  ggplot(radar_df, aes(x = modality, y = value, group = .data[[neuron_col]])) +
    geom_polygon(fill = NA, color = alpha("steelblue", 0.3)) +
    geom_point(size = 1, color = "steelblue", alpha = 0.3) +
    coord_polar() +
    labs(title = title) +
    theme_minimal() +
    theme(
      axis.text.x = element_text(size = 10, face = "bold"),
      axis.title = element_blank(),
      panel.grid.major = element_line(color = "grey80")
    )
}

#' Create radar plot for a single neuron
#' @param df Dataframe with modality strength columns
#' @param neuron_id Neuron identifier to plot
#' @param neuron_col Column name for neuron identifiers
#' @param strength_cols Vector of column names for strengths
#' @param rank_cols Optional vector of column names for ranks
#' @param title Plot title
#' @return ggplot object (or list of plots if rank_cols provided)
make_single_radar <- function(df, neuron_id, neuron_col = "end",
                              strength_cols, rank_cols = NULL, title = NULL) {
  neuron_data <- df %>% filter(.data[[neuron_col]] == neuron_id)

  if (nrow(neuron_data) == 0) {
    stop(sprintf("Neuron '%s' not found", neuron_id))
  }

  if (is.null(title)) title <- neuron_id

  # Strength radar
  strength_df <- neuron_data %>%
    select(all_of(strength_cols)) %>%
    tidyr::pivot_longer(
      cols = everything(),
      names_to = "modality",
      values_to = "value"
    ) %>%
    mutate(modality = gsub("_strength$", "", modality))

  p_strength <- ggplot(strength_df, aes(x = modality, y = value, group = 1)) +
    geom_polygon(fill = alpha("steelblue", 0.3), color = "steelblue") +
    geom_point(size = 3, color = "steelblue") +
    coord_polar() +
    labs(title = paste(title, "- Strength")) +
    theme_minimal() +
    theme(
      axis.text.x = element_text(size = 10, face = "bold"),
      axis.title = element_blank()
    )

  if (!is.null(rank_cols)) {
    # Rank radar (invert so lower rank = higher value on chart)
    rank_df <- neuron_data %>%
      select(all_of(rank_cols)) %>%
      tidyr::pivot_longer(
        cols = everything(),
        names_to = "modality",
        values_to = "value"
      ) %>%
      mutate(
        modality = gsub("_mod_rank$", "", modality),
        value = max(value, na.rm = TRUE) - value + 1  # Invert ranks
      )

    p_rank <- ggplot(rank_df, aes(x = modality, y = value, group = 1)) +
      geom_polygon(fill = alpha("darkred", 0.3), color = "darkred") +
      geom_point(size = 3, color = "darkred") +
      coord_polar() +
      labs(title = paste(title, "- Rank (inverted)")) +
      theme_minimal() +
      theme(
        axis.text.x = element_text(size = 10, face = "bold"),
        axis.title = element_blank()
      )

    return(list(strength = p_strength, rank = p_rank))
  }

  p_strength
}

#' Create heatmap of modality strengths across neurons
#' @param df Dataframe with modality strength columns
#' @param neuron_col Column name for neuron identifiers
#' @param strength_cols Vector of column names for strengths
#' @param top_n Number of top neurons to show (by total strength)
#' @param title Plot title
#' @return ggplot object
make_strength_heatmap <- function(df, neuron_col = "end", strength_cols,
                                  top_n = 30, title = "Modality Strength Heatmap") {
  # Calculate total strength and get top neurons
  df_top <- df %>%
    mutate(total = rowSums(across(all_of(strength_cols)), na.rm = TRUE)) %>%
    slice_max(total, n = top_n)

  # Pivot to long format
  heatmap_df <- df_top %>%
    select(all_of(c(neuron_col, strength_cols))) %>%
    tidyr::pivot_longer(
      cols = all_of(strength_cols),
      names_to = "modality",
      values_to = "strength"
    ) %>%
    mutate(modality = gsub("_strength$", "", modality))

  # Normalize within each modality for better visualization
  heatmap_df <- heatmap_df %>%
    group_by(modality) %>%
    mutate(strength_norm = strength / max(strength, na.rm = TRUE)) %>%
    ungroup()

  ggplot(heatmap_df, aes(x = modality, y = reorder(.data[[neuron_col]], strength_norm),
                         fill = strength_norm)) +
    geom_tile() +
    scale_fill_viridis_c(option = "plasma", name = "Normalized\nStrength") +
    labs(title = title, x = "Modality", y = "Neuron Type") +
    theme_minimal() +
    theme(
      axis.text.y = element_text(size = 7),
      axis.text.x = element_text(angle = 45, hjust = 1)
    )
}
