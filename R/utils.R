# Utility Functions for Path Analysis
# Contains helper functions used across the analysis

#' Check if file exists; if not, signal to execute code
#' @param path File path to check
#' @return TRUE if file doesn't exist (execute), FALSE if it exists (load)
load_or_execute <- function(path) {
  if (file.exists(path)) {
    file.exists(path)
    FALSE
  } else {
    TRUE
  }
}

#' Column-normalize a matrix
#' @param A Matrix to normalize
#' @param na.rm Remove NA values
#' @return Column-normalized matrix
colScale <- function(A, na.rm = TRUE) {
  scalefac <- 1 / Matrix::colSums(A)
  if (na.rm) scalefac[!is.finite(scalefac)] <- 0
  A %*% Matrix::Diagonal(x = scalefac)
}

#' Row-normalize a matrix
#' @param A Matrix to normalize
#' @param na.rm Remove NA values
#' @return Row-normalized matrix
rowScale <- function(A, na.rm = TRUE) {
  scalefac <- 1 / Matrix::rowSums(A)
  if (na.rm) scalefac[!is.finite(scalefac)] <- 0
  Matrix::Diagonal(x = scalefac) %*% A
}

#' Add column prefix to dataframe
#' @param df Dataframe
#' @param prefix Prefix to add
#' @return Dataframe with prefixed column names
prefix_cols <- function(df, prefix) {
  names(df) <- paste0(prefix, "_", names(df))
  df
}

#' Make color gradient
#' @param col1 First color
#' @param col2 Second color
#' @param n Number of colors
#' @return Vector of colors
make_gradient <- function(col1, col2, n) {
  colorRampPalette(c(col1, col2))(n)
}

#' Get body IDs for a type string
#' @param type_string Type string to search for
#' @param mba Body annotations dataframe (uses global if not provided)
#' @return Vector of body IDs
get.body.ids <- function(type_string, mba = NULL) {
  if (is.null(mba)) mba <- get("mba", envir = .GlobalEnv)
  mba %>%
    filter(grepl(type_string, type, ignore.case = TRUE)) %>%
    pull(bodyid) %>%
    unique()
}

#' Save plot in both PNG and PDF formats
#' @param plot ggplot object
#' @param base_path Path without extension
#' @param width Width in cm (default 18)
#' @param height Height in cm (default 12)
#' @param dpi DPI for PNG (default 300)
save_plot_formats <- function(plot, base_path, width = 18, height = 12, dpi = 300) {
  ggsave(paste0(base_path, ".png"), plot = plot,
         width = width, height = height, units = "cm", dpi = dpi)
  ggsave(paste0(base_path, ".pdf"), plot = plot,
         width = width, height = height, units = "cm", dpi = dpi)
}

#' Compute statistical annotations for valence-split boxplots
#' @param df Dataframe with 'strength', 'dataset', and 'valence' columns
#' @param y_multiplier Multiplier for y.position (default 1.12)
#' @return Dataframe with statistical annotations
compute_valence_annotations <- function(df, y_multiplier = 1.12) {
  df %>%
    group_by(valence) %>%
    summarise(
      group1 = "PPN1",
      group2 = "vAB3",
      p = tryCatch(
        unname(t.test(log(strength) ~ dataset)$p.value),
        error = function(e) NA_real_
      ),
      y.position = max(strength, na.rm = TRUE) * y_multiplier,
      .groups = "drop"
    )
}

#' Get strongest path combinations per start-end-valence
#' @param df Dataframe with path data
#' @return Dataframe with strongest path per combination
get_strongest_combinations <- function(df) {
  df %>%
    group_by(start, end, valence) %>%
    slice_max(strength, n = 1, with_ties = FALSE) %>%
    ungroup() %>%
    arrange(desc(strength))
}

#' Compute average edge weight across a path
#' @param path_str Path string (e.g., "A -> B -> C")
#' @param adj Adjacency matrix
#' @return Average edge weight
avg_path <- function(path_str, adj) {
  nodes <- strsplit(path_str, " -> ", fixed = TRUE)[[1]]
  if (length(nodes) < 2) return(NA_real_)

  edges <- vapply(seq_len(length(nodes) - 1), function(i) {
    pre <- nodes[i]
    post <- nodes[i + 1]
    if (pre %in% rownames(adj) && post %in% colnames(adj)) {
      adj[pre, post]
    } else {
      NA_real_
    }
  }, numeric(1))

  mean(edges, na.rm = TRUE)
}
