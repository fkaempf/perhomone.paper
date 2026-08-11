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
  an05b023bc = list(
    targets = c("AN05B023b", "AN05B023c"),
    focus   = c("WG3", "WG4", "LgLG1a", "LgLG1b"),
    # two target types make for a one-branch dendrogram, so the clustered figures
    # say nothing here; the receptor table is reference material and lives on the
    # AN09B017 page
    figures = FALSE, billy = FALSE
  ),
  an09b017 = list(
    targets = c("AN09B017a", "AN09B017b", "AN09B017c", "AN09B017d",
                "AN09B017e", "AN09B017f", "AN09B017g"),
    # LgLG5-8 are the family's own drivers; LgLG1a/1b are included because
    # AN09B017d is the only member that receives them, which is what separates
    # it from a/b/c/f
    focus   = c("LgLG5", "LgLG6", "LgLG7", "LgLG8", "LgLG1a", "LgLG1b"),
    figures = TRUE, billy = TRUE
  ),
  an05b102 = list(
    targets = c("AN05B102a", "AN05B102b", "AN05B102c", "AN05B102d"),
    # a/b/c are LgLG1a/WG4/LgLG1b/WG3 cells; AN05B102d is a different animal,
    # driven by WG1 and LgLG2, so both sets are needed to show the split
    focus   = c("WG3", "WG4", "LgLG1a", "LgLG1b", "WG1", "LgLG2"),
    figures = TRUE, billy = TRUE,
    # driver line imagery for PPN1, i.e. AN05B102a
    links   = list(list(
      label = "Gen1 MCFO: R56C09",
      url   = "https://gen1mcfo.janelia.org/cgi-bin/view_gen1mcfo_imagery.cgi?line=R56C09",
      note  = paste0("the line used for PPN1 in ",
                     "<a href=\"https://elifesciences.org/articles/11188\" rel=\"noopener\">",
                     "Kallman et al. 2015</a>. The labelled morphology looks like ",
                     "<b>AN05B102a</b>"))),
    # MCFO imagery for that line, hotlinked from the Janelia FlyLight S3 bucket
    # camera for the embedded viewer, matched by hand to the VNC panel beside it
    # so the two show the neuron from the same angle
    embed   = list(body = 12286,
                   position    = c(49768.5, 60317.5, 100391.5),
                   orientation = c(0.5, -0.5, -0.5, -0.5),
                   scale       = 25967.26498891576),
    # w/h are the intrinsic pixel sizes; rot turns the portrait VNC stack on its
    # side so all three panels are landscape and the row fills the text column
    images  = list(
      list(cap = "Prothoracic, multichannel MIP", w = 686, h = 685, rot = FALSE,
           url = "https://s3.amazonaws.com/janelia-flylight-imagery/Gen1+MCFO/R56C09/R56C09-20190730_61_F1-m-40x-prothoracic-GAL4-multichannel_mip.png"),
      list(cap = "VNC, aligned to JRC2018 VNC Unisex", w = 573, h = 1119, rot = TRUE,
           url = "https://s3.amazonaws.com/janelia-flylight-imagery/Gen1+MCFO/R56C09/R56C09-20190730_61_F1-m-40x-vnc-GAL4-JRC2018_VNC_Unisex-aligned_stack.png"),
      list(cap = "Central brain, aligned to JRC2018 Unisex 20x HR", w = 1210, h = 566, rot = FALSE,
           url = "https://s3.amazonaws.com/janelia-flylight-imagery/Gen1+MCFO/R56C09/R56C09-20190730_61_F1-m-40x-central-GAL4-JRC2018_Unisex_20x_HR-aligned_stack.png"))
  )
)

CASE <- Sys.getenv("AN_CASE", "an05b023bc")
if (!CASE %in% names(CASES)) {
  stop("unknown AN_CASE '", CASE, "' - one of: ", paste(names(CASES), collapse = ", "))
}

TARGET_TYPES <- CASES[[CASE]]$targets

# optional page sections, on unless the case turns them off
`%||%` <- function(a, b) if (is.null(a)) b else a
SHOW_FIGURES <- isTRUE(CASES[[CASE]]$figures %||% TRUE)
SHOW_BILLY   <- isTRUE(CASES[[CASE]]$billy   %||% TRUE)

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
                 LgLG8  = "#18FFFF",   # cyan
                 WG1    = "#FF5252",   # red
                 LgLG2  = "#B2FF59")   # lime

if (!all(FOCUS %in% names(WEB_PALETTE))) {
  stop("no colour for: ", paste(setdiff(FOCUS, names(WEB_PALETTE)), collapse = ", "))
}
WEB_COLS <- WEB_PALETTE[FOCUS]

# --- case-derived paths and labels ------------------------------------------
SYN_RAW    <- file.path(RAW,     paste0(CASE, "_input_synapses.feather"))
SYN_ANN    <- file.path(DERIVED, paste0(CASE, "_input_synapses_annotated.feather"))
# Compact label: AN09B017a, AN09B017b, ... -> "AN09B017a-g". Listing seven full
# type names is unreadable in a page title.
CASE_LABEL <- local({
  n <- length(TARGET_TYPES)
  if (n == 1) return(TARGET_TYPES)
  pre <- ""
  for (i in seq_len(min(nchar(TARGET_TYPES)))) {
    if (length(unique(substr(TARGET_TYPES, 1, i))) == 1) pre <- substr(TARGET_TYPES[1], 1, i)
    else break
  }
  if (!nchar(pre)) return(paste(TARGET_TYPES, collapse = " / "))
  suf <- substring(TARGET_TYPES, nchar(pre) + 1)
  if (n == 2) paste0(pre, suf[1], "/", suf[2])
  else paste0(pre, suf[1], "-", suf[n])
})

# one colour per target type, for the overview scene
TARGET_COLS <- setNames(
  grDevices::hcl.colors(max(2, length(TARGET_TYPES)), "Dark 3")[seq_along(TARGET_TYPES)],
  TARGET_TYPES)

# --- literature aliases -----------------------------------------------------
# Connectome type names that the pheromone literature knows under another name.
# Kept here rather than inline so the figures, the table and the prose cannot
# drift apart.
# Populated in 03 from the maleCNS `synonyms` annotation, not hardcoded, so the
# page reports what the dataset actually records (e.g. "Yu 2010: vAB3").
TYPE_ALIAS <- character(0)

alias_of <- function(x) unname(ifelse(x %in% names(TYPE_ALIAS), TYPE_ALIAS[x], ""))

# raw coordinates are 8 nm voxels
vox_to_um <- function(v) v * 8 / 1000
