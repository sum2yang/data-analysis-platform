#* Assumption checks (normality, homogeneity, outliers)
#* @post /assumptions
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    prep <- prepare_grouped_data(body)
    df_raw <- prep$df_raw
    df <- prep$df
    response_col <- prep$response_col
    group_col <- prep$group_col

    if (nrow(df) < 3) stop("Not enough complete rows for assumption checks")

    assumptions <- run_assumptions(df, response_col, group_col)

    bart <- stats::bartlett.test(
      stats::as.formula(paste(response_col, "~", group_col)), data = df
    )
    assumptions$bartlett <- list(
      test = "Bartlett",
      statistic = safe_num(bart$statistic),
      df = safe_num(bart$parameter),
      p_value = as.numeric(bart$p.value)
    )

    y_vals <- df[[response_col]]
    outlier_vals <- grDevices::boxplot.stats(y_vals)$out
    outlier_count <- length(outlier_vals)

    build_response(
      analysis_type = "assumption_checks",
      summary = list(
        response_column = response_col,
        group_column = group_col,
        n_rows_complete = nrow(df),
        n_rows_total = nrow(df_raw),
        n_groups = length(unique(df[[group_col]]))
      ),
      tables = list(
        outlier_summary = list(
          count = outlier_count,
          values = as.list(as.numeric(outlier_vals))
        )
      ),
      assumptions = assumptions
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}
