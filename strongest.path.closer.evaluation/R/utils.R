# Utility Functions for Path Analysis
# Contains helper functions used across the analysis

#' Check if file exists; if not, signal to execute code
#' @param path File path to check
#' @return TRUE if file doesn't exist (execute), FALSE if it exists (load)
load_or_execute <- function(path) {
  if (file.exists(path)) {
    file.exists(path)
    FALSE
  } else {
    TRUE
  }
}

#' Column-normalize a matrix
#' @param A Matrix to normalize
#' @param na.rm Remove NA values
#' @return Column-normalized matrix
colScale <- function(A, na.rm = TRUE) {
  scalefac <- 1 / Matrix::colSums(A)
  if (na.rm) scalefac[!is.finite(scalefac)] <- 0
  A %*% Matrix::Diagonal(x = scalefac)
}

#' Row-normalize a matrix
#' @param A Matrix to normalize
#' @param na.rm Remove NA values
#' @return Row-normalized matrix
rowScale <- function(A, na.rm = TRUE) {
  scalefac <- 1 / Matrix::rowSums(A)
  if (na.rm) scalefac[!is.finite(scalefac)] <- 0
  Matrix::Diagonal(x = scalefac) %*% A
}

#' Add column prefix to dataframe
#' @param df Dataframe
#' @param prefix Prefix to add
#' @return Dataframe with prefixed column names
prefix_cols <- function(df, prefix) {
  names(df) <- paste0(prefix, "_", names(df))
  df
}

#' Make color gradient
#' @param col1 First color
#' @param col2 Second color
#' @param n Number of colors
#' @return Vector of colors
make_gradient <- function(col1, col2, n) {
  colorRampPalette(c(col1, col2))(n)
}

#' Get body IDs for a type string
#' @param type_string Type string to search for
#' @return Vector of body IDs
get.body.ids <- function(type_string){
  mba %>%
    filter(grepl(type_string, type, ignore.case = TRUE)) %>%
    pull(bodyid) %>%
    unique()
}
