# Path Analysis Functions
# Functions for finding and analyzing neural paths

#' Add valence flag to paths based on neurotransmitter
#' @param df Dataframe with paths
#' @param nt_by_type Named vector of neurotransmitters by type
#' @param is_inhib_by_nt Named logical vector of inhibitory status by NT
#' @return Dataframe with valence information
add_valence_flag <- function(df, nt_by_type, is_inhib_by_nt) {
  df %>%
    rowwise() %>%
    mutate(
      # split path and drop endpoint
      nodes = list(setdiff(strsplit(path, " -> ", fixed = TRUE)[[1]], end)),
      # lookup NTs
      nts = list(unname(nt_by_type[unlist(nodes)])),
      # lookup inhibitory flags
      inhib = list(unname(is_inhib_by_nt[unlist(nts)])),
      # count inhibitors
      n_inhib = sum(unlist(inhib), na.rm = TRUE),
      # convert to +1 / -1
      d = ifelse(n_inhib %% 2 == 0, 1, -1)
    ) %>%
    ungroup()
}
find_k_strongest_paths <- function(
g,
starts,
targets,
mba,
n_paths = 3,
diversity = c("otheredges", "othernodes", "none"),
ignore_pattern = NULL # grepl() pattern; matched node names are excluded (start/target kept),
) {
type2nt <- mba %>%
  select(type, consensus_nt) %>%
  group_by(type) %>%
  distinct() %>%
  rename(nt = consensus_nt)
nt_by_type <- setNames(type2nt$nt, type2nt$type)
inhibitory_nts <- c("gaba", "glycine", "histamine")
all_nts <- unique(type2nt$nt)
is_inhib_by_nt <- setNames(all_nts %in% inhibitory_nts, all_nts)

diversity <- match.arg(diversity)

# optional: drop nodes matching ignore_pattern (but never drop starts/targets)
if (!is.null(ignore_pattern)) {
  drop <- V(g)$name[grepl(ignore_pattern, V(g)$name)]
  keep <- unique(c(starts, targets))
  drop <- setdiff(drop, keep)
  if (length(drop)) g <- igraph::delete_vertices(g, drop)
}

# weights → log-costs; guard zeros/NAs
w <- E(g)$weight
if (is.null(w)) stop("Edges must have numeric 'weight'.")
w[!is.finite(w) | w <= 0] <- .Machine$double.eps
log_w <- -log(w)

results <- list()
all_nodes <- character(0)

for (s in starts) {
  for (t in targets) {
    if (!(s %in% V(g)$name) || !(t %in% V(g)$name)) {
      results[[paste(s, t, sep = "->")]] <- list(list(
        start = s, end = t, path = NA_character_, strength = NA_real_, hops = NA_integer_
      ))
      next
    }

    g_tmp <- g
    E(g_tmp)$log_weight <- log_w
    pair_paths <- list()

    for (i in seq_len(n_paths)) {
      sp <- igraph::shortest_paths(
        g_tmp,
        from = s, to = t,
        weights = E(g_tmp)$log_weight,
        output = "both"
      )
      if (length(sp$vpath[[1]]) == 0) break

      vpath <- sp$vpath[[1]]
      epath <- sp$epath[[1]]

      final_strength <- exp(-sum(E(g_tmp)[epath]$log_weight))
      hops <- length(epath)

      pair_paths[[paste0("path", i)]] <- list(
        start = s,
        end = t,
        path = paste(V(g)[vpath]$name, collapse = " -> "),
        strength = final_strength,
        hops = hops
      )

      all_nodes <- c(all_nodes, V(g)[vpath]$name)

      if (diversity == "othernodes") {
        inter <- setdiff(V(g)[vpath]$name, c(s, t))
        if (length(inter)) g_tmp <- igraph::delete_vertices(g_tmp, inter)
      } else if (diversity == "otheredges") {
        g_tmp <- igraph::delete_edges(g_tmp, epath)
      }
    }

    if (length(pair_paths) == 0) {
      pair_paths <- list(list(
        start = s, end = t, path = NA_character_, strength = NA_real_, hops = NA_integer_
      ))
    }

    results[[paste(s, t, sep = "->")]] <- pair_paths
  }
}

# flatten
results_df <- do.call(rbind, lapply(results, function(pl) {
  do.call(rbind, lapply(pl, function(r) {
    data.frame(
      start = r$start, end = r$end, path = r$path,
      strength = r$strength, hops = r$hops,
      stringsAsFactors = FALSE
    )
  }))
}))

results_df_wo_na <- dplyr::filter(results_df, !is.na(strength))
all_nodes <- unique(all_nodes)

results_df_wo_na <- add_valence_flag(results_df_wo_na, nt_by_type, is_inhib_by_nt) %>%
  mutate(valence = ifelse(d == 1L, "excitatory", "inhibitory"))

list(df = results_df_wo_na, nodes = all_nodes, raw = results)
}
find_k_strongest_paths_yen <- function(
g,
starts,
targets,
mba,
n_paths = 3,
diversity = c("otheredges", "othernodes", "none"),
ignore_pattern = NULL # grepl() pattern; matched node names are excluded (start/target kept),
) {
for (ip in ignore_pattern){
g <- delete_vertices(g, V(g)[grepl(ip, name)])
}
type2nt <- mba %>%
  select(type, consensus_nt) %>%
  group_by(type) %>%
  distinct() %>%
  rename(nt = consensus_nt)
nt_by_type <- setNames(type2nt$nt, type2nt$type)
inhibitory_nts <- c("gaba", "glycine", "histamine")
all_nts <- unique(type2nt$nt)
is_inhib_by_nt <- setNames(all_nts %in% inhibitory_nts, all_nts)


# weights → log-costs; guard zeros/NAs
w <- E(g)$weight
if (is.null(w)) stop("Edges must have numeric 'weight'.")
w[!is.finite(w) | w <= 0] <- .Machine$double.eps
log_w <- -log(w)

results <- list()
all_nodes <- character(0)

for (s in starts) {
  for (t in targets) {
    pair_paths <- list()
    temp.k.shortest.paths = k_shortest_paths(g,from = s, to = t,weights = E(g)$log_weight,k=n_paths)


    # cache once
    vnames <- V(g)$name
    w      <- E(g)$weight
    logw   <- E(g)$log_weight
    
    paths_e <- temp.k.shortest.paths$epaths
    paths_v <- temp.k.shortest.paths$vpaths
    n_k     <- length(paths_e)
    
    if (n_k == 0L) {
      pair_paths <- list(list(start = s, end = t, path = NA_character_, strength = NA_real_, hops = NA_integer_))
    } else {
      # strengths: prefer log-weights if present (faster + stable)
      if (!is.null(logw)) {
        strengths <- exp(-vapply(paths_e, function(idx) sum(logw[idx]), numeric(1)))
      } else {
        strengths <- vapply(paths_e, function(idx) prod(w[idx]), numeric(1))
      }
    
      hops      <- lengths(paths_e)
      path_str  <- vapply(paths_v, function(idx) paste(vnames[idx], collapse = " -> "), character(1))
    
      # build list-of-lists without a for-loop
      pair_paths <- lapply(seq_len(n_k), function(i) {
        list(
          start    = s,
          end      = t,
          path     = path_str[i],
          strength = strengths[i],
          hops     = hops[i]
        )
      })
      names(pair_paths) <- paste0("path", seq_len(n_k))
    }
    
    # collect nodes once, not in the loop
    all_nodes <- c(all_nodes, vnames[unique(unlist(paths_v, use.names = FALSE))])

    if (length(pair_paths) == 0) {
      pair_paths <- list(list(
        start = s, end = t, path = NA_character_, strength = NA_real_, hops = NA_integer_
      ))
    }

    results[[paste(s, t, sep = "->")]] <- pair_paths
  }
}

# flatten
results_df <- do.call(rbind, lapply(results, function(pl) {
  do.call(rbind, lapply(pl, function(r) {
    data.frame(
      start = r$start, end = r$end, path = r$path,
      strength = r$strength, hops = r$hops,
      stringsAsFactors = FALSE
    )
  }))
}))

results_df_wo_na <- dplyr::filter(results_df, !is.na(strength))
all_nodes <- unique(all_nodes)

results_df_wo_na <- add_valence_flag(results_df_wo_na, nt_by_type, is_inhib_by_nt) %>%
  mutate(valence = ifelse(d == 1L, "excitatory", "inhibitory"))

list(df = results_df_wo_na, nodes = all_nodes, raw = results)
}
summarise_paths_all <- function(df,
                                adj.matrix,
                                adj.matrix.pre,
                                adj.matrix.raw,
                                min_frac = 0.001) {
  # df must have columns: "path" ("A -> B -> C") and "dataset"
  
  # ---------- expand path into node_0, node_1, ... ----------
  nodes_list <- strsplit(df$path, " -> ", fixed = TRUE)
  max_nodes  <- max(lengths(nodes_list))
  n_rows     <- nrow(df)
  
  for (i in 0:(max_nodes - 1L)) {
    df[[paste0("node_", i)]] <-
      vapply(
        nodes_list,
        function(x) if (length(x) >= i + 1L) x[[i + 1L]] else NA_character_,
        character(1)
      )
  }
  
  # ---------- node → datasets mapping ----------
  # per node: list in which input datasets it appears
  node_datasets <- df %>%
    tidyr::pivot_longer(
      cols = dplyr::starts_with("node_"),
      names_to  = "pos",
      values_to = "node"
    ) %>%
    dplyr::filter(!is.na(node)) %>%
    dplyr::group_by(node) %>%
    dplyr::summarise(
      datasets = paste(sort(unique(dataset)), collapse = ";"),
      .groups  = "drop"
    )
  
  # ---------- helper: synapse value lookup ----------
  get_syn_value <- function(pre, post, adj.matrix) {
    if (is.na(pre) || is.na(post)) return(NA_real_)
    
    cell <- adj.matrix[pre, post][[1]]
    if (is.null(cell) || length(cell) == 0) return(NA_real_)
    
    if (is.numeric(cell) && length(cell) == 1L)
      return(as.numeric(cell))
    
    fields <- grep("^synapse\\.strength\\.post\\.normed\\.",
                   names(cell), value = TRUE)
    if (length(fields) == 0) return(NA_real_)
    
    sum(unlist(cell[fields]), na.rm = TRUE)
  }
  
  # ---------- helper: add syn columns for a given matrix ----------
  add_syn_cols <- function(df, nodes_list, max_nodes, adj, prefix) {
    for (i in 0:(max_nodes - 2L)) {
      syn_col <- paste0(prefix, "_pos", i)
      df[[syn_col]] <-
        vapply(
          seq_len(nrow(df)),
          function(r) {
            nodes <- nodes_list[[r]]
            if (length(nodes) < i + 2L) return(NA_real_)
            
            pre  <- nodes[[i + 1L]]
            post <- nodes[[i + 2L]]
            
            get_syn_value(pre, post, adj)
          },
          numeric(1)
        )
    }
    df
  }
  
  # add syn.post.normed_pos*, syn.pre.normed_pos*, syn.raw_pos*
  df <- add_syn_cols(df, nodes_list, max_nodes, adj.matrix,     "syn.post.normed")
  df <- add_syn_cols(df, nodes_list, max_nodes, adj.matrix.pre, "syn.pre.normed")
  df <- add_syn_cols(df, nodes_list, max_nodes, adj.matrix.raw, "syn.raw")
  
  # ---------- helper: summarise for one matrix ----------
  summarise_strength_by_matrix <- function(df, syn_prefix, tag) {
    pattern_base <- gsub("\\.", "\\\\.", syn_prefix)  # escape dots
    syn_col_name <- syn_prefix
    
    # normalise syn column names: syn.xxx_pos0 -> syn.xxx_0
    syn_cols_pos <- grep(paste0("^", pattern_base, "_pos\\d+"),
                         names(df), value = TRUE)
    
    df_tmp <- df
    for (nm in syn_cols_pos) {
      pos_id  <- sub(paste0("^", pattern_base, "_pos"), "", nm)  # "0","1",...
      new_nm  <- paste0(syn_prefix, "_", pos_id)                 # syn.xxx_0
      names(df_tmp)[names(df_tmp) == nm] <- new_nm
    }
    
    # long: (row, pos) with node and strength
    df_long <- df_tmp %>%
      dplyr::mutate(row_id = dplyr::row_number()) %>%
      tidyr::pivot_longer(
        cols = tidyselect::matches(paste0("^node_\\d+|^", pattern_base, "_\\d+")),
        names_to      = c(".value", "pos"),
        names_pattern = paste0("(node|", pattern_base, ")_(\\d+)")
      ) %>%
      dplyr::mutate(pos = as.integer(pos))
    
    # per node + position
    node_pos <- df_long %>%
      dplyr::filter(!is.na(node)) %>%
      dplyr::group_by(node, pos) %>%
      dplyr::summarise(
        count        = dplyr::n(),
        strength_sum = sum(.data[[syn_col_name]], na.rm = TRUE),
        .groups = "drop"
      )
    
    # wide: one row per node
    summary_mat <- node_pos %>%
      tidyr::pivot_wider(
        names_from  = pos,
        values_from = c(count, strength_sum),
        names_glue  = "{.value}_pos{pos}"
      )
    
    # rename strength_sum_posX -> strength_sum_<tag>_posX
    strength_cols_old <- grep("^strength_sum_pos", names(summary_mat), value = TRUE)
    for (nm in strength_cols_old) {
      pos_id <- sub("^strength_sum_pos", "", nm)
      new_nm <- paste0("strength_sum_", tag, "_pos", pos_id)
      names(summary_mat)[names(summary_mat) == nm] <- new_nm
    }
    
    # totals + overall average
    count_cols <- grep("^count_pos", names(summary_mat), value = TRUE)
    summary_mat[[paste0("count_total_", tag)]] <- rowSums(
      summary_mat[, count_cols, drop = FALSE],
      na.rm = TRUE
    )
    
    strength_cols <- grep(
      paste0("^strength_sum_", tag, "_pos"),
      names(summary_mat),
      value = TRUE
    )
    
    total_sum_name <- paste0("strength_sum_", tag, "_total")
    total_avg_name <- paste0("strength_avg_", tag, "_total")
    
    summary_mat[[total_sum_name]] <- rowSums(
      summary_mat[, strength_cols, drop = FALSE],
      na.rm = TRUE
    )
    
    summary_mat[[total_avg_name]] <- ifelse(
      summary_mat[[paste0("count_total_", tag)]] == 0,
      NA_real_,
      summary_mat[[total_sum_name]] / summary_mat[[paste0("count_total_", tag)]]
    )
    
    # per-position averages: strength_avg_<tag>_posX
    for (cnt_nm in count_cols) {
      pos_id <- sub("^count_pos", "", cnt_nm)
      sum_nm <- paste0("strength_sum_", tag, "_pos", pos_id)
      avg_nm <- paste0("strength_avg_", tag, "_pos", pos_id)
      
      if (sum_nm %in% names(summary_mat)) {
        summary_mat[[avg_nm]] <- ifelse(
          summary_mat[[cnt_nm]] > 0,
          summary_mat[[sum_nm]] / summary_mat[[cnt_nm]],
          NA_real_
        )
      }
    }
    
    summary_mat %>%
      dplyr::select(dplyr::all_of(sort(names(.))))
  }
  
  # ---------- summaries per adjacency type ----------
  summary_post <- summarise_strength_by_matrix(df, "syn.post.normed", "post")
  summary_pre  <- summarise_strength_by_matrix(df, "syn.pre.normed",  "pre")
  summary_raw  <- summarise_strength_by_matrix(df, "syn.raw",         "raw")
  
  # ---------- join + global filtering + dataset tag ----------
  summary_all <- summary_post %>%
    dplyr::full_join(summary_pre,  by = "node") %>%
    dplyr::full_join(summary_raw, by = "node") %>%
    # attach dataset info per node
    dplyr::left_join(node_datasets, by = "node")
  
  # global count across all positions and matrices
  all_count_cols <- grep("^count_pos|^count_total_", names(summary_all), value = TRUE)
  summary_all$count_total_global <- rowSums(
    summary_all[, all_count_cols, drop = FALSE],
    na.rm = TRUE
  )
  
  summary_all$count_total_frac <- summary_all$count_total_global / n_rows
  
  summary_all <- summary_all %>%
    dplyr::filter(count_total_frac >= min_frac) %>%
    dplyr::select(dplyr::all_of(sort(names(.))))
  
  # remove duplicate columns (by content)
  summary_all <- summary_all[, !duplicated(as.list(summary_all))]
  
  summary_all
}


#' Prepare pie chart data for modality analysis
#' @param df Dataframe with path data
#' @param dataset_name Dataset name to filter on
#' @param valence_keep Optional vector of valence values to keep (NULL keeps all)
#' @return Dataframe ready for pie plotting
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


#' Create pie plot for modality contribution
#' @param pdat Dataframe from pie_data function
#' @param title_txt Plot title
#' @return ggplot object
pie_plot <- function(pdat, title_txt) {
  ggplot(pdat, aes(x = "", y = prop, fill = modality)) +
    geom_col(width = 1, color = "white") +
    coord_polar(theta = "y") +
    facet_wrap(~end) +
    theme_void() +
    labs(title = title_txt) +
    geom_text(aes(label = scales::percent(prop, accuracy = 1)),
      position = position_stack(vjust = 0.5), size = 2
    )
}


#' Prefix all columns except 'node'
#' @param df Dataframe
#' @param prefix Prefix to add
#' @return Dataframe with prefixed columns (except 'node')
prefix_cols_path_analysis <- function(df, prefix) {
  df %>%
    rename_with(
      ~ ifelse(.x == "node", "node", paste0(prefix, ".", .x))
    )
}
