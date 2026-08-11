# Shared paths and constants. Every script in R/ sources this first.
# Structure follows ~/Documents/AVLP743m_connectomics.

PROJ    <- "/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation"
RAW     <- file.path(PROJ, "data", "raw")       # fetched from neuprint, cached
DERIVED <- file.path(PROJ, "data", "derived")   # produced by these scripts
PLOTS   <- file.path(PROJ, "plots")

# the pheromone.paper repo supplies mba.feather and R/neuroglancer.R
PAPER <- "/Users/fkampf/Documents/pheromone.paper"

# the Clio-NG scenes are published from the fkaempf.github.io checkout that
# already lives inside the AVLP743m project
SITE <- "/Users/fkampf/Documents/AVLP743m_connectomics/website"

for (p in c(RAW, DERIVED, PLOTS)) dir.create(p, recursive = TRUE, showWarnings = FALSE)

MCNS_DATASET <- "male-cns:v0.9"
MCNS_SERVER  <- "https://neuprint-cns.janelia.org"

# --- cases ------------------------------------------------------------------
# Scripts 01-03 run against one case at a time. Pick it by setting AN_CASE before
# sourcing, either in the session
#     Sys.setenv(AN_CASE = "an09b017")
# or on the command line
#     AN_CASE=an09b017 Rscript R/01_fetch_input_synapses.R
#
# Every cache file, plot and neuroglancer scene is prefixed with the case name,
# so the two cases never overwrite each other.
CASES <- list(
  an05b023 = list(
    targets = c("AN05B023b", "AN05B023c"),
    focus   = c("WG3", "WG4", "LgLG1a", "LgLG1b")
  ),
  an09b017 = list(
    targets = c("AN09B017a", "AN09B017b", "AN09B017c", "AN09B017d",
                "AN09B017e", "AN09B017f", "AN09B017g"),
    # LgLG5-8 are the family's own drivers; LgLG1a/1b are included because
    # AN09B017d is the only member that receives them, which is what separates
    # it from a/b/c/f
    focus   = c("LgLG5", "LgLG6", "LgLG7", "LgLG8", "LgLG1a", "LgLG1b")
  )
)

CASE <- Sys.getenv("AN_CASE", "an05b023")
if (!CASE %in% names(CASES)) {
  stop("unknown AN_CASE '", CASE, "' - one of: ", paste(names(CASES), collapse = ", "))
}

TARGET_TYPES <- CASES[[CASE]]$targets

# --- focus sensory inputs ---------------------------------------------------
# Types are named as they are in the connectome. No receptor-channel grouping:
# the ppk23/ppk25 assignment is a light-level call from Fig 1 and is not used here.
#
# NOTE on suffixes: the neuprint server's `type` is always the bare name. The
# " _ADMN" / " _ProLN" / " _MesoLN" / " _MetaLN" variants exist only in the local
# mba.feather, minted in pheromone.paper/R/data_processing.R (~line 65) from
# neuprint_get_roiInfo. Note the SPACE before the underscore. Matching on the bare
# name with == therefore drops the suffixed majority silently, which is why every
# focus filter in this project goes through bare_type() first.
FOCUS <- CASES[[CASE]]$focus

bare_type <- function(x) sub(" _(ADMN|ProLN|MesoLN|MetaLN)$", "", x)

# Neuroglancer palette: black background, clearly separated hues at high
# luminance. Deliberately not paired by hue - the colours carry no grouping claim.
WEB_PALETTE <- c(WG3    = "#00E676",   # green
                 WG4    = "#FFAB00",   # amber
                 LgLG1a = "#FF4081",   # pink
                 LgLG1b = "#00B0FF",   # blue
                 LgLG5  = "#FFFF00",   # yellow
                 LgLG6  = "#7C4DFF",   # violet
                 LgLG7  = "#FF6D00",   # orange
                 LgLG8  = "#18FFFF")   # cyan

if (!all(FOCUS %in% names(WEB_PALETTE))) {
  stop("no colour for: ", paste(setdiff(FOCUS, names(WEB_PALETTE)), collapse = ", "))
}
WEB_COLS <- WEB_PALETTE[FOCUS]

# --- case-derived paths and labels ------------------------------------------
SYN_RAW    <- file.path(RAW,     paste0(CASE, "_input_synapses.feather"))
SYN_ANN    <- file.path(DERIVED, paste0(CASE, "_input_synapses_annotated.feather"))
CASE_LABEL <- paste(TARGET_TYPES, collapse = " / ")

# one colour per target type, for the overview scene
TARGET_COLS <- setNames(
  grDevices::hcl.colors(max(2, length(TARGET_TYPES)), "Dark 3")[seq_along(TARGET_TYPES)],
  TARGET_TYPES)

# raw coordinates are 8 nm voxels
vox_to_um <- function(v) v * 8 / 1000
