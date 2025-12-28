# Data Processing Functions
# Functions for fetching and processing connectivity data

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
