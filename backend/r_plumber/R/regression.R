handle_regression_linear <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  predictor_cols <- params$predictor_columns

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(predictor_cols) || length(predictor_cols) < 1)
    stop("params.predictor_columns requires at least 1 predictor")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  for (pc in predictor_cols) {
    if (pc %in% names(df)) df[[pc]] <- suppressWarnings(as.numeric(df[[pc]]))
  }

  formula_str <- paste(response_col, "~", paste(predictor_cols, collapse = " + "))
  fit <- stats::lm(stats::as.formula(formula_str), data = df)
  s <- summary(fit)

  coefs <- s$coefficients
  coef_rows <- lapply(seq_len(nrow(coefs)), function(i) {
    list(
      term = rownames(coefs)[i],
      estimate = as.numeric(coefs[i, "Estimate"]),
      std_error = as.numeric(coefs[i, "Std. Error"]),
      t_value = as.numeric(coefs[i, "t value"]),
      p_value = as.numeric(coefs[i, "Pr(>|t|)"])
    )
  })

  fstat <- s$fstatistic
  f_pvalue <- if (!is.null(fstat)) {
    as.numeric(stats::pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE))
  } else NA

  build_response(
    "regression_linear",
    summary = list(
      response_column = response_col,
      predictor_columns = as.list(predictor_cols),
      formula = formula_str,
      n = as.integer(nrow(fit$model)),
      r_squared = s$r.squared,
      adj_r_squared = s$adj.r.squared,
      f_statistic = if (!is.null(fstat)) as.numeric(fstat[1]) else NA,
      f_pvalue = f_pvalue,
      residual_se = s$sigma,
      df = as.integer(s$df[2])
    ),
    tables = list(coefficients = coef_rows)
  )
}

handle_regression_glm <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  predictor_cols <- params$predictor_columns
  family <- if (is.null(params$family)) "poisson" else tolower(params$family)
  link_fn <- params$link

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(predictor_cols) || length(predictor_cols) < 1)
    stop("params.predictor_columns requires at least 1 predictor")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  for (pc in predictor_cols) {
    if (pc %in% names(df)) df[[pc]] <- suppressWarnings(as.numeric(df[[pc]]))
  }

  formula_str <- paste(response_col, "~", paste(predictor_cols, collapse = " + "))

  fam <- switch(family,
    "poisson" = if (!is.null(link_fn)) stats::poisson(link = link_fn) else stats::poisson(),
    "binomial" = if (!is.null(link_fn)) stats::binomial(link = link_fn) else stats::binomial(),
    "gaussian" = if (!is.null(link_fn)) stats::gaussian(link = link_fn) else stats::gaussian(),
    stats::poisson()
  )

  fit <- stats::glm(stats::as.formula(formula_str), data = df, family = fam)
  s <- summary(fit)

  coefs <- s$coefficients
  coef_rows <- lapply(seq_len(nrow(coefs)), function(i) {
    list(
      term = rownames(coefs)[i],
      estimate = as.numeric(coefs[i, 1]),
      std_error = as.numeric(coefs[i, 2]),
      z_value = as.numeric(coefs[i, 3]),
      p_value = as.numeric(coefs[i, 4])
    )
  })

  build_response(
    "regression_glm",
    summary = list(
      response_column = response_col,
      predictor_columns = as.list(predictor_cols),
      formula = formula_str,
      family = family,
      link = as.character(fam$link),
      n = as.integer(nrow(fit$model)),
      aic = fit$aic,
      deviance = fit$deviance,
      null_deviance = fit$null.deviance,
      df_residual = as.integer(fit$df.residual)
    ),
    tables = list(coefficients = coef_rows)
  )
}
