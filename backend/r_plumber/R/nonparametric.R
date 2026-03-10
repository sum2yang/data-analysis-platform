handle_kruskal_wallis <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(group_col) || !(group_col %in% names(df)))
    stop("params.group_column is required")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  df[[group_col]] <- as.factor(as.character(df[[group_col]]))
  complete <- stats::complete.cases(df[, c(response_col, group_col)])
  df <- df[complete, , drop = FALSE]

  test <- stats::kruskal.test(stats::as.formula(paste(response_col, "~", group_col)), data = df)

  # Dunn post-hoc (pairwise Wilcoxon with BH correction)
  levs <- levels(df[[group_col]])
  split_vals <- split(df[[response_col]], df[[group_col]])
  pairs <- utils::combn(levs, 2, simplify = FALSE)
  posthoc <- list()
  p_vals <- numeric(length(pairs))
  for (idx in seq_along(pairs)) {
    a <- pairs[[idx]][1]
    b <- pairs[[idx]][2]
    pw <- suppressWarnings(stats::wilcox.test(split_vals[[a]], split_vals[[b]]))
    p_vals[idx] <- pw$p.value
    posthoc[[idx]] <- list(comparison = paste0(a, "-", b), p_value = pw$p.value)
  }
  p_adj <- stats::p.adjust(p_vals, method = "BH")
  for (idx in seq_along(posthoc)) posthoc[[idx]]$p_adj <- p_adj[idx]

  group_summary <- lapply(names(split_vals), function(g) {
    compute_group_stats(split_vals[[g]], label = g)
  })

  build_response(
    "kruskal_wallis",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      n_groups = as.integer(length(levs))
    ),
    tables = list(
      kruskal_wallis = list(
        statistic = safe_num(test$statistic),
        df = safe_num(test$parameter),
        p_value = as.numeric(test$p.value)
      ),
      group_summary = group_summary,
      posthoc = posthoc
    )
  )
}

handle_mann_whitney <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column
  alternative <- if (is.null(params$alternative)) "two.sided"
                 else gsub("-|_", ".", tolower(params$alternative))

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(group_col) || !(group_col %in% names(df)))
    stop("params.group_column is required")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  g <- as.character(df[[group_col]])
  levs <- unique(g[!is.na(g)])
  if (length(levs) != 2) stop("Mann-Whitney U test requires exactly 2 groups")

  x <- df[[response_col]][g == levs[1]]
  y <- df[[response_col]][g == levs[2]]
  x <- x[!is.na(x)]
  y <- y[!is.na(y)]

  test <- suppressWarnings(stats::wilcox.test(x, y, alternative = alternative, exact = FALSE))

  build_response(
    "mann_whitney",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      groups = as.list(levs),
      alternative = alternative,
      n_x = as.integer(length(x)),
      n_y = as.integer(length(y))
    ),
    tables = list(
      mann_whitney = list(
        statistic = safe_num(test$statistic),
        p_value = as.numeric(test$p.value),
        method = as.character(test$method)
      )
    )
  )
}
