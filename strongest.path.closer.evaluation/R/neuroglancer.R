# Neuroglancer URL Generation Functions
# Functions for creating and shortening neuroglancer visualization links

library(jsonlite)
make_mcns_scene <- function(
  ids,
  title        = "CNS-Quad",
  em_url       = "precomputed://gs://cns-full-clahe",
  malecns_url  = "dvid://https://emdata6-novran.janelia.org/f3969:master/segmentation?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app",
  brain_shell_url =
    "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/brain-shell-smooth-linear",
  vnc_shell_url   =
    "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/vnc-shell",
  pl_url   = NULL,
  pl_name  = "plshere"
) {
  ## keep exact input order
  ids_chr <- as.character(ids)

  ## EM base layer
  em_layer <- list(
    type   = "image",
    source = list(
      url                     = em_url,
      subsources              = list(default = TRUE),
      enableDefaultSubsources = FALSE
    ),
    tab   = "rendering",
    name  = "em"
  )

  ## malecns segmentation layer
  malecns_layer <- list(
    type   = "segmentation",
    source = list(
      list(
        url                     = malecns_url,
        subsources              = list(default = TRUE, meshes = TRUE),
        enableDefaultSubsources = FALSE
      ),
      "precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_properties/emdata6-novran.janelia.org/f3969:master/segmentation_annotations/type/group"
    ),
    toolBindings = list(Q = "selectSegments"),
    tab          = "segments",
    segments     = ids_chr,                         # order preserved
    segmentQuery = paste(ids_chr, collapse = " "),  # order preserved
    name         = "malecns"
  )

  ## brain-shell layer
  brain_shell_layer <- list(
    type   = "segmentation",
    source = list(
      url                     = brain_shell_url,
      subsources              = list(default = TRUE, properties = TRUE, mesh = TRUE),
      enableDefaultSubsources = FALSE
    ),
    pick                    = FALSE,
    tab                     = "rendering",
    selectedAlpha           = 0,
    saturation              = 0,
    meshSilhouetteRendering = 7,
    segments                = list("1"),
    colorSeed               = 1336242844,
    segmentDefaultColor     = "#ffffff",
    name                    = "brain-shell"
  )

  ## vnc-shell layer
  vnc_shell_layer <- list(
    type   = "segmentation",
    source = list(
      url                     = vnc_shell_url,
      subsources              = list(default = TRUE, properties = TRUE, mesh = TRUE),
      enableDefaultSubsources = FALSE
    ),
    pick                    = FALSE,
    tab                     = "segments",
    selectedAlpha           = 0,
    saturation              = 0,
    meshSilhouetteRendering = 7,
    segments                = list("1"),
    colorSeed               = 1336242844,
    segmentDefaultColor     = "#ffffff",
    name                    = "vnc-shell"
  )

  layers <- list(
    em_layer,
    malecns_layer,
    brain_shell_layer,
    vnc_shell_layer
  )

  ## optional pl reference layer
  if (!is.null(pl_url)) {
    pl_layer <- list(
      type   = "segmentation",
      source = list(
        url                     = pl_url,
        subsources              = list(default = TRUE, properties = TRUE, mesh = TRUE),
        enableDefaultSubsources = FALSE
      ),
      pick     = FALSE,
      tab      = "segments",
      segments = list("1"),
      name     = pl_name
    )
    layers <- c(layers, list(pl_layer))
  }

  scene <- list(
    title      = title,
    dimensions = list(
      x = list(8e-9, "m"),
      y = list(8e-9, "m"),
      z = list(8e-9, "m")
    ),
    ## orientation + zoom taken from your reference URL
    position             = c(47470.59375, 54212.50390625, 66301.59375),
    crossSectionScale    = 1.1208,
    projectionOrientation= c(
      0,
      0.7071067690849304,
      0.7071067690849304,
      0
    ),
    projectionScale      = 192860.74860894235,
    layers               = layers,
    showAxisLines        = FALSE,
    showSlices           = FALSE,
    prefetch             = FALSE,
    selectedLayer        = list(
      visible = TRUE,
      layer   = "malecns"
    ),
    layout               = "3d"
  )

  scene
}


## ------------------------------------------------------------------
## 2) Make long Clio-NG URL from a scene
## ------------------------------------------------------------------
make_ng_url <- function(scene,
                        base_url = "https://clio-ng.janelia.org/#!") {

  if (is.character(scene) && length(scene) == 1L && file.exists(scene)) {
    scene_json <- paste(readLines(scene, warn = FALSE), collapse = "")
  } else if (is.list(scene)) {
    scene_json <- jsonlite::toJSON(scene, auto_unbox = TRUE, pretty = FALSE)
  } else if (is.character(scene)) {
    scene_json <- scene
  } else {
    stop("scene must be a list, JSON string, or path to JSON file")
  }

  encoded <- utils::URLencode(scene_json, reserved = TRUE)
  paste0(base_url, encoded)
}

## ------------------------------------------------------------------
## 3) Free shortener via is.gd
## ------------------------------------------------------------------
shorten_free <- function(long_url) {
  api <- "https://is.gd/create.php?format=simple&url="
  readLines(
    paste0(api, utils::URLencode(long_url, reserved = TRUE)),
    warn = FALSE
  )
}

## ------------------------------------------------------------------
## 4) Convenience wrapper: IDs -> short Clio link
## ------------------------------------------------------------------
mcns_shortlink <- function(ids,
                           pl_url  = NULL,
                           pl_name = "plshere") {
  scene <- make_mcns_scene(ids, pl_url = pl_url, pl_name = pl_name)
  long  <- make_ng_url(scene)
  shorten_free(long)
}



## ------------------------------------------------------------------
## Example
## ------------------------------------------------------------------
ids   <- c(13693, 13341)
scene <- make_mcns_scene(ids)
url   <- make_ng_url(scene)

writeLines(url, "/Users/fkampf/Documents/pheromone.paper/strongest.path.closer.evaluation/full_url.txt")
browseURL(url)
```
```{r}
## ------------------------------------------------------------------
## Dependencies
## ------------------------------------------------------------------
library(jsonlite)

## ------------------------------------------------------------------
## 1) Build MCNS scene (EM + malecns + brain-shell + vnc-shell + optional pl)
##    Now supports:
##      - ids: numeric/character vector (old behavior)
##      - id_groups: list of numeric/character vectors (multiple layers)
##        with optional group_colors and group_names
## ------------------------------------------------------------------
mcns_shortlink_groups <- function(id_groups,
                                  group_colors = NULL,
                                  group_names  = NULL,
                                  pl_url       = NULL,
                                  pl_name      = "plshere") {
  scene <- make_mcns_scene(
    ids          = NULL,
    id_groups    = id_groups,
    group_colors = group_colors,
    group_names  = group_names,
    pl_url       = pl_url,
    pl_name      = pl_name
  )
  long  <- make_ng_url(scene)
  
}






```


```{r}

tsne_df %>% select(eval_identity,node) %>% filter(eval_identity=='ppk25.in+VA1v') %>% View() #HERE I SELECT A MODALITY PAIR AND FIND NEURONS THAT RELAY ONLY THOSE TWO
NTOI <- "AN09B023"

#all.modalities.included %>% filter(grepl(NTOI,path)) %>% View()


get.body.ids <- function(type_string){
                         
    mba %>%
