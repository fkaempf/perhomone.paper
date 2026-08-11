# Clio-NG scenes for the target types of the selected case (see _paths.R):
#   - one scene per body: that neuron in red, plus its input synapses as point
#     annotations, one layer per presynaptic sensory type
#   - one overview scene with every body in the case
#   - a menu page linking to all of them
#
# The segmentation (f3969:master) and EM (gs://cns-full-clahe) sources both span
# the full CNS, and vnc-shell is already one of the default layers, so the VNC
# synapses render without any source change.
#
# Publishing is manual and deliberate:
#   cd /Users/fkampf/Documents/AVLP743m_connectomics/website
#   git add -A ng && git commit -m "..." && git push

suppressMessages({
  library(arrow); library(dplyr); library(jsonlite)
})
options(rgl.useNULL = TRUE)

source("/Users/fkampf/Documents/pheromone.paper/R/neuroglancer.R")
source("/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R")

ng_dir <- file.path(SITE, "ng")
base   <- "https://floriankaempf.com/ng"
dir.create(ng_dir, showWarnings = FALSE, recursive = TRUE)

focus_cols <- WEB_COLS[FOCUS]

syn <- read_feather(SYN_ANN)
bodies <- syn %>% distinct(bodyid, target_type, soma_side) %>% arrange(target_type, bodyid)

dims <- list(x = list(8e-9, "m"), y = list(8e-9, "m"), z = list(8e-9, "m"))

point_layer <- function(df, name, colour, visible = TRUE) {
  anns <- lapply(seq_len(nrow(df)), function(i) {
    list(point = c(df$x[i], df$y[i], df$z[i]), type = "point", id = as.character(i))
  })
  list(type = "annotation",
       source = list(url = "local://annotations",
                     transform = list(outputDimensions = dims)),
       tool = "annotatePoint", annotations = anns, annotationColor = colour,
       shader = "void main() { setColor(defaultColor()); setPointMarkerSize(8.0); }",
       visible = visible, tab = "annotations",
       name = sprintf("%s (%d syn)", name, nrow(df)))
}

write_scene <- function(scene, fname) {
  write(toJSON(scene, auto_unbox = TRUE, pretty = FALSE, digits = 8),
        file.path(ng_dir, fname))
  sprintf("https://clio-ng.janelia.org/#!%s/%s", base, fname)
}

# --- one scene per body ------------------------------------------------------
per_body <- lapply(seq_len(nrow(bodies)), function(i) {
  b  <- bodies$bodyid[i]
  tt <- bodies$target_type[i]
  s  <- syn %>% filter(bodyid == b)

  scene <- make_mcns_scene(b, title = sprintf("%s %s", tt, b))
  scene$layers[[2]]$segments            <- as.list(as.character(b))
  scene$layers[[2]]$segmentDefaultColor <- "#ff0000"
  scene$layers[[2]]$segmentColors       <- setNames(list("#ff0000"), as.character(b))

  anns <- lapply(FOCUS, function(tp) {
    point_layer(s %>% filter(partner_group == tp), tp, unname(focus_cols[tp]))
  })
  other <- s %>% filter(!is_focus)
  set.seed(1)
  n_other_all <- nrow(other)
  if (n_other_all > 300) other <- other[sample(n_other_all, 300), ]
  anns <- c(anns, list(point_layer(
    other, sprintf("other inputs (sample of %d)", n_other_all), "#9e9e9e", FALSE)))

  scene$layers <- c(scene$layers, anns)
  f <- s %>% filter(is_focus)
  scene$position <- c(mean(f$x), mean(f$y), mean(f$z))

  fname <- sprintf("%s_%s.json", tt, b)
  url   <- write_scene(scene, fname)
  data.frame(type = tt, bodyid = b, soma_side = bodies$soma_side[i],
             n_syn = nrow(s), n_focus = sum(s$is_focus, na.rm = TRUE),
             file = fname, url = url,
             kb = round(file.size(file.path(ng_dir, fname)) / 1024))
})
per_body <- bind_rows(per_body)
print(per_body %>% select(type, bodyid, soma_side, n_syn, n_focus, kb) %>% as.data.frame())

# --- overview: every body in the case ---------------------------------------
all_ids <- bodies$bodyid
scene <- make_mcns_scene(all_ids, title = sprintf("%s - sensory input", CASE_LABEL))
scene$layers[[2]]$segments <- as.list(as.character(all_ids))
# one colour per target type, so the types stay distinguishable in the overview
type_col <- unname(TARGET_COLS[bodies$target_type])
scene$layers[[2]]$segmentColors <- setNames(as.list(type_col), as.character(all_ids))

pt_layers <- lapply(FOCUS, function(tp) {
  point_layer(syn %>% filter(partner_group == tp), tp, unname(focus_cols[tp]))
})
scene$layers <- c(scene$layers, pt_layers)
f <- syn %>% filter(is_focus)
scene$position <- c(mean(f$x), mean(f$y), mean(f$z))
overview_url <- write_scene(scene, sprintf("%s_overview.json", CASE))

# --- menu page ---------------------------------------------------------------
rows <- paste(sprintf(
  '<tr><td><a href="%s">%s %s</a></td><td>%s</td><td>%d</td><td>%d</td></tr>',
  per_body$url, per_body$type, per_body$bodyid, per_body$soma_side,
  per_body$n_syn, per_body$n_focus), collapse = "\n")

# built from focus_cols so the legend cannot drift from the scene colours
legend <- paste(sprintf(
  '<span class="sw" style="background:%s%s"></span>%s',
  unname(focus_cols), c("", rep(";margin-left:1rem", length(focus_cols) - 1)),
  names(focus_cols)), collapse = "\n")

html <- sprintf('<!doctype html>
<meta charset="utf-8">
<title>%s - Clio-NG scenes</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<style>
 body{font:15px/1.6 system-ui,sans-serif;margin:0;padding:2.5rem 1.25rem;
      max-width:52rem;margin-inline:auto;color:#1a1a1a;background:#fff}
 h1{font-size:1.5rem;margin:0 0 .35rem}
 p.sub{color:#555;margin:0 0 2rem}
 a{color:#0b5fa5}
 .big{display:block;padding:1rem 1.15rem;border:1px solid #d8d8d8;border-radius:9px;
      margin-bottom:1.75rem;text-decoration:none;color:inherit}
 .big:hover{border-color:#0b5fa5;background:#f7fbff}
 .big b{color:#0b5fa5}
 table{border-collapse:collapse;width:100%%}
 th,td{text-align:left;padding:.45rem .6rem;border-bottom:1px solid #ececec}
 th{font-weight:600;color:#555;font-size:.85rem;text-transform:uppercase;
    letter-spacing:.03em}
 td:nth-child(n+3){text-align:right;font-variant-numeric:tabular-nums}
 .legend{margin:1.5rem 0 0;font-size:.9rem;color:#555}
 .sw{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;
     margin-right:.35rem;vertical-align:-1px}
 @media (prefers-color-scheme:dark){
  body{background:#141414;color:#e8e8e8}
  a{color:#6fb3ef} .big{border-color:#333} .big b{color:#6fb3ef}
  .big:hover{border-color:#6fb3ef;background:#1b2430}
  th,td{border-bottom-color:#2a2a2a} th,.legend,p.sub{color:#aaa}
 }
</style>
<h1>%s sensory input</h1>
<p class="sub">Clio-NG scenes for the male CNS (male-cns:v0.9). The neuron is red;
input synapses are point annotations, one layer per presynaptic sensory type.
All of this input lands in the nerve cord. Extra layers start hidden; toggle
them in the layer bar.</p>

<a class="big" href="%s">
  <b>Overview: all %d bodies</b><br>
  One colour per target type, with every sensory input synapse from the focus
  types overlaid.
</a>

<table>
<tr><th>Neuron</th><th>Side</th><th>Input syn</th><th>Of the focus types</th></tr>
%s
</table>

<p class="legend">
%s
</p>',
  CASE_LABEL, CASE_LABEL, overview_url, nrow(per_body), rows, legend)

dir.create(file.path(ng_dir, CASE), showWarnings = FALSE)
write(html, file.path(ng_dir, CASE, "index.html"))

write.csv(per_body, file.path(DERIVED, paste0(CASE, "_neuroglancer_scenes.csv")),
          row.names = FALSE)
cat("\nmenu:    ", file.path(ng_dir, CASE, "index.html"), "\n")
cat("overview:", overview_url, "\n")
