handle_descriptive <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required and must exist in data")

  y <- suppressWarnings(as.numeric(df[[response_col]]))
  missing_total <- sum(is.na(y))

  rows <- list()
  if (!is.null(group_col) && group_col %in% names(df)) {
    g <- as.character(df[[group_col]])
    split_vals <- split(y, g)
    for (gname in names(split_vals)) {
      row <- compute_group_stats(split_vals[[gname]], label = gname)
      row$missing <- as.integer(sum(is.na(df[[response_col]][g == gname])))
      rows <- c(rows, list(row))
    }
    n_groups <- length(split_vals)
  } else {
    row <- compute_group_stats(y, label = "all")
    row$missing <- as.integer(missing_total)
    rows <- list(row)
    n_groups <- 1L
    group_col <- NULL
  }

  build_response(
    "descriptive",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      n_groups = n_groups
    ),
    tables = list(descriptive = rows)
  )
}
