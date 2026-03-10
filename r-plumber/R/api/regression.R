#* Correlation analysis (Pearson/Spearman matrix)
#* @post /correlation
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params

    method <- tolower(params$method %||% "pearson")
    if (!(method %in% c("pearson", "spearman"))) method <- "pearson"

    columns <- if (!is.null(params$columns)) as.character(unlist(params$columns)) else names(df)
    columns <- columns[columns %in% names(df)]

    numeric_cols <- c()
    skipped <- c()
    for (nm in columns) {
      if (is.numeric(df[[nm]])) {
        numeric_cols <- c(numeric_cols, nm)
      } else {
        v <- suppressWarnings(as.numeric(df[[nm]]))
        if (sum(!is.na(v)) == sum(!is.na(df[[nm]])) && sum(!is.na(v)) > 0) {
          df[[nm]] <- v
          numeric_cols <- c(numeric_cols, nm)
        } else {
          skipped <- c(skipped, nm)
        }
      }
    }
    if (length(numeric_cols) < 2) stop("Requires at least 2 numeric columns")

    mat <- df[, numeric_cols, drop = FALSE]
    cor_mat <- stats::cor(mat, method = method, use = "pairwise.complete.obs")

    pairs <- list()
    idx <- 1
    for (i in seq_len(ncol(mat) - 1)) {
      for (j in seq.int(i + 1, ncol(mat))) {
        xi <- mat[[i]]
        xj <- mat[[j]]
        ok <- stats::complete.cases(xi, xj)
        n_ok <- sum(ok)
        p_val <- NA
        if (n_ok >= 3) {
          ct <- tryCatch(
            stats::cor.test(xi[ok], xj[ok], method = method),
            error = function(e) NULL
          )
          if (!is.null(ct)) p_val <- as.numeric(ct$p.value)
        }
        pairs[[idx]] <- list(
          var1 = numeric_cols[i],
          var2 = numeric_cols[j],
          n = n_ok,
          correlation = as.numeric(cor_mat[i, j]),
          p_value = p_val
        )
        idx <- idx + 1
      }
    }

    warnings_out <- list()
    if (length(skipped) > 0) {
      warnings_out <- c(warnings_out, paste("Skipped non-numeric:", paste(skipped, collapse = ", ")))
    }

    build_response(
      analysis_type = "correlation",
      summary = list(
        method = method,
        n_variables = length(numeric_cols),
        n_rows = nrow(mat),
        columns = as.list(numeric_cols)
      ),
      tables = list(pairwise = pairs),
      warnings = warnings_out
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Linear regression
#* @post /regression/linear
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column", "predictor_columns"))

    response_col <- as.character(params$response_column)
    predictor_cols <- as.character(unlist(params$predictor_columns))
    validate_columns(df, c(response_col, predictor_cols))

    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
    for (pc in predictor_cols) {
      df[[pc]] <- suppressWarnings(as.numeric(df[[pc]]))
    }

    used_cols <- c(response_col, predictor_cols)
    df <- df[stats::complete.cases(df[, used_cols, drop = FALSE]), used_cols, drop = FALSE]
    if (nrow(df) < 3) stop("Not enough complete rows")

    rhs <- paste(predictor_cols, collapse = " + ")
    formula_str <- paste(response_col, "~", rhs)
    fit <- stats::lm(stats::as.formula(formula_str), data = df)
    fit_sum <- summary(fit)

    coef_tbl <- fit_sum$coefficients
    coef_rows <- lapply(seq_len(nrow(coef_tbl)), function(i) {
      list(
        term = rownames(coef_tbl)[[i]],
        estimate = safe_num(coef_tbl[i, "Estimate"]),
        std_error = safe_num(coef_tbl[i, "Std. Error"]),
        t_value = if ("t value" %in% colnames(coef_tbl)) safe_num(coef_tbl[i, "t value"]) else NA,
        p_value = if ("Pr(>|t|)" %in% colnames(coef_tbl)) safe_num(coef_tbl[i, "Pr(>|t|)"]) else NA
      )
    })

    fstat <- fit_sum$fstatistic
    f_test <- NULL
    if (!is.null(fstat) && length(fstat) >= 3) {
      f_test <- list(
        f_value = as.numeric(fstat[[1]]),
        df1 = as.numeric(fstat[[2]]),
        df2 = as.numeric(fstat[[3]]),
        p_value = stats::pf(fstat[[1]], fstat[[2]], fstat[[3]], lower.tail = FALSE)
      )
    }

    build_response(
      analysis_type = "linear_regression",
      summary = list(
        method = "Linear Regression (OLS)",
        formula = formula_str,
        r_squared = as.numeric(fit_sum$r.squared),
        adj_r_squared = as.numeric(fit_sum$adj.r.squared),
        sigma = as.numeric(fit_sum$sigma),
        n_rows = nrow(df),
        f_test = f_test
      ),
      tables = list(coefficients = coef_rows)
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Generalized linear model (Poisson/Binomial)
#* @post /regression/glm
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column", "predictor_columns", "family"))

    response_col <- as.character(params$response_column)
    predictor_cols <- as.character(unlist(params$predictor_columns))
    family_name <- tolower(as.character(params$family))
    validate_columns(df, c(response_col, predictor_cols))

    glm_family <- switch(family_name,
      poisson = stats::poisson(),
      binomial = stats::binomial(),
      gaussian = stats::gaussian(),
      gamma = stats::Gamma(),
      stop(paste("Unsupported family:", family_name))
    )

    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
    for (pc in predictor_cols) {
      df[[pc]] <- suppressWarnings(as.numeric(df[[pc]]))
    }

    used_cols <- c(response_col, predictor_cols)
    df <- df[stats::complete.cases(df[, used_cols, drop = FALSE]), used_cols, drop = FALSE]
    if (nrow(df) < 3) stop("Not enough complete rows")

    rhs <- paste(predictor_cols, collapse = " + ")
    formula_str <- paste(response_col, "~", rhs)
    fit <- stats::glm(stats::as.formula(formula_str), data = df, family = glm_family)
    fit_sum <- summary(fit)

    coef_tbl <- fit_sum$coefficients
    coef_rows <- lapply(seq_len(nrow(coef_tbl)), function(i) {
      list(
        term = rownames(coef_tbl)[[i]],
        estimate = safe_num(coef_tbl[i, "Estimate"]),
        std_error = safe_num(coef_tbl[i, "Std. Error"]),
        z_value = if ("z value" %in% colnames(coef_tbl)) safe_num(coef_tbl[i, "z value"]) else NA,
        p_value = if ("Pr(>|z|)" %in% colnames(coef_tbl)) safe_num(coef_tbl[i, "Pr(>|z|)"]) else NA
      )
    })

    build_response(
      analysis_type = "glm",
      summary = list(
        method = paste0("GLM (", family_name, ")"),
        formula = formula_str,
        family = family_name,
        aic = as.numeric(fit_sum$aic),
        null_deviance = as.numeric(fit_sum$null.deviance),
        residual_deviance = as.numeric(fit_sum$deviance),
        df_null = as.numeric(fit_sum$df.null),
        df_residual = as.numeric(fit_sum$df.residual),
        n_rows = nrow(df)
      ),
      tables = list(coefficients = coef_rows)
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}
