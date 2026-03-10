#* Independent/Paired/One-sample t-test
#* @post /t-test
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column"))

    response_col <- as.character(params$response_column)
    validate_columns(df, response_col)
    response_col <- safe_colname(response_col)
    if (!(response_col %in% names(df))) {
      orig <- as.character(params$response_column)
      names(df)[names(df) == orig] <- response_col
    }
    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))

    mode <- tolower(params$mode %||% "independent")
    if (mode %in% c("ind", "two_sample", "two-sample")) mode <- "independent"
    if (mode %in% c("pair")) mode <- "paired"
    if (mode %in% c("one_sample", "one-sample", "onesample")) mode <- "one_sample"

    alternative <- tolower(params$alternative %||% "two.sided")
    if (alternative %in% c("two-sided", "two_sided")) alternative <- "two.sided"

    conf_level <- as.numeric(params$conf_level %||% 0.95)
    if (is.na(conf_level) || conf_level <= 0 || conf_level >= 1) conf_level <- 0.95
    mu <- as.numeric(params$mu %||% 0)
    if (is.na(mu)) mu <- 0
    var_equal <- as.logical(params$var_equal %||% TRUE)

    if (mode == "one_sample") {
      x <- df[[response_col]][!is.na(df[[response_col]])]
      if (length(x) < 2) stop("One-sample t-test requires at least 2 non-missing values")
      test <- stats::t.test(x, mu = mu, alternative = alternative, conf.level = conf_level)
      n1 <- length(x)
      n2 <- NA
    } else {
      group_col <- as.character(params$group_column)
      validate_columns(df, group_col)
      df[[group_col]] <- as.character(df[[group_col]])
      groups <- unique(df[[group_col]][!is.na(df[[group_col]])])
      if (length(groups) != 2) stop("t-test requires exactly 2 groups")

      g1 <- df[[response_col]][df[[group_col]] == groups[1]]
      g2 <- df[[response_col]][df[[group_col]] == groups[2]]
      g1 <- g1[!is.na(g1)]
      g2 <- g2[!is.na(g2)]

      if (mode == "paired") {
        if (length(g1) != length(g2)) stop("Paired t-test requires equal group sizes")
        test <- stats::t.test(g1, g2, paired = TRUE, mu = mu,
                              alternative = alternative, conf.level = conf_level)
      } else {
        test <- stats::t.test(g1, g2, paired = FALSE, var.equal = var_equal, mu = mu,
                              alternative = alternative, conf.level = conf_level)
      }
      n1 <- length(g1)
      n2 <- length(g2)
    }

    build_response(
      analysis_type = "t_test",
      summary = list(
        mode = mode,
        alternative = alternative,
        conf_level = conf_level,
        mu = mu,
        var_equal = if (mode == "independent") var_equal else NULL,
        n_x = n1,
        n_y = n2,
        method = as.character(test$method)
      ),
      tables = list(
        t_test = list(
          statistic = safe_num(test$statistic),
          df = safe_num(test$parameter),
          p_value = as.numeric(test$p.value),
          conf_int_low = as.numeric(test$conf.int[[1]]),
          conf_int_high = as.numeric(test$conf.int[[2]]),
          method = as.character(test$method)
        ),
        estimates = lapply(seq_along(test$estimate), function(i) {
          list(name = names(test$estimate)[[i]], value = as.numeric(test$estimate[[i]]))
        })
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* One-way ANOVA with posthoc and significance letters
#* @post /anova/one-way
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    prep <- prepare_grouped_data(body)
    df_raw <- prep$df_raw
    df <- prep$df
    response_col <- prep$response_col
    group_col <- prep$group_col
    alpha <- prep$alpha
    posthoc_method <- normalize_posthoc_method(prep$params$posthoc_method)

    if (nrow(df) < 3) stop("Not enough complete rows for ANOVA")
    if (length(unique(df[[group_col]])) < 2) stop("ANOVA requires at least 2 groups")

    formula_str <- paste(response_col, "~", group_col)
    fit <- stats::aov(stats::as.formula(formula_str), data = df)
    anova_tbl <- summary(fit)[[1]]

    anova_rows <- lapply(seq_len(nrow(anova_tbl)), function(i) {
      list(
        term = trimws(rownames(anova_tbl)[[i]]),
        df = safe_num(anova_tbl[i, "Df"]),
        sum_sq = if ("Sum Sq" %in% colnames(anova_tbl)) safe_num(anova_tbl[i, "Sum Sq"]) else NA,
        mean_sq = if ("Mean Sq" %in% colnames(anova_tbl)) safe_num(anova_tbl[i, "Mean Sq"]) else NA,
        f_value = if ("F value" %in% colnames(anova_tbl)) safe_num(anova_tbl[i, "F value"]) else NA,
        p_value = if ("Pr(>F)" %in% colnames(anova_tbl)) safe_num(anova_tbl[i, "Pr(>F)"]) else NA
      )
    })

    group_rows <- group_summary_rows(df_raw, df, response_col, group_col)
    assumptions <- run_assumptions(df, response_col, group_col)
    warnings_out <- list()
    posthoc_rows <- NULL
    letters_rows <- NULL

    if (posthoc_method != "none" && requireNamespace("agricolae", quietly = TRUE)) {
      comp <- run_agricolae_posthoc(df, response_col, group_col, posthoc_method, alpha)
      if (!is.null(comp)) {
        res_ph <- extract_posthoc_results(comp)
        posthoc_rows <- res_ph$posthoc
        letters_rows <- res_ph$letters
        group_rows <- attach_letters_to_summary(group_rows, letters_rows)
      } else {
        warnings_out <- c(warnings_out, paste("Unsupported posthoc_method:", posthoc_method))
      }
    }

    build_response(
      analysis_type = "one_way_anova",
      summary = list(
        method = "One-Way ANOVA",
        response_column = response_col,
        group_column = group_col,
        n_rows_complete = nrow(df),
        n_groups = length(unique(df[[group_col]])),
        alpha = alpha,
        posthoc_method = posthoc_method,
        statistic = safe_num(anova_tbl[1, "F value"]),
        p_value = safe_num(anova_tbl[1, "Pr(>F)"])
      ),
      tables = list(
        anova_table = anova_rows,
        group_summary = group_rows,
        posthoc = posthoc_rows,
        significance_letters = letters_rows
      ),
      assumptions = assumptions,
      warnings = warnings_out
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Multi-way ANOVA (car::Anova Type II/III)
#* @post /anova/multi-way
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column", "factor_columns"))

    response_col <- as.character(params$response_column)
    factor_cols <- as.character(unlist(params$factor_columns))
    validate_columns(df, c(response_col, factor_cols))

    include_interactions <- as.logical(params$include_interactions %||% TRUE)
    ss_type_raw <- as.character(params$ss_type %||% "2")
    ss_type <- as.integer(gsub("[^123]", "", ss_type_raw))
    if (is.na(ss_type) || !(ss_type %in% c(1L, 2L, 3L))) ss_type <- 2L

    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
    for (fc in factor_cols) df[[fc]] <- as.factor(as.character(df[[fc]]))

    used_cols <- c(response_col, factor_cols)
    df <- df[stats::complete.cases(df[, used_cols, drop = FALSE]), used_cols, drop = FALSE]
    if (nrow(df) < 3) stop("Not enough complete rows")
    if (length(factor_cols) < 2) stop("Multi-way ANOVA requires at least 2 factors")

    rhs <- if (include_interactions) paste(factor_cols, collapse = " * ")
           else paste(factor_cols, collapse = " + ")
    formula_obj <- stats::as.formula(paste(response_col, "~", rhs))

    warnings_out <- list()
    if (ss_type == 3L) {
      old_opts <- options("contrasts")
      on.exit(options(old_opts), add = TRUE)
      options(contrasts = c("contr.sum", "contr.poly"))
    }
    fit <- stats::lm(formula_obj, data = df)

    if (ss_type %in% c(2L, 3L) && requireNamespace("car", quietly = TRUE)) {
      car_tbl <- car::Anova(fit, type = ss_type)
      anova_df <- as.data.frame(car_tbl)
      anova_df$term <- rownames(anova_df)
      rownames(anova_df) <- NULL
      anova_source <- paste0("car::Anova(type=", ss_type, ")")
    } else {
      a1 <- stats::anova(fit)
      anova_df <- as.data.frame(a1)
      anova_df$term <- rownames(anova_df)
      rownames(anova_df) <- NULL
      anova_source <- "stats::anova (Type I)"
      if (ss_type != 1L) {
        warnings_out <- c(warnings_out, "Package 'car' not installed; falling back to Type I")
      }
    }

    anova_rows <- lapply(seq_len(nrow(anova_df)), function(i) {
      row_i <- anova_df[i, , drop = FALSE]
      cols <- colnames(row_i)
      list(
        term = as.character(row_i$term),
        df = if ("Df" %in% cols) safe_num(row_i[1, "Df"]) else NA,
        sum_sq = if ("Sum Sq" %in% cols) safe_num(row_i[1, "Sum Sq"]) else NA,
        f_value = if ("F value" %in% cols) safe_num(row_i[1, "F value"])
                  else if ("F" %in% cols) safe_num(row_i[1, "F"]) else NA,
        p_value = if ("Pr(>F)" %in% cols) safe_num(row_i[1, "Pr(>F)"])
                  else if ("Pr(>Chisq)" %in% cols) safe_num(row_i[1, "Pr(>Chisq)"]) else NA
      )
    })

    resids <- stats::residuals(fit)
    assumptions <- list()
    n_resid <- sum(!is.na(resids))
    if (n_resid >= 3 && n_resid <= 5000) {
      sh <- stats::shapiro.test(resids)
      assumptions$normality <- list(test = "Shapiro-Wilk (residuals)",
                                    statistic = unname(sh$statistic), p_value = sh$p.value)
    }

    build_response(
      analysis_type = "multi_way_anova",
      summary = list(
        method = paste0("Multi-Way ANOVA (", anova_source, ")"),
        response_column = response_col,
        factor_columns = as.list(factor_cols),
        include_interactions = include_interactions,
        ss_type = ss_type,
        n_rows = nrow(df)
      ),
      tables = list(anova_table = anova_rows),
      assumptions = assumptions,
      warnings = warnings_out
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Welch ANOVA with Games-Howell posthoc
#* @post /anova/welch
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    prep <- prepare_grouped_data(body)
    df_raw <- prep$df_raw
    df <- prep$df
    response_col <- prep$response_col
    group_col <- prep$group_col
    alpha <- prep$alpha
    posthoc_method <- normalize_welch_posthoc(prep$params$posthoc_method)

    if (nrow(df) < 3) stop("Not enough complete rows")
    if (length(unique(df[[group_col]])) < 2) stop("Requires at least 2 groups")

    tmp <- data.frame(y = df[[response_col]], g = df[[group_col]])
    welch <- stats::oneway.test(y ~ g, data = tmp, var.equal = FALSE)

    group_rows <- group_summary_rows(df_raw, df, response_col, group_col)
    group_levels <- vapply(group_rows, function(x) x$group, FUN.VALUE = character(1))
    assumptions <- run_assumptions(df, response_col, group_col)
    warnings_out <- list()
    posthoc_rows <- NULL
    letters_rows <- NULL

    if (posthoc_method != "none" && requireNamespace("PMCMRplus", quietly = TRUE)) {
      posthoc_obj <- switch(posthoc_method,
        "games-howell" = PMCMRplus::gamesHowellTest(y ~ g, data = tmp),
        "tamhane-t2" = PMCMRplus::tamhaneT2Test(y ~ g, data = tmp),
        "dunnett-t3" = PMCMRplus::dunnettT3Test(y ~ g, data = tmp),
        NULL
      )
      if (!is.null(posthoc_obj)) {
        p_matrix <- posthoc_obj$p.value
        posthoc_rows <- pairwise_matrix_to_rows(p_matrix)
        full_p <- full_p_matrix(p_matrix, group_levels)
        letters_info <- letters_from_p_matrix(full_p, alpha)
        if (!is.null(letters_info$warning)) warnings_out <- c(warnings_out, letters_info$warning)
        letters_rows <- letters_info$rows
        group_rows <- attach_letters_to_summary(group_rows, letters_rows)
      }
    }

    build_response(
      analysis_type = "welch_anova",
      summary = list(
        method = "Welch's ANOVA",
        response_column = response_col,
        group_column = group_col,
        n_rows_complete = nrow(df),
        n_groups = length(unique(df[[group_col]])),
        alpha = alpha,
        posthoc_method = posthoc_method,
        statistic = as.numeric(welch$statistic[[1]]),
        p_value = as.numeric(welch$p.value)
      ),
      tables = list(
        welch_anova = list(
          numerator_df = as.numeric(welch$parameter[[1]]),
          denominator_df = as.numeric(welch$parameter[[2]]),
          f_value = as.numeric(welch$statistic[[1]]),
          p_value = as.numeric(welch$p.value)
        ),
        group_summary = group_rows,
        posthoc = posthoc_rows,
        significance_letters = letters_rows
      ),
      assumptions = assumptions,
      warnings = warnings_out
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Kruskal-Wallis test with pairwise Wilcoxon
#* @post /nonparametric/kruskal-wallis
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    prep <- prepare_grouped_data(body)
    df_raw <- prep$df_raw
    df <- prep$df
    response_col <- prep$response_col
    group_col <- prep$group_col
    alpha <- prep$alpha

    p_adjust <- tolower(prep$params$p_adjust %||% "none")
    valid_adjusts <- c("none", "holm", "hommel", "hochberg", "bonferroni", "BH", "BY", "fdr")
    if (!(p_adjust %in% valid_adjusts)) p_adjust <- "none"

    if (nrow(df) < 3) stop("Not enough complete rows")
    if (length(unique(df[[group_col]])) < 2) stop("Requires at least 2 groups")

    tmp <- data.frame(y = df[[response_col]], g = df[[group_col]])
    kw <- stats::kruskal.test(y ~ g, data = tmp)

    group_rows <- group_summary_rows(df_raw, df, response_col, group_col)
    group_levels <- vapply(group_rows, function(x) x$group, FUN.VALUE = character(1))
    warnings_out <- list()
    posthoc_rows <- NULL
    letters_rows <- NULL

    pw <- stats::pairwise.wilcox.test(
      x = df[[response_col]], g = df[[group_col]],
      p.adjust.method = p_adjust, exact = FALSE
    )
    if (!is.null(pw$p.value)) {
      posthoc_rows <- pairwise_matrix_to_rows(pw$p.value)
      full_p <- full_p_matrix(pw$p.value, group_levels)
      letters_info <- letters_from_p_matrix(full_p, alpha)
      if (!is.null(letters_info$warning)) warnings_out <- c(warnings_out, letters_info$warning)
      letters_rows <- letters_info$rows
      group_rows <- attach_letters_to_summary(group_rows, letters_rows)
    }

    build_response(
      analysis_type = "kruskal_wallis",
      summary = list(
        method = "Kruskal-Wallis",
        response_column = response_col,
        group_column = group_col,
        n_rows_complete = nrow(df),
        n_groups = length(unique(df[[group_col]])),
        alpha = alpha,
        p_adjust = p_adjust,
        statistic = as.numeric(kw$statistic[[1]]),
        p_value = as.numeric(kw$p.value)
      ),
      tables = list(
        kruskal_wallis = list(
          chi_squared = as.numeric(kw$statistic[[1]]),
          df = as.numeric(kw$parameter[[1]]),
          p_value = as.numeric(kw$p.value)
        ),
        group_summary = group_rows,
        posthoc = posthoc_rows,
        significance_letters = letters_rows
      ),
      warnings = warnings_out
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* Mann-Whitney U test
#* @post /nonparametric/mann-whitney
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params
    validate_required(params, c("response_column", "group_column"))

    response_col <- as.character(params$response_column)
    group_col <- as.character(params$group_column)
    validate_columns(df, c(response_col, group_col))

    df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
    df[[group_col]] <- as.character(df[[group_col]])
    df <- df[stats::complete.cases(df[, c(response_col, group_col)]), , drop = FALSE]

    groups <- unique(df[[group_col]])
    if (length(groups) != 2) stop("Mann-Whitney requires exactly 2 groups")

    g1 <- df[[response_col]][df[[group_col]] == groups[1]]
    g2 <- df[[response_col]][df[[group_col]] == groups[2]]

    alternative <- tolower(params$alternative %||% "two.sided")
    if (alternative %in% c("two-sided", "two_sided")) alternative <- "two.sided"

    test <- stats::wilcox.test(g1, g2, alternative = alternative, exact = FALSE,
                               correct = TRUE, conf.int = TRUE)

    build_response(
      analysis_type = "mann_whitney",
      summary = list(
        method = "Mann-Whitney U",
        response_column = response_col,
        group_column = group_col,
        groups = as.list(groups),
        n_group1 = length(g1),
        n_group2 = length(g2),
        alternative = alternative,
        statistic = safe_num(test$statistic),
        p_value = as.numeric(test$p.value)
      ),
      tables = list(
        mann_whitney = list(
          statistic_w = safe_num(test$statistic),
          p_value = as.numeric(test$p.value),
          conf_int_low = if (!is.null(test$conf.int)) as.numeric(test$conf.int[[1]]) else NA,
          conf_int_high = if (!is.null(test$conf.int)) as.numeric(test$conf.int[[2]]) else NA,
          estimate = if (!is.null(test$estimate)) safe_num(test$estimate) else NA,
          method = as.character(test$method)
        )
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}
