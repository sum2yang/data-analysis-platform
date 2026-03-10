# Shared helper functions for R Plumber analysis endpoints

parse_body <- function(req) {
  jsonlite::fromJSON(req$postBody, simplifyVector = TRUE)
}

parse_data <- function(body) {
  if (!is.null(body$data)) {
    return(as.data.frame(body$data, stringsAsFactors = FALSE))
  }
  if (!is.null(body$manifest)) {
    return(utils::read.csv(body$manifest$path, stringsAsFactors = FALSE))
  }
  stop("No data or manifest provided in request body")
}

build_response <- function(analysis_type,
                           summary = list(),
                           tables = list(),
                           assumptions = NULL,
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
  as.numeric(x[[1]])
}

safe_shapiro <- function(x) {
  x <- x[!is.na(x)]
  n <- length(x)
  if (n < 3 || n > 5000) {
    return(list(n = n, statistic = NA, p_value = NA,
                note = "Shapiro requires 3-5000 non-missing values"))
  }
  res <- stats::shapiro.test(x)
  list(n = n, statistic = unname(res$statistic), p_value = res$p.value, note = NULL)
}

compute_group_stats <- function(x, label = "all") {
  x <- x[!is.na(x)]
  n <- length(x)
  if (n == 0) {
    return(list(group = label, n = 0L, mean = NA, sd = NA, se = NA,
                median = NA, min = NA, max = NA, q1 = NA, q3 = NA,
                iqr = NA, cv = NA, skewness = NA, kurtosis = NA, missing = 0L))
  }
  m <- mean(x)
  s <- if (n > 1) stats::sd(x) else NA
  se <- if (n > 1) s / sqrt(n) else NA
  qs <- stats::quantile(x, probs = c(0.25, 0.75), na.rm = TRUE, names = FALSE)
  iqr_val <- unname(stats::IQR(x))
  cv <- if (n > 1 && m != 0) s / abs(m) * 100 else NA

  skew <- NA
  kurt <- NA
  if (n >= 3) {
    z <- (x - m) / s
    skew <- sum(z^3) / n
    kurt <- sum(z^4) / n - 3
  }

  list(
    group = label, n = as.integer(n),
    mean = m, sd = s, se = se,
    median = stats::median(x),
    min = min(x), max = max(x),
    q1 = qs[1], q3 = qs[2], iqr = iqr_val,
    cv = cv, skewness = skew, kurtosis = kurt,
    missing = 0L
  )
}
