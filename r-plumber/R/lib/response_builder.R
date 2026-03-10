build_response <- function(analysis_type,
                           summary = list(),
                           tables = list(),
                           assumptions = list(),
                           warnings = list(),
                           chart_contracts = list()) {
  list(
    analysis_type = analysis_type,
    engine = "R",
    summary = summary,
    tables = tables,
    assumptions = assumptions,
    warnings = as.list(warnings),
    chart_contracts = as.list(chart_contracts)
  )
}

safe_num <- function(x) {
  if (is.null(x) || length(x) == 0) return(NA_real_)
  val <- suppressWarnings(as.numeric(x[[1]]))
  if (is.nan(val) || is.infinite(val)) return(NA_real_)
  val
}

df_to_records <- function(df) {
  if (is.null(df) || nrow(df) == 0) return(list())
  lapply(seq_len(nrow(df)), function(i) as.list(df[i, , drop = FALSE]))
}
