suppressMessages({ 
  library(neuprintr); 
  library(malecns); 
  library(nat); 
  library(coconatfly);
  library(coconat); 
  library(malecns);
  options(malecns.dataset = "male-cns:v1.0")   # malecns helpers ignore MCNS_DATASET
  library(fafbseg)
  library(bancr);
  library(dplyr);
  library(tibble);
  library(igraph);
  library(pheatmap);
  library(RColorBrewer);
  library(viridisLite)
})
options(rgl.useNULL = TRUE)   # rgl cannot init headless on this machine

source("/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R")
neuprint_login(server = MCNS_SERVER, dataset = MCNS_DATASET)

load_once <- function(name, expr, envir = .GlobalEnv) {
  if (!exists(name, envir = envir, inherits = FALSE)) {
    assign(name, eval(expr), envir = envir)
  }
  get(name, envir = envir)
}

fct <- load_once("fct", quote(banc_edgelist(source = 'cave')))
mba <- load_once("mba", quote(mcns_body_annotations()))
fba <- load_once("fba", quote(banc_codex_annotations()))

contact_pool <- mba |>
  filter(class == "gustatory",
         superclass == "vnc_sensory",
         !is.na(type),
         subclass %in% c("leg bristle", "wing bristle")) |>
  pull(bodyid)


contact2ans <- mcns_connection_table(contact_pool, 'o')

post_in_conn <- load_once("post_in_conn", quote(
  mcns_connection_table(unique(contact2ans$partner), 'i') |>
    summarise(post_total_in = sum(weight), .by = bodyid)
))

sn_an <- contact2ans |>
  rename(post_type = type) |>
  left_join(mba |> select(bodyid, pre_type = type), by = "bodyid") |>
  filter(!post_type %in% pre_type) |>
  left_join(post_in_conn, by = c("partner" = "bodyid")) |>
  mutate(post_total_in = sum(distinct(pick(partner, post_total_in))$post_total_in, na.rm = TRUE),
         .by = post_type) |>
  summarise(weight     = sum(weight),
            norm_input = sum(weight) / first(post_total_in),
            n_pre      = n_distinct(bodyid),
            n_post     = n_distinct(partner),
            .by        = c(pre_type, post_type)) |>
  arrange(desc(weight))


MIN_WEIGHT <- 500   # a post type needs this many synapses from the pool in total

m <- sn_an |>
  filter(sum(weight) >= MIN_WEIGHT, .by = post_type) |>
  xtabs(norm_input ~ pre_type + post_type, data = _)

# --- column blocks by family (type name minus its trailing letter) ----------
fam   <- sub("_?[a-z]$", "", colnames(m))
multi <- sort(names(which(table(fam) > 1)))
blk   <- factor(ifelse(fam %in% multi, fam, "other"), levels = c(multi, "other"))

m <- m[, order(blk, colnames(m)), drop = FALSE]

# recompute after the reorder - colouring with the pre-reorder vector would put
# every colour on the wrong column
fam <- sub("_?[a-z]$", "", colnames(m))
blk <- factor(ifelse(fam %in% multi, fam, "other"), levels = c(multi, "other"))

pal     <- setNames(brewer.pal(max(3, length(multi)), "Set1")[seq_along(multi)], multi)
lab_col <- ifelse(fam %in% multi, pal[fam], "grey35")
gaps    <- head(cumsum(rle(as.character(blk))$lengths), -1)

# pheatmap has no option for coloured tick labels, and angle_col only accepts
# 0/45/90/270/315 - so the col_names grob is recoloured and rotated after the
# fact, hence silent = TRUE plus an explicit grid.draw
draw_hm <- function(mat, title) {
  ph <- pheatmap(mat, color = viridis(100),
                 cluster_rows = FALSE, cluster_cols = T,
                 gaps_col = gaps, border_color = NA,
                 cellwidth = 10, cellheight = 10,
                 fontsize_row = 10, fontsize_col = 9,
                 main = title, silent = TRUE)
  g <- ph$gtable
  i <- which(g$layout$name == "col_names")
  g$grobs[[i]]$gp$col <- lab_col
  g$grobs[[i]]$rot    <- 90
  g$grobs[[i]]$hjust  <- 1
  g$grobs[[i]]$vjust  <- 1
  grid::grid.newpage(); grid::grid.draw(g)
}

draw_hm(m, "Sensory input onto downstream types (fraction of each type's total input)")

# margin 2 now that post types are columns, so each COLUMN still sums to 1
draw_hm(prop.table(m, 2), "Sensory input composition (each column sums to 1)")

