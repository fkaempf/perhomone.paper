# Clio-NG scenes for the target types of the selected case (see _paths.R):
#   - one scene per body: that neuron in red, plus its input synapses as point
#     annotations, one layer per presynaptic sensory type
#   - one overview scene with every body in the case
#   - a menu page linking to all of them
#
# The segmentation (4b2087c0fbe046bfaf0d60bc970e3e5d) and EM (gs://cns-full-clahe) sources both span
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

# make_mcns_scene frames the whole CNS (projectionScale 192860 vox = 1.54 mm),
# which leaves every scene opening far too wide. Fit the zoom to the extent of the
# points the scene is actually about, with a floor so a tight cluster does not
# open inside the neuron.
fit_scale <- function(d, pad = 1.8, floor_vox = 2500) {
  if (!nrow(d)) return(NULL)
  span <- max(diff(range(d$x)), diff(range(d$y)), diff(range(d$z)))
  max(floor_vox, round(span * pad))
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
  scene$position        <- c(mean(f$x), mean(f$y), mean(f$z))
  scene$projectionScale <- fit_scale(f)

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
scene$position        <- c(mean(f$x), mean(f$y), mean(f$z))
scene$projectionScale <- fit_scale(f)
overview_url <- write_scene(scene, sprintf("%s_overview.json", CASE))

# --- cluster diagrams for the menu page --------------------------------------
# Built from the same annotated synapses as the scenes, so the figures and the
# point layers can never disagree. Three views of one matrix:
#   raw   synapse counts
#   norm  as a fraction of that target's TOTAL input (all sources, focus or not)
#   comp  renormalised so each column sums to 1 - profile shape, scale removed
suppressMessages({ library(pheatmap); library(viridisLite); library(grid) })
options(malecns.dataset = "male-cns:v1.0")   # malecns helpers ignore MCNS_DATASET

case_dir <- file.path(ng_dir, CASE)
dir.create(case_dir, showWarnings = FALSE, recursive = TRUE)

raw <- syn %>% filter(is_focus) %>% count(partner_group, target_type) %>%
  xtabs(n ~ partner_group + target_type, data = .)
raw <- raw[FOCUS[FOCUS %in% rownames(raw)], , drop = FALSE]

tot_in <- syn %>% count(target_type)
tot_in <- setNames(tot_in$n, tot_in$target_type)

norm <- sweep(raw, 2, tot_in[colnames(raw)], "/")
comp <- prop.table(raw, 2)

# Column names share a long prefix (AN09B017a..g), which collides at any sensible
# cell width. Strip the common prefix onto the title and label the columns by what
# actually differs.
cn     <- colnames(raw)
prefix <- ""
for (i in seq_len(min(nchar(cn)))) {
  if (length(unique(substr(cn, 1, i))) == 1) prefix <- substr(cn[1], 1, i) else break
}
short <- if (nchar(prefix)) substring(cn, nchar(prefix) + 1) else cn
colnames(raw) <- colnames(norm) <- colnames(comp) <- short
family <- if (nchar(prefix)) prefix else CASE_LABEL

# Clustering is computed once and shared: raw -> norm -> comp differ only by a
# per-column rescaling, and correlation distance is scale-free, so all three
# produce the identical tree. The page draws the matrices itself (dark, in one
# row, with hover readout), so R only emits the numbers and the dendrogram.
hc  <- hclust(as.dist(1 - cor(comp)), method = "ward.D2")
ord <- hc$order

raw <- raw[, ord, drop = FALSE]
norm <- norm[, ord, drop = FALSE]
comp <- comp[, ord, drop = FALSE]

# hclust -> plottable segments, in leaf-position / height coordinates
hc_segments <- function(hc) {
  pos_of <- function(k) if (k < 0) which(hc$order == -k) else mx[k]
  h_of   <- function(k) if (k < 0) 0 else hc$height[k]
  mx <- numeric(nrow(hc$merge))
  segs <- list()
  for (i in seq_len(nrow(hc$merge))) {
    a <- hc$merge[i, 1]; b <- hc$merge[i, 2]
    xa <- pos_of(a); xb <- pos_of(b); h <- hc$height[i]
    mx[i] <- (xa + xb) / 2
    segs[[length(segs) + 1]] <- c(xa, h_of(a), xa, h)
    segs[[length(segs) + 1]] <- c(xb, h_of(b), xb, h)
    segs[[length(segs) + 1]] <- c(xa, h, xb, h)
  }
  m <- do.call(rbind, segs)
  colnames(m) <- c("x1", "y1", "x2", "y2")
  as.data.frame(m)
}

# xtabs results carry class "table", which jsonlite cannot serialise
as_plain <- function(x) matrix(as.numeric(x), nrow(x), ncol(x))

# --- literature names, straight from the maleCNS synonyms annotation ---------
syn_cache <- file.path(DERIVED, paste0(CASE, "_synonyms.rds"))
if (file.exists(syn_cache)) {
  alias_tbl <- readRDS(syn_cache)
} else {
  suppressMessages(library(malecns))
  alias_tbl <- mcns_body_annotations() %>%
    filter(type %in% TARGET_TYPES, !is.na(synonyms), nzchar(synonyms)) %>%
    distinct(type, synonyms)
  saveRDS(alias_tbl, syn_cache)
}

# entries look like "Yu 2010: vAB3" - the name after the colon, the citation before
TYPE_ALIAS <- setNames(trimws(sub("^[^:]*:", "", alias_tbl$synonyms)), alias_tbl$type)
ALIAS_CITE <- unique(trimws(sub(":.*$", "", alias_tbl$synonyms)))

fig_data <- list(
  rows = rownames(comp),
  cols = colnames(comp),
  family = family,
  alias  = alias_of(paste0(family, colnames(comp))),
  tree = list(segs = hc_segments(hc), maxh = max(hc$height)),
  panels = list(
    list(key = "raw",  title = "Raw synapse count",
         sub = "absolute wiring strength",
         unit = "syn", values = as_plain(raw)),
    list(key = "norm", title = "Fraction of total input",
         sub = "counting every source, not just these",
         unit = "pct", values = as_plain(norm)),
    list(key = "comp", title = "Composition",
         sub = "each column sums to 1",
         unit = "pct", values = as_plain(comp))
  )
)

fig_json <- jsonlite::toJSON(fig_data, auto_unbox = TRUE, digits = 6)

# --- T1 bilaterality of the TARGET neurons -----------------------------------
# An ascending neuron receives in the VNC, so its laterality is read off where its
# POSTsynapses sit: contra = the smaller of the two T1 leg neuropils divided by the
# total. 0 means every input synapse is on one side.
bilat_cache <- file.path(DERIVED, paste0(CASE, "_t1_bilaterality.rds"))
if (file.exists(bilat_cache)) {
  bilat <- readRDS(bilat_cache)
} else {
  suppressMessages({ library(neuprintr) })
  neuprint_login(server = MCNS_SERVER, dataset = MCNS_DATASET)
  ri <- neuprint_get_roiInfo(bodies$bodyid, dataset = MCNS_DATASET)
  z  <- function(v) if (is.null(v)) 0 else ifelse(is.na(v), 0, v)
  L  <- z(ri[["LegNp(T1)(L).post"]]); R <- z(ri[["LegNp(T1)(R).post"]])
  bilat <- data.frame(bodyid = ri$bodyid,
                      t1_minor = pmin(L, R), t1_major = pmax(L, R)) %>%
    mutate(contra = ifelse(t1_major > 0, t1_minor / (t1_minor + t1_major), NA_real_))
  saveRDS(bilat, bilat_cache)
}

per_body <- per_body %>% left_join(bilat, by = "bodyid")

# a type counts as unilateral only if every one of its bodies is
uni_types <- per_body %>%
  summarise(uni = all(contra < 0.01, na.rm = TRUE), .by = type) %>%
  filter(uni) %>% pull(type)

alias_types <- intersect(names(TYPE_ALIAS), TARGET_TYPES)
alias_note <- if (length(alias_types)) {
  sprintf(" <b>%s</b> %s recorded in the maleCNS <code>synonyms</code> annotation as %s (%s).",
          paste(alias_types, collapse = " and "),
          if (length(alias_types) > 1) "are" else "is",
          paste(unique(TYPE_ALIAS[alias_types]), collapse = ", "),
          paste(ALIAS_CITE, collapse = "; "))
} else ""

bilat_note <- if (length(uni_types)) {
  sprintf("Unilateral in T1: %s. All other types receive T1 input on both sides.",
          paste(uni_types, collapse = ", "))
} else {
  "Every type here receives T1 input on both sides."
}
bilat_note <- paste0(bilat_note, alias_note)

# external references declared by the case, e.g. driver-line imagery. On their own
# line rather than trailing the laterality sentence, where they were easy to miss.
case_links <- CASES[[CASE]]$links
if (length(case_links)) {
  bilat_note <- paste0(bilat_note,
    '</p><p class="note reflink">',
    paste(vapply(case_links, function(l)
      sprintf('<span class="reftag">ref</span><a href="%s" rel="noopener">%s</a> &ndash; %s.',
              l$url, l$label, l$note),
      character(1)), collapse = "<br>"))
}

# line imagery, hotlinked from the source bucket rather than copied into the site.
# Each one links through to the full-size file.
# --- embeddable 3d scene ------------------------------------------------------
# The representative body: the aliased type if the case has one (so the embed
# shows the neuron the literature name refers to), else the first target type.
# layout 3d with slices off, so the iframe opens on the morphology rather than
# on EM planes.
embed_cfg  <- CASES[[CASE]]$embed
embed_type <- if (length(alias_types)) alias_types[1] else TARGET_TYPES[1]
embed_body <- if (!is.null(embed_cfg$body)) embed_cfg$body else {
  syn %>% filter(target_type == embed_type, is_focus) %>%
    count(bodyid, sort = TRUE) %>% slice_head(n = 1) %>% pull(bodyid)
}
# a case may pin the camera, e.g. to match the orientation of a light-level panel
if (!is.null(embed_cfg$body)) {
  embed_type <- bodies$target_type[match(embed_cfg$body, bodies$bodyid)]
}

embed_url <- NULL
if (length(embed_body)) {
  es <- make_mcns_scene(embed_body, title = sprintf("%s %s", embed_type, embed_body))
  es$layers[[2]]$segments            <- as.list(as.character(embed_body))
  es$layers[[2]]$segmentDefaultColor <- "#ff0000"
  es$layers[[2]]$segmentColors       <- setNames(list("#ff0000"), as.character(embed_body))
  ep <- syn %>% filter(bodyid == embed_body, is_focus)
  es$position        <- if (!is.null(embed_cfg$position)) embed_cfg$position
                        else c(mean(ep$x), mean(ep$y), mean(ep$z))
  es$projectionScale <- if (!is.null(embed_cfg$scale)) embed_cfg$scale else fit_scale(ep)
  if (!is.null(embed_cfg$orientation)) es$projectionOrientation <- embed_cfg$orientation
  es$layout          <- list(type = "3d", orthographicProjection = TRUE)
  es$showSlices      <- FALSE
  es$showAxisLines   <- FALSE
  # the embed is for looking, not for driving: close every panel so the frame
  # opens on the neuron rather than on neuroglancer's chrome
  es$showScaleBar    <- FALSE
  es$showDefaultAnnotations <- FALSE
  es$selectedLayer   <- list(visible = FALSE)
  es$layerListPanel  <- list(visible = FALSE)
  es$selection       <- list(visible = FALSE)
  es$helpPanel       <- list(visible = FALSE)
  es$settingsPanel   <- list(visible = FALSE)
  embed_url <- write_scene(es, sprintf("%s_embed.json", CASE))
}

case_images <- CASES[[CASE]]$images
mcfo_html <- if (length(case_images)) {
  # Each panel is flexed in proportion to its displayed aspect ratio, so the row
  # fills the text column with every panel the same height. A rotated image keeps
  # its layout box unrotated, so the box carries the post-rotation aspect and the
  # image is absolutely centred inside it at the reciprocal width.
  paste0('<div class="mcfo">',
    paste(vapply(case_images, function(im) sprintf(
      '<figure><a href="%s" rel="noopener"><img src="%s" alt="%s" loading="lazy"></a><figcaption>%s</figcaption></figure>',
      im$url, im$url, im$cap, im$cap), character(1)), collapse = ""),
    '</div>')
} else ""

# a live Clio-NG viewer beside the fixed imagery, same row, same height, so the
# light-level morphology and the EM reconstruction can be compared directly
if (!is.null(embed_url)) {
  frame <- sprintf(
    '<figure><div class="box ngbox"><iframe src="%s" loading="lazy" allowfullscreen title="%s %s"></iframe><span class="mask tl"></span><span class="mask tr"></span></div><figcaption>%s %s, interactive. Same view as the VNC panel above. <a href="%s" rel="noopener">open full</a></figcaption></figure>',
    embed_url, embed_type, embed_body, embed_type, embed_body, embed_url)
  mcfo_html <- paste0(mcfo_html, '<div class="ngrow">', frame, '</div>')
}

# --- Billy's receptor assignment ---------------------------------------------
# Reproduced from Billy's figure. This is a light-level receptor-to-type call and
# is NOT derived from any connectivity on this page - it is shown so the two can
# be compared, and is labelled as his throughout.
BILLY <- list(
  list(tone = "m",    receptor = "ppk23+",        detects = "Males",
       group = "M cells", grouped = c("LgLG1a", "LgLG6", "LgLG7"), extra = "WG4"),
  list(tone = "both", receptor = "Ir52a+;Ir52b+<br>Gr33a+", detects = "Both",
       group = NA,        grouped = character(0),
       extra = c("LgLG2", "WG1", "LgAG1")),
  list(tone = "f",    receptor = "ppk23+;ppk25+", detects = "Females",
       group = "F cells", grouped = c("LgLG1b", "LgLG5", "LgLG8"), extra = "WG3")
)

# a type used by the current case is outlined, so the assignment connects to the
# rest of the page without the page adopting its claims
chip <- function(x) sprintf('<span class="ty%s">%s</span>',
                            ifelse(x %in% FOCUS, " used", ""), x)

billy_rows <- paste(vapply(BILLY, function(r) {
  types <- paste0(
    if (length(r$grouped))
      sprintf('<div class="grp"><div class="grp-items">%s</div><div class="grp-lbl">%s</div></div>',
              paste(vapply(r$grouped, chip, character(1)), collapse = ""), r$group)
    else "",
    paste(vapply(r$extra, chip, character(1)), collapse = ""))
  sprintf('<tr class="%s"><td class="rec"><i>%s</i></td><td class="det">%s</td><td>%s</td></tr>',
          r$tone, r$receptor, r$detects, types)
}, character(1)), collapse = "\n")

# --- menu page ---------------------------------------------------------------
# one column per focus type, so the table carries the same numbers as the figures
fc <- syn %>% filter(is_focus) %>% count(bodyid, partner_group) %>%
  xtabs(n ~ bodyid + partner_group, data = .)
for (tp in setdiff(FOCUS, colnames(fc))) fc <- cbind(fc, 0)
colnames(fc)[colnames(fc) == ""] <- setdiff(FOCUS, colnames(fc))
fc <- fc[, FOCUS, drop = FALSE]

thead <- paste0('<tr><th>Neuron</th><th>Side</th><th>T1 contra</th>',
                '<th>Input syn</th><th>Focus syn</th>',
                paste(sprintf("<th>%s</th>", FOCUS), collapse = ""), "</tr>")

rows <- paste(vapply(seq_len(nrow(per_body)), function(i) {
  b <- as.character(per_body$bodyid[i])
  v <- if (b %in% rownames(fc)) as.integer(fc[b, ]) else rep(0L, length(FOCUS))
  paste0("<tr>",
         sprintf('<td><a href="%s">%s %s</a>%s</td>', per_body$url[i],
                 per_body$type[i], per_body$bodyid[i],
                 ifelse(nzchar(alias_of(per_body$type[i])),
                        sprintf(' <span class="alias">%s</span>',
                                alias_of(per_body$type[i])), "")),
         sprintf("<td>%s</td>", per_body$soma_side[i]),
         sprintf("<td>%s</td>", ifelse(is.na(per_body$contra[i]), "-",
                                       sprintf("%.0f%%", 100 * per_body$contra[i]))),
         sprintf("<td>%d</td>", per_body$n_syn[i]),
         sprintf("<td>%d</td>", per_body$n_focus[i]),
         paste(sprintf("<td>%d</td>", v), collapse = ""),
         "</tr>")
}, character(1)), collapse = "\n")

# built from focus_cols so the legend cannot drift from the scene colours
legend <- paste(sprintf(
  '<li><span class="sw" style="background:%s"></span>%s</li>',
  unname(focus_cols), names(focus_cols)), collapse = "\n")

# optional sections, assembled here so a case can leave them out entirely
figs_section <- if (SHOW_FIGURES) {
  sprintf('<h2>Input structure</h2>
<p class="note">The same synapses as the scenes, collapsed to type level and
clustered on the target axis. Correlation distance, Ward.D2 linkage. The three
panels differ only by a per-column rescaling, and correlation is scale-free, so
they share one dendrogram, and only the colour scale changes. Hover a cell for
the exact value.</p>

<div id="figs" class="figs"></div>
<p class="note" style="margin-top:.6rem">%s</p>
<script id="figdata" type="application/json">%s</script>
', bilat_note, fig_json)
} else {
  sprintf('<p class="note">%s</p>', bilat_note)
}

figs_section <- paste0(figs_section, mcfo_html)

billy_section <- if (SHOW_BILLY) sprintf('<h2>Receptor assignment</h2>
<p class="note"><b>Billy&rsquo;s assignment, reproduced here.</b> This is a
light-level receptor-to-type call and is not derived from any of the
connectivity on this page. Types outlined below are the ones used as focus
inputs here; the rest are shown for completeness.</p>

<table class="billy">
<tr><th>Receptor</th><th>Detects</th><th>mCNS type</th></tr>
%s
</table>
', billy_rows) else ""

html_head <- sprintf('<!doctype html>
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
 th,td{text-align:left;padding:.45rem .6rem;border-bottom:1px solid #ececec;
       white-space:nowrap}
 th{font-weight:600;color:#555;font-size:.85rem;text-transform:uppercase;
    letter-spacing:.03em}
 th:nth-child(n+3),td:nth-child(n+3){text-align:right;font-variant-numeric:tabular-nums}
 .legend{margin:1.25rem 0 0;padding:0;list-style:none;font-size:.85rem;
         display:flex;flex-wrap:wrap;gap:.35rem 1.1rem;align-items:center}
 .legend li{margin:0;white-space:nowrap}
 .legend .bi{color:#666;font-size:.85rem}
 h2{font-size:1.05rem;margin:2.75rem 0 .35rem;font-weight:600}
 p.note{color:#555;margin:0 0 1.25rem;font-size:.92rem}
 p.reflink{margin-top:.5rem}
 .mcfo{display:flex;gap:.7rem;align-items:flex-start;justify-content:center;
        flex-wrap:wrap;margin:.5rem 0 1.3rem}
 .mcfo figure{margin:0}
 .mcfo img{display:block;height:190px;width:auto;max-width:100%%;
           background:#000;border:0;border-radius:7px}
 .mcfo figcaption{color:#666;font-size:.72rem;margin-top:.3rem;line-height:1.3;
                  max-width:22rem}
 @media (prefers-color-scheme:dark){
  .mcfo figcaption{color:#9aa3b0}
 }
 .ngrow{margin:0 0 1.6rem}
 .ngrow figure{margin:0}
 .ngrow .box{position:relative;width:100%%;height:440px;overflow:hidden;
             background:#000;border:0;border-radius:7px}
 /* The frame is laid out at twice the visible size and scaled back down, so
    neuroglancer renders into twice as many pixels and the result stays sharp.
    It is also grown past the layer bar height and pulled up, letting the box
    overflow clip the bar: Clio-NG keeps it whatever the state says, and a
    cross-origin frame cannot be restyled from here. */
 /* the frame also overhangs the box by 6px on the other three sides, so the
    focus ring the browser draws on click falls outside the clipped area:
    outline:none does not reach a ring drawn inside a cross-origin frame */
 .ngrow .box iframe{position:absolute;left:-6px;top:-48px;
                    width:calc(200%% + 24px);height:calc(200%% + 120px);
                    transform:scale(.5);transform-origin:0 0;
                    z-index:1;border:0;display:block;outline:none}
 /* clicking an iframe focuses it and the browser draws a focus ring, which is
    the pale outline that appears around the viewer on click or hover */
 .ngrow .box iframe:focus,.ngrow .box iframe:focus-visible{outline:none}
 .ngrow .box:focus-within{outline:none}
 /* the axis letters and the panel toggle survive every state flag, so they are
    covered by patches in matching black */
 /* z-index is required: the transform on the iframe promotes it to its own
    compositing layer, which otherwise paints over anything later in the DOM */
 .ngrow .box .mask{position:absolute;z-index:2;background:#000;pointer-events:none}
 .ngrow .box .mask.tl{left:0;top:0;width:30px;height:58px}
 .ngrow .box .mask.tr{right:0;top:0;width:36px;height:32px}
 .ngrow figcaption{color:#666;font-size:.75rem;margin-top:.35rem}
 @media (prefers-color-scheme:dark){
  .ngrow figcaption{color:#9aa3b0}
 }
 .reftag{display:inline-block;margin-right:.45rem;padding:0 .35rem;border-radius:4px;
         background:#0b5fa5;color:#fff;font-size:.68rem;font-weight:600;
         text-transform:uppercase;letter-spacing:.04em;vertical-align:1px}
 /* the plots keep their own dark ground in both colour schemes, to match the
    neuroglancer scenes they describe */
 .figs{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;
       background:#0b0e13;border-radius:11px;padding:1.4rem 1.2rem;justify-items:center;
       width:min(1180px,94vw);position:relative;left:50%%;transform:translateX(-50%%)}
 @media (max-width:820px){.figs{grid-template-columns:1fr}}
 .pnl{width:100%%}
 .pnl h3{margin:0 0 .1rem;font-size:.9rem;font-weight:600;color:#e8edf4}
 .pnl p{margin:0 0 .6rem;font-size:.76rem;color:#8b95a5}
 .pnl{display:flex;flex-direction:column;align-items:center;text-align:center}
 .pnl svg{display:block;width:100%%;height:auto;overflow:visible}
 #scenes th{cursor:pointer;user-select:none}
 #scenes th:hover{color:#0b5fa5}
 #scenes th.sorted::after{content:" \\2195";font-size:.8em;opacity:.6}
 .pnl .cell{stroke:#0b0e13;stroke-width:1}
 .pnl .cell:hover{stroke:#fff;stroke-width:1.5}
 .lbl{fill:#c3cbd8;font:10px system-ui,sans-serif}
 .lbl.dim{fill:#7d8798}
 .lbl.alias-lbl{fill:#ffd166;font-weight:600}
 .lbl.sm{font-size:8px;font-weight:400}
 .alias{display:inline-block;margin-left:.35rem;padding:0 .3rem;border-radius:4px;
        background:#ffd166;color:#3a2f00;font-size:.72rem;font-weight:600;
        vertical-align:1px}
 .tree{stroke:#5b6675;fill:none;stroke-width:1}
 #tip{position:fixed;pointer-events:none;background:#161b22;color:#e8edf4;
      border:1px solid #30363d;border-radius:6px;padding:.3rem .5rem;
      font:12px system-ui,sans-serif;opacity:0;transition:opacity .1s;z-index:9}
 table.billy{border-collapse:collapse;width:auto;max-width:26rem;
             margin:.25rem 0 .5rem;font-size:.8rem}
 table.billy th{font-size:.68rem;padding:.2rem .55rem;letter-spacing:.02em}
 table.billy td{padding:.3rem .55rem;border-bottom:1px solid rgba(0,0,0,.1);
                vertical-align:middle;white-space:normal;line-height:1.35}
 table.billy tr.m    td{background:#fbf6cf}
 table.billy tr.both td{background:#f6efd6}
 table.billy tr.f    td{background:#f7dfe3}
 table.billy .rec,table.billy .det{color:#2b2b2b;text-align:left;font-size:.8rem}
 .ty{display:block;font-size:.78rem;color:#2b2b2b;line-height:1.45;
      padding-left:.4rem;box-shadow:inset 2px 0 0 transparent}
 .ty.used{font-weight:700;box-shadow:inset 2px 0 0 #0b5fa5}
 .grp{border:1px dashed #9a9a9a;border-radius:4px;padding:.12rem .3rem;
      margin-bottom:.15rem;display:flex;align-items:center;gap:.4rem}
 .grp-lbl{font-size:.7rem;color:#555;white-space:nowrap}
 @media (prefers-color-scheme:dark){
  table.billy td{border-bottom-color:rgba(255,255,255,.1)}
 }
 .sw{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;
     margin-right:.35rem;vertical-align:-1px}
 @media (prefers-color-scheme:dark){
  body{background:#141414;color:#e8e8e8}
  a{color:#6fb3ef} .big{border-color:#333} .big b{color:#6fb3ef}
  .big:hover{border-color:#6fb3ef;background:#1b2430}
  th,td{border-bottom-color:#2a2a2a} th,.legend,p.sub{color:#aaa}
  p.note{color:#c2c8d2}
  /* the page is already dark, so the figures need no card of their own -
     without this the panel ground reads as a second, slightly different black */
  .figs{background:transparent;padding-left:0;padding-right:0}
  .pnl .cell{stroke:#141414}
 }
</style>',
  CASE_LABEL)

html_body <- sprintf('
<h1>%s sensory input</h1>
<p class="sub">Clio-NG scenes for the male CNS (male-cns:v1.0). The neuron is red;
input synapses are point annotations, one layer per presynaptic sensory type.
All of this input lands in the nerve cord. Extra layers start hidden; toggle
them in the layer bar.</p>

<a class="big" href="%s">
  <b>Overview: all %d bodies</b><br>
  One colour per target type, with every sensory input synapse from the focus
  types overlaid.
</a>

%s%s

<h2>Scenes</h2>

<table id="scenes">
<thead>%s</thead>
<tbody>
%s
</tbody>
</table>
<p class="note" style="margin-top:.5rem">Click a column header to sort.</p>

<ul class="legend">
%s
</ul>

',
  CASE_LABEL, overview_url, nrow(per_body), figs_section, billy_section,
  thead, rows, legend)

# not passed through sprintf: the whole thing exceeds sprintf's 8192-char
# format limit, and the script needs its per-cent signs unescaped anyway
html_js <- '<div id="tip"></div>
<script>
(function () {
  var dataEl = document.getElementById("figdata");
  var D = dataEl ? JSON.parse(dataEl.textContent) : null;
  var NS = "http://www.w3.org/2000/svg";
  // CW == CH so the cells stay square at any rendered size: the viewBox scales
  // uniformly, so a square here is a square on screen
  var CW = 30, CH = 30, TREE = 30, PADL = 8, PADT = 4, LBLW = 46, LBLH = 28;

  // viridis, sampled - reads well on a dark ground at both ends
  var RAMP = ["#440154","#472d7b","#3b528b","#2c728e","#21918c",
              "#28ae80","#5ec962","#addc30","#fde725"];
  function lerp(a, b, t) { return a + (b - a) * t; }
  function hex(c) { return [parseInt(c.substr(1,2),16), parseInt(c.substr(3,2),16), parseInt(c.substr(5,2),16)]; }
  function colour(t) {
    if (!(t > 0)) return "#12161d";                 // exact zero reads as ground
    var i = Math.min(RAMP.length - 2, Math.floor(t * (RAMP.length - 1)));
    var f = t * (RAMP.length - 1) - i, a = hex(RAMP[i]), b = hex(RAMP[i + 1]);
    return "rgb(" + Math.round(lerp(a[0],b[0],f)) + "," + Math.round(lerp(a[1],b[1],f)) +
           "," + Math.round(lerp(a[2],b[2],f)) + ")";
  }

  var tip = document.getElementById("tip");
  function el(n, at) { var e = document.createElementNS(NS, n);
    for (var k in at) e.setAttribute(k, at[k]); return e; }

  function fmt(v, unit) {
    return unit === "pct" ? (100 * v).toFixed(v < 0.1 ? 1 : 0) + "%" : Math.round(v) + " syn";
  }

  // click-to-sort. Numeric columns sort numerically, text columns alphabetically;
  // "24%" and "1,191" both parse, and a non-numeric cell falls back to text.
  var tbl = document.getElementById("scenes");
  if (tbl) {
    var dir = {};
    tbl.querySelectorAll("th").forEach(function (th, idx) {
      th.addEventListener("click", function () {
        var body = tbl.tBodies[0];
        var rws = Array.prototype.slice.call(body.rows);
        dir[idx] = -(dir[idx] || 1);
        var num = rws.every(function (r) {
          var t = r.cells[idx].textContent.replace(/[%,]/g, "").trim();
          return t === "-" || t === "" || !isNaN(parseFloat(t));
        });
        rws.sort(function (a, b) {
          var x = a.cells[idx].textContent.trim(), y = b.cells[idx].textContent.trim();
          if (num) {
            var nx = parseFloat(x.replace(/[%,]/g, "")) || 0;
            var ny = parseFloat(y.replace(/[%,]/g, "")) || 0;
            return (nx - ny) * dir[idx];
          }
          return x.localeCompare(y) * dir[idx];
        });
        rws.forEach(function (r) { body.appendChild(r); });
        tbl.querySelectorAll("th").forEach(function (o) { o.classList.remove("sorted"); });
        th.classList.add("sorted");
      });
    });
  }

  if (D) D.panels.forEach(function (P) {
    var nr = D.rows.length, nc = D.cols.length;
    var W = LBLW + nc * CW + PADL, H = TREE + nr * CH + LBLH + PADT;
    var wrap = document.createElement("div");
    wrap.className = "pnl";
    wrap.innerHTML = "<h3>" + P.title + "</h3><p>" + P.sub + "</p>";
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H });

    // shared dendrogram, scaled into the TREE band
    D.tree.segs.forEach(function (s) {
      var sx = function (x) { return LBLW + (x - 0.5) * CW; };
      var sy = function (y) { return TREE - (y / D.tree.maxh) * (TREE - 4) + PADT; };
      svg.appendChild(el("line", { x1: sx(s.x1), y1: sy(s.y1), x2: sx(s.x2), y2: sy(s.y2),
                                   "class": "tree" }));
    });

    // cells - each panel scaled to its own maximum, since the units differ
    var max = 0;
    P.values.forEach(function (r) { r.forEach(function (v) { if (v > max) max = v; }); });
    P.values.forEach(function (row, i) {
      row.forEach(function (v, j) {
        var c = el("rect", { x: LBLW + j * CW, y: TREE + PADT + i * CH,
                             width: CW, height: CH, "class": "cell", fill: colour(v / max) });
        c.addEventListener("mousemove", function (e) {
          var al = D.alias && D.alias[j] ? " (" + D.alias[j] + ")" : "";
          tip.textContent = D.rows[i] + " \u2192 " + D.family + D.cols[j] + al + "  " + fmt(v, P.unit);
          tip.style.opacity = 1;
          tip.style.left = (e.clientX + 12) + "px";
          tip.style.top  = (e.clientY + 12) + "px";
        });
        c.addEventListener("mouseleave", function () { tip.style.opacity = 0; });
        svg.appendChild(c);
      });
    });

    D.rows.forEach(function (r, i) {
      svg.appendChild(el("text", { x: LBLW - 6, y: TREE + PADT + i * CH + CH / 2 + 3.5,
                                   "text-anchor": "end", "class": "lbl" })).textContent = r;
    });
    D.cols.forEach(function (c, j) {
      var al = D.alias && D.alias[j];
      svg.appendChild(el("text", { x: LBLW + j * CW + CW / 2, y: TREE + PADT + nr * CH + 12,
                                   "text-anchor": "middle",
                                   "class": al ? "lbl alias-lbl" : "lbl dim" })).textContent = c;
      if (al) {
        svg.appendChild(el("text", { x: LBLW + j * CW + CW / 2, y: TREE + PADT + nr * CH + 22,
                                     "text-anchor": "middle", "class": "lbl alias-lbl sm" }))
           .textContent = al;
      }
    });

    wrap.appendChild(svg);
    document.getElementById("figs").appendChild(wrap);
  });
})();
</script>'

html <- paste0(html_head, html_body, html_js)

dir.create(file.path(ng_dir, CASE), showWarnings = FALSE)
write(html, file.path(ng_dir, CASE, "index.html"))

write.csv(per_body, file.path(DERIVED, paste0(CASE, "_neuroglancer_scenes.csv")),
          row.names = FALSE)
cat("\nmenu:    ", file.path(ng_dir, CASE, "index.html"), "\n")
cat("overview:", overview_url, "\n")
