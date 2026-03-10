handle_assumptions <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(group_col) || !(group_col %in% names(df)))
    stop("params.group_column is required")

  y <- suppressWarnings(as.numeric(df[[response_col]]))
  g <- as.character(df[[group_col]])

  complete <- stats::complete.cases(y, g)
  y_clean <- y[complete]
  g_clean <- as.factor(g[complete])

  if (length(y_clean) < 3) stop("Not enough complete rows for assumption checks")

  # Outlier detection (IQR method)
  bx <- grDevices::boxplot.stats(y_clean)
  outlier_count <- length(bx$out)
  outlier_values <- as.list(as.numeric(bx$out))

  # Shapiro-Wilk per group
  split_vals <- split(y_clean, g_clean)
  shapiro_by_group <- lapply(names(split_vals), function(grp) {
    c(list(group = grp), safe_shapiro(split_vals[[grp]]))
  })

  # Bartlett test
  bart <- stats::bartlett.test(y_clean ~ g_clean)

  # Levene test
  warns <- list()
  levene_out <- NULL
  if (requireNamespace("car", quietly = TRUE)) {
    lev <- car::leveneTest(y_clean, g_clean)
    levene_out <- list(
      statistic = if ("F value" %in% colnames(lev)) safe_num(lev[1, "F value"]) else NA,
      p_value = if ("Pr(>F)" %in% colnames(lev)) safe_num(lev[1, "Pr(>F)"]) else NA,
      df1 = safe_num(lev[1, "Df"]),
      df2 = safe_num(lev[2, "Df"])
    )
  } else {
    warns <- c(warns, "Package 'car' not installed; Levene test skipped.")
    levene_out <- list(statistic = NA, p_value = NA, note = "car package not available")
  }

  build_response(
    "assumption_checks",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      n_rows_complete = as.integer(sum(complete)),
      n_rows_total = as.integer(nrow(df)),
      n_groups = as.integer(length(unique(g_clean)))
    ),
    tables = list(
      outlier_summary = list(count = outlier_count, values = outlier_values)
    ),
    assumptions = list(
      shapiro_by_group = shapiro_by_group,
      levene = levene_out,
      bartlett = list(
        test = "Bartlett",
        statistic = safe_num(bart$statistic),
        df = safe_num(bart$parameter),
        p_value = as.numeric(bart$p.value)
      )
    ),
    warnings = warns
  )
}
