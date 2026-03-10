#* Descriptive statistics (grouped)
#* @post /descriptive
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column"))

    response_col <- as.character(params$response_column)
    group_col <- if (!is.null(params$group_column)) as.character(params$group_column) else NULL
    validate_columns(df, response_col)

    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))

    compute_stats <- function(x, label = "all") {
      x <- x[!is.na(x)]
      n <- length(x)
      list(
        group = label,
        n = n,
        mean = if (n > 0) mean(x) else NA,
        sd = if (n > 1) stats::sd(x) else NA,
        se = if (n > 1) stats::sd(x) / sqrt(n) else NA,
        median = if (n > 0) stats::median(x) else NA,
        min = if (n > 0) min(x) else NA,
        max = if (n > 0) max(x) else NA,
        q1 = if (n > 0) unname(stats::quantile(x, 0.25)) else NA,
        q3 = if (n > 0) unname(stats::quantile(x, 0.75)) else NA,
        iqr = if (n > 0) unname(stats::IQR(x)) else NA,
        cv = if (n > 1 && mean(x) != 0) stats::sd(x) / abs(mean(x)) * 100 else NA,
        skewness = if (n >= 3) {
          m3 <- mean((x - mean(x))^3)
          s3 <- stats::sd(x)^3
          if (s3 > 0) m3 / s3 else NA
        } else NA,
        kurtosis = if (n >= 4) {
          m4 <- mean((x - mean(x))^4)
          s4 <- stats::sd(x)^4
          if (s4 > 0) m4 / s4 - 3 else NA
        } else NA,
        missing = sum(is.na(df[[response_col]]))
      )
    }

    if (!is.null(group_col)) {
      validate_columns(df, group_col)
      df[[group_col]] <- as.character(df[[group_col]])
      groups <- split(df[[response_col]], df[[group_col]])
      stats_rows <- lapply(names(groups), function(g) compute_stats(groups[[g]], g))
    } else {
      stats_rows <- list(compute_stats(df[[response_col]]))
    }

    build_response(
      analysis_type = "descriptive",
      summary = list(
        response_column = response_col,
        group_column = group_col,
        n_groups = length(stats_rows)
      ),
      tables = list(descriptive = stats_rows)
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}
