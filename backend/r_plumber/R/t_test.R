handle_t_test <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column
  test_type <- if (is.null(params$test_type)) "independent" else tolower(params$test_type)
  alternative <- if (is.null(params$alternative)) "two.sided"
                 else gsub("-|_", ".", tolower(params$alternative))
  conf_level <- if (is.null(params$conf_level)) 0.95 else as.numeric(params$conf_level)
  mu <- if (is.null(params$mu)) 0 else as.numeric(params$mu)
  var_equal <- if (is.null(params$var_equal)) FALSE else as.logical(params$var_equal)

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")

  y <- suppressWarnings(as.numeric(df[[response_col]]))

  if (test_type == "one_sample") {
    x_clean <- y[!is.na(y)]
    if (length(x_clean) < 2) stop("One-sample t-test requires at least 2 non-missing values")
    test <- stats::t.test(x_clean, mu = mu, alternative = alternative, conf.level = conf_level)
    n_x <- length(x_clean)
    n_y <- NA
    method <- "One Sample t-test"
  } else {
    if (is.null(group_col) || !(group_col %in% names(df)))
      stop("params.group_column is required for independent/paired t-test")

    g <- as.character(df[[group_col]])
    levels <- unique(g[!is.na(g)])
    if (length(levels) < 2) stop("t-test requires at least 2 groups")

    x <- y[g == levels[1]]
    z <- y[g == levels[2]]

    if (test_type == "paired") {
      keep <- stats::complete.cases(x, z)
      x_clean <- x[keep]
      z_clean <- z[keep]
      if (length(x_clean) < 2) stop("Paired t-test requires at least 2 complete pairs")
      test <- stats::t.test(x_clean, z_clean, paired = TRUE, mu = mu,
                            alternative = alternative, conf.level = conf_level)
      method <- "Paired t-test"
    } else {
      x_clean <- x[!is.na(x)]
      z_clean <- z[!is.na(z)]
      if (length(x_clean) < 1 || length(z_clean) < 1)
        stop("Independent t-test requires non-missing values in both groups")
      test <- stats::t.test(x_clean, z_clean, paired = FALSE, var.equal = var_equal,
                            mu = mu, alternative = alternative, conf.level = conf_level)
      method <- if (var_equal) "Two Sample t-test" else "Welch Two Sample t-test"
    }
    n_x <- length(x_clean)
    n_y <- length(z_clean)
  }

  est <- test$estimate
  estimates <- NULL
  if (!is.null(est)) {
    estimates <- lapply(seq_along(est), function(i) {
      list(name = names(est)[i], value = as.numeric(est[i]))
    })
  }

  build_response(
    "t_test",
    summary = list(
      mode = test_type,
      alternative = alternative,
      conf_level = conf_level,
      mu = mu,
      var_equal = var_equal,
      n_x = as.integer(n_x),
      n_y = if (is.na(n_y)) NULL else as.integer(n_y),
      method = method
    ),
    tables = list(
      t_test = list(
        statistic = safe_num(test$statistic),
        df = safe_num(test$parameter),
        p_value = as.numeric(test$p.value),
        conf_int_low = as.numeric(test$conf.int[1]),
        conf_int_high = as.numeric(test$conf.int[2]),
        method = as.character(test$method)
      ),
      estimates = estimates
    )
  )
}
