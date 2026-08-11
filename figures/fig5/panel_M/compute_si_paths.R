# =============================================================================
# Build / load three strongest-path caches for SI-centric Panel M views:
#   1. ppk23 ORNs  -> GABA sign-inverter pool  (feeds Plot 1)
#   2. ppk25 ORNs  -> GABA sign-inverter pool  (feeds Plot 1)
#   3. GABA sign-inverter pool -> mAL_m subtypes (feeds Plot 2)
#
# Requires: figures/fig5/setup_mspecific.R already sourced. That brings in
#   channel_neurons, gaba_sign_inverter_types, mal_subtypes, graph.general,
#   mba, paths_dir, and find_k_strongest_paths_yen.
# =============================================================================

si_paths_cache_path <- function(mod_label, target_name, n_paths = 50) {
  file.path(paths_dir,
            sprintf("strongest.%d.paths.%s.2.%s.feather",
                    n_paths, mod_label, target_name))
}

.ensure_si_cache <- function(mod_label, starts, targets, target_name,
                             n_paths = 50) {
  fname <- si_paths_cache_path(mod_label, target_name, n_paths)
  if (file.exists(fname)) {
    df <- arrow::read_feather(fname)
    if ("strength" %in% names(df) && nrow(df) > 0) {
      message(sprintf("  Loaded cached paths: %s -> %s (%d rows)",
                      mod_label, target_name, nrow(df)))
      return(df)
    }
    message(sprintf("  Cache empty at %s, recomputing.", fname))
  }

  starts  <- intersect(starts,  V(graph.general)$name)
  targets <- intersect(targets, V(graph.general)$name)
  if (length(starts) == 0 || length(targets) == 0) {
    stop(sprintf("No valid starts/targets for %s -> %s", mod_label, target_name))
  }

  g <- graph.general
  w <- E(g)$weight
  w[!is.finite(w) | w <= 0] <- .Machine$double.eps
  E(g)$log_weight <- -log(w)

  message(sprintf("  Computing %d strongest paths: %s -> %s (starts=%d, targets=%d) ...",
                  n_paths, mod_label, target_name,
                  length(starts), length(targets)))
  res <- find_k_strongest_paths_yen(
    g       = g,
    starts  = starts,
    targets = targets,
    mba     = mba,
    n_paths = n_paths
  )
  df <- res$df
  if (is.null(df) || nrow(df) == 0) {
    stop(sprintf("No paths found for %s -> %s", mod_label, target_name))
  }
  arrow::write_feather(df, fname)
  message(sprintf("    Cached %d rows -> %s", nrow(df), basename(fname)))
  df
}

# --- Public loaders ---------------------------------------------------------

load_paths_channel_to_si <- function(channel = c("ppk23", "ppk25"),
                                     n_paths = 50) {
  channel <- match.arg(channel)
  df <- .ensure_si_cache(
    mod_label   = channel,
    starts      = channel_neurons[[channel]],
    targets     = gaba_sign_inverter_types,
    target_name = "gaba_si_pool",
    n_paths     = n_paths
  )
  df$modality <- channel
  df
}

load_paths_si_to_mal <- function(n_paths = 50) {
  .ensure_si_cache(
    mod_label   = "gaba_si_pool",
    starts      = gaba_sign_inverter_types,
    targets     = mal_subtypes,
    target_name = "mAL_m",
    n_paths     = n_paths
  )
}

ensure_all_si_caches <- function(n_paths = 50) {
  list(
    ppk23_to_si = load_paths_channel_to_si("ppk23", n_paths),
    ppk25_to_si = load_paths_channel_to_si("ppk25", n_paths),
    si_to_mal   = load_paths_si_to_mal(n_paths)
  )
}
