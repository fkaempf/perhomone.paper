# Data Processing Functions
# Functions for fetching and processing connectivity data

library(dplyr)
library(arrow)
library(malevnc)
library(coconatfly)
library(neuprintr)
library(igraph)
library(Matrix)
library(stringr)
options(malecns.dataset = "male-cns:v1.0")   # malecns helpers ignore MCNS_DATASET

#' Load or fetch male body annotations with ppk region annotations
#'
#' @param feather_path Path for caching the mba dataframe
#' @param force_recompute If TRUE, recompute even if cache exists
#' @param set_ppk25_glutamate If TRUE, set ppk25 neurons consensus_nt to glutamate
#' @return List with mba dataframe and ppk region IDs
load_mba <- function(
    feather_path = "/Users/fkampf/Documents/pheromone.paper/feather/mba.feather",
    force_recompute = FALSE,
    set_ppk25_glutamate = TRUE
) {
  if (!force_recompute && file.exists(feather_path)) {
    message("Loading cached mba from: ", feather_path)
    mba <- read_feather(feather_path)
  } else {
    message("Fetching mba from neuprint...")
    mba <- mcns_body_annotations()
    mba <- mba %>% mutate(type = ifelse(type == "", NA, type))

    # Get ppk23 and ppk25 body IDs
    ppk23_ids <- mba %>%
      filter(grepl("ppk23", receptor_type)) %>%
      pull(bodyid) %>%
      unique()

    ppk25_ids <- mba %>%
      filter(grepl("ppk25", receptor_type)) %>%
      pull(bodyid) %>%
      unique()

    # Get ROI info for region-specific annotations
    message("Fetching ROI info for ppk neurons...")
    roiinfo_ppk23 <- neuprint_get_roiInfo(ppk23_ids)
    roiinfo_ppk25 <- neuprint_get_roiInfo(ppk25_ids)

    # Extract region-specific IDs for ppk25
    ppk25_regions <- list(
      ProLN = roiinfo_ppk25 %>% filter(if_any(contains("ProLN"), ~ .x > 0)) %>% pull(bodyid),
      ADMN = roiinfo_ppk25 %>% filter(if_any(contains("ADMN"), ~ .x > 0)) %>% pull(bodyid),
      MesoLN = roiinfo_ppk25 %>% filter(if_any(contains("MesoLN"), ~ .x > 0)) %>% pull(bodyid),
      MetaLN = roiinfo_ppk25 %>% filter(if_any(contains("MetaLN"), ~ .x > 0)) %>% pull(bodyid)
    )

    # Extract region-specific IDs for ppk23
    ppk23_regions <- list(
      ProLN = roiinfo_ppk23 %>% filter(if_any(contains("ProLN"), ~ .x > 0)) %>% pull(bodyid),
      ADMN = roiinfo_ppk23 %>% filter(if_any(contains("ADMN"), ~ .x > 0)) %>% pull(bodyid),
      MesoLN = roiinfo_ppk23 %>% filter(if_any(contains("MesoLN"), ~ .x > 0)) %>% pull(bodyid),
      MetaLN = roiinfo_ppk23 %>% filter(if_any(contains("MetaLN"), ~ .x > 0)) %>% pull(bodyid)
    )

    # Add region suffix to type names
    mba <- mba %>%
      mutate(
        type = case_when(
          bodyid %in% c(ppk25_regions$MetaLN, ppk23_regions$MetaLN) ~ paste(type, "_MetaLN"),
          bodyid %in% c(ppk25_regions$MesoLN, ppk23_regions$MesoLN) ~ paste(type, "_MesoLN"),
          bodyid %in% c(ppk25_regions$ProLN, ppk23_regions$ProLN) ~ paste(type, "_ProLN"),
          bodyid %in% c(ppk25_regions$ADMN, ppk23_regions$ADMN) ~ paste(type, "_ADMN"),
          TRUE ~ type
        )
      )

    # Save cache
    write_feather(mba, feather_path)
    message("Saved mba to: ", feather_path)
  }

  # Optionally set ppk25 consensus_nt to glutamate
  if (set_ppk25_glutamate) {
    mba <- mba %>%
      mutate(consensus_nt = ifelse(grepl("ppk25", receptor_type), "glutamate", consensus_nt))
  }

  mba
}

#' Get ppk neuron IDs by region
#'
#' @param mba Body annotations dataframe
#' @return List with ppk23 and ppk25 IDs by region
get_ppk_region_ids <- function(mba) {
  ppk23_ids <- mba %>% filter(grepl("ppk23", receptor_type)) %>% pull(bodyid) %>% unique()
  ppk25_ids <- mba %>% filter(grepl("ppk25", receptor_type)) %>% pull(bodyid) %>% unique()

  roiinfo_ppk23 <- neuprint_get_roiInfo(ppk23_ids)
  roiinfo_ppk25 <- neuprint_get_roiInfo(ppk25_ids)

  list(
    ppk23 = list(
      all = ppk23_ids,
      ProLN = roiinfo_ppk23 %>% filter(if_any(contains("ProLN"), ~ .x > 0)) %>% pull(bodyid),
      ADMN = roiinfo_ppk23 %>% filter(if_any(contains("ADMN"), ~ .x > 0)) %>% pull(bodyid),
      MesoLN = roiinfo_ppk23 %>% filter(if_any(contains("MesoLN"), ~ .x > 0)) %>% pull(bodyid),
      MetaLN = roiinfo_ppk23 %>% filter(if_any(contains("MetaLN"), ~ .x > 0)) %>% pull(bodyid)
    ),
    ppk25 = list(
      all = ppk25_ids,
      ProLN = roiinfo_ppk25 %>% filter(if_any(contains("ProLN"), ~ .x > 0)) %>% pull(bodyid),
      ADMN = roiinfo_ppk25 %>% filter(if_any(contains("ADMN"), ~ .x > 0)) %>% pull(bodyid),
      MesoLN = roiinfo_ppk25 %>% filter(if_any(contains("MesoLN"), ~ .x > 0)) %>% pull(bodyid),
      MetaLN = roiinfo_ppk25 %>% filter(if_any(contains("MetaLN"), ~ .x > 0)) %>% pull(bodyid)
    )
  )
}

#' Fetch connectivity data with annotations
#' @param synapse_threshold Minimum synapse threshold
#' @param mba Body annotations dataframe
#' @return Connectivity dataframe with annotations
fetch_connectivity <- function(synapse_threshold = 5, mba = NULL) {
  if (is.null(mba)) {
    mba <- mcns_body_annotations() %>%
      mutate(type = coalesce(type, flywire_type, manc_type, hemibrain_type)) %>%
      mutate(cachero.type = str_extract(synonyms, "(?<=Cachero 2010:)[^;]+") %>%
        str_trim())
  } else {
    mba %>%
      mutate(type = coalesce(type, flywire_type, manc_type, hemibrain_type)) %>%
      mutate(cachero.type = str_extract(synonyms, "(?<=Cachero 2010:)[^;]+") %>%
        str_trim()) -> mba
  }

  connectivity <- cf_partners(
    cf_ids(malecns = mba %>% pull(bodyid)),
    partners = "o",
    threshold = synapse_threshold
  )

  connectivity <- connectivity %>%
    left_join(
      mba %>%
        select("type", "bodyid", "fru_dsx", "consensus_nt", "flywire_type",
               "synonyms", "receptor_type", "cachero.type", "dimorphism") %>%
        mutate(bodyid = as.integer(bodyid)) %>%
        rename(
          pre_type = type,
          pre_fru_dsx = fru_dsx,
          pre_nt = consensus_nt,
          pre_fw_type = flywire_type,
          pre_synonyms = synonyms,
          pre_receptor_type = receptor_type,
          pre.dimorphism = dimorphism,
          pre.cachero.type = cachero.type
        ),
      by = c("pre_id" = "bodyid")
    ) %>%
    rename(post_type = type) %>%
    left_join(
      mba %>%
        select("bodyid", "fru_dsx", "consensus_nt", "flywire_type",
               "synonyms", "receptor_type", "cachero.type", "dimorphism") %>%
        mutate(bodyid = as.integer(bodyid)) %>%
        rename(
          post_fru_dsx = fru_dsx,
          post_nt = consensus_nt,
          post_fw_type = flywire_type,
          post_synonyms = synonyms,
          post_receptor_type = receptor_type,
          post.dimorphism = dimorphism,
          post.cachero.type = cachero.type
        ),
      by = c("post_id" = "bodyid")
    )

  return(connectivity)
}

#' Calculate normalized adjacency matrix
#' @param connectivity Connectivity dataframe
#' @param cell.or.type Use "cell" or "type" level
#' @param pre.or.post Normalization type: "pre", "post", "avg", or "raw"
#' @return Normalized adjacency matrix
calculate_normed_adj_matrix <- function(connectivity,
                                        cell.or.type = "type",
                                        pre.or.post = "pre") {
  # Build raw adjacency with integer synapse counts
  if (cell.or.type == "cell") {
    unique.identifier <- union(
      as.character(connectivity$pre_id),
      as.character(connectivity$post_id)
    )
    adj.matrix <- sparseMatrix(
      i   = match(connectivity$pre_id,  unique.identifier),
      j   = match(connectivity$post_id, unique.identifier),
      x   = as.integer(connectivity$weight),
      dims = c(length(unique.identifier), length(unique.identifier)),
      dimnames = list(unique.identifier, unique.identifier)
    )
  } else {
    unique.identifier <- union(
      connectivity$pre_type,
      connectivity$post_type
    )
    adj.matrix <- sparseMatrix(
      i   = match(connectivity$pre_type,  unique.identifier),
      j   = match(connectivity$post_type, unique.identifier),
      x   = as.integer(connectivity$weight),
      dims = c(length(unique.identifier), length(unique.identifier)),
      dimnames = list(unique.identifier, unique.identifier)
    )
  }

  # Choose what to return
  if (pre.or.post == "raw") {
    # Raw integer synapse-count adjacency
    return(adj.matrix)

  } else if (pre.or.post == "pre") {
    # Row-normalised (pre)
    adj.matrix.normed.pre <- rowScale(adj.matrix)
    colnames(adj.matrix.normed.pre) <- colnames(adj.matrix)
    rownames(adj.matrix.normed.pre) <- rownames(adj.matrix)
    return(adj.matrix.normed.pre)

  } else if (pre.or.post == "avg") {
    # Average of row- and col-normalised
    adj.matrix.normed.post <- colScale(adj.matrix)
    colnames(adj.matrix.normed.post) <- colnames(adj.matrix)
    rownames(adj.matrix.normed.post) <- rownames(adj.matrix)

    adj.matrix.normed.pre  <- rowScale(adj.matrix)
    colnames(adj.matrix.normed.pre)  <- colnames(adj.matrix)
    rownames(adj.matrix.normed.pre)  <- rownames(adj.matrix)

    avg_mat <- (adj.matrix.normed.post + adj.matrix.normed.pre) / 2
    return(avg_mat)

  } else {
    # Col-normalised (post)
    adj.matrix.normed.post <- colScale(adj.matrix)
    colnames(adj.matrix.normed.post) <- colnames(adj.matrix)
    rownames(adj.matrix.normed.post) <- rownames(adj.matrix)
    return(adj.matrix.normed.post)
  }
}

#' Load or fetch connectivity data
#'
#' @param mba Body annotations dataframe
#' @param feather_path Path for caching
#' @param force_recompute If TRUE, recompute even if cache exists
#' @param rename_putative If TRUE, rename putative_ppk23/25 to m-cell/f-cell
#' @return Connectivity dataframe
load_connectivity <- function(
    mba,
    feather_path = "/Users/fkampf/Documents/pheromone.paper/feather/connectivity.feather",
    force_recompute = FALSE,
    rename_putative = TRUE
) {
  if (!force_recompute && file.exists(feather_path)) {
    message("Loading cached connectivity from: ", feather_path)
    conn <- read_feather(feather_path)
  } else {
    message("Fetching connectivity...")
    conn <- fetch_connectivity(mba = mba)
    write_feather(conn, feather_path)
    message("Saved connectivity to: ", feather_path)
  }

  if (rename_putative) {
    conn <- conn %>%
      mutate(
        pre_type = case_when(
          grepl("putative_ppk23", pre_receptor_type) ~ "m-cell",
          grepl("putative_ppk25", pre_receptor_type) ~ "f-cell",
          TRUE ~ pre_type
        ),
        post_type = case_when(
          grepl("putative_ppk23", post_receptor_type) ~ "m-cell",
          grepl("putative_ppk25", post_receptor_type) ~ "f-cell",
          TRUE ~ post_type
        )
      )
  }

  conn
}

#' Prepare connectivity for adjacency matrix creation
#'
#' @param conn Connectivity dataframe
#' @return Cleaned connectivity dataframe
prepare_connectivity <- function(conn) {
  conn %>%
    mutate(
      pre_type = coalesce(pre_type, pre_fw_type),
      post_type = coalesce(post_type, post_fw_type)
    ) %>%
    mutate(
      pre_type = if_else(is.na(pre_type), as.character(bodyid), pre_type),
      post_type = if_else(is.na(post_type), as.character(partner), post_type)
    ) %>%
    mutate(
      pre_type = gsub("[()]", "", pre_type),
      post_type = gsub("[()]", "", post_type)
    )
}

#' Load or create all adjacency matrices
#'
#' @param conn Connectivity dataframe (will be prepared internally)
#' @param cache_dir Directory for caching RDS files
#' @param force_recompute If TRUE, recompute even if cache exists
#' @return List with adj.matrix (post-normed), adj.matrix.pre, adj.matrix.raw
load_adjacency_matrices <- function(
    conn,
    cache_dir = "/Users/fkampf/Documents/pheromone.paper/feather",
    force_recompute = FALSE
) {
  # Prepare connectivity

  conn_clean <- prepare_connectivity(conn)

  paths <- list(
    post = file.path(cache_dir, "adj.matrix.rds"),
    pre = file.path(cache_dir, "adj.matrix.pre.rds"),
    raw = file.path(cache_dir, "adj.matrix.raw.rds")
  )

  result <- list()

  # Post-normalized (column-normalized)
  if (!force_recompute && file.exists(paths$post)) {
    message("Loading cached adj.matrix (post-normed)")
    result$adj.matrix <- readRDS(paths$post)
  } else {
    message("Computing adj.matrix (post-normed)...")
    result$adj.matrix <- calculate_normed_adj_matrix(conn_clean, cell.or.type = "type", pre.or.post = "post")
    saveRDS(result$adj.matrix, paths$post)
  }

  # Pre-normalized (row-normalized)
  if (!force_recompute && file.exists(paths$pre)) {
    message("Loading cached adj.matrix.pre")
    result$adj.matrix.pre <- readRDS(paths$pre)
  } else {
    message("Computing adj.matrix.pre...")
    result$adj.matrix.pre <- calculate_normed_adj_matrix(conn_clean, cell.or.type = "type", pre.or.post = "pre")
    saveRDS(result$adj.matrix.pre, paths$pre)
  }

  # Raw (unnormalized)
  if (!force_recompute && file.exists(paths$raw)) {
    message("Loading cached adj.matrix.raw")
    result$adj.matrix.raw <- readRDS(paths$raw)
  } else {
    message("Computing adj.matrix.raw...")
    result$adj.matrix.raw <- calculate_normed_adj_matrix(conn_clean, cell.or.type = "type", pre.or.post = "raw")
    saveRDS(result$adj.matrix.raw, paths$raw)
  }

  result
}

#' Load or create weighted igraph from adjacency matrix
#'
#' @param adj.matrix Adjacency matrix (typically post-normalized)
#' @param cache_path Path for caching the graph
#' @param force_recompute If TRUE, recompute even if cache exists
#' @return igraph object with log_weight edge attribute
load_graph <- function(
    adj.matrix,
    cache_path = "/Users/fkampf/Documents/pheromone.paper/feather/graph.general.rds",
    force_recompute = FALSE
) {
  if (!force_recompute && file.exists(cache_path)) {
    message("Loading cached graph")
    g <- readRDS(cache_path)
  } else {
    message("Creating graph from adjacency matrix...")
    g <- graph_from_adjacency_matrix(
      adj.matrix,
      mode = "directed",
      weighted = TRUE,
      diag = FALSE
    )
    saveRDS(g, cache_path)
  }


  # Add log weights for path finding
  w <- E(g)$weight
  if (is.null(w)) stop("Edges must have numeric 'weight'.")
  w[!is.finite(w) | w <= 0] <- .Machine$double.eps
  E(g)$log_weight <- -log(w)

  g
}

#' Complete data loading pipeline
#'
#' Loads mba, connectivity, adjacency matrices, and graph in one call.
#'
#' @param cache_dir Base directory for all cache files
#' @param force_recompute If TRUE, recompute everything
#' @param set_ppk25_glutamate If TRUE, set ppk25 consensus_nt to glutamate
#' @return List with mba, conn, adj_matrices, and graph
load_all_data <- function(
    cache_dir = "/Users/fkampf/Documents/pheromone.paper/feather",
    force_recompute = FALSE,
    set_ppk25_glutamate = TRUE
) {
  message("=== Loading all data ===")

  # Load mba
  mba <- load_mba(
    feather_path = file.path(cache_dir, "mba.feather"),
    force_recompute = force_recompute,
    set_ppk25_glutamate = set_ppk25_glutamate
  )

  # Load connectivity
  conn <- load_connectivity(
    mba = mba,
    feather_path = file.path(cache_dir, "connectivity.feather"),
    force_recompute = force_recompute
  )

  # Load adjacency matrices
  adj_matrices <- load_adjacency_matrices(
    conn = conn,
    cache_dir = cache_dir,
    force_recompute = force_recompute
  )

  # Load graph
  graph <- load_graph(
    adj.matrix = adj_matrices$adj.matrix,
    cache_path = file.path(cache_dir, "graph.general.rds"),
    force_recompute = force_recompute
  )

  message("=== Data loading complete ===")

  list(
    mba = mba,
    conn = conn,
    adj.matrix = adj_matrices$adj.matrix,
    adj.matrix.pre = adj_matrices$adj.matrix.pre,
    adj.matrix.raw = adj_matrices$adj.matrix.raw,
    graph = graph
  )
}

#' Get downstream targets for a set of neurons
#'
#' @param neuron_ids Vector of body IDs
#' @param mba Body annotations dataframe
#' @param min_weight_frac Minimum fraction of total weight to include (default 0.001)
#' @param exclude_patterns Patterns to exclude from results (default c("AN", "IN"))
#' @return Vector of target type names
get_downstream_targets <- function(
    neuron_ids,
    mba,
    min_weight_frac = 0.001,
    exclude_patterns = c("AN", "IN")
) {
  targets <- cf_partner_summary(cf_ids(malecns = neuron_ids), partners = "out", normalise = FALSE) %>%
    group_by(type.post) %>%
    summarize(weight = sum(weight), .groups = "drop") %>%
    filter(!is.na(type.post))

  # Apply exclusion patterns

for (pattern in exclude_patterns) {
    targets <- targets %>% filter(!grepl(pattern, type.post))
  }

  targets %>%
    arrange(desc(weight)) %>%
    filter(weight / sum(weight) >= min_weight_frac) %>%
    pull(type.post)
}
