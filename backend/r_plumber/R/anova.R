handle_anova_one_way <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  group_col <- params$group_column
  alpha <- if (is.null(params$alpha)) 0.05 else as.numeric(params$alpha)
  posthoc_method <- if (is.null(params$posthoc_method)) "tukey" else tolower(params$posthoc_method)

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(group_col) || !(group_col %in% names(df)))
    stop("params.group_column is required")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  df[[group_col]] <- as.character(df[[group_col]])
  complete <- stats::complete.cases(df[, c(response_col, group_col)])
  df <- df[complete, , drop = FALSE]
  df[[group_col]] <- as.factor(df[[group_col]])

  if (nrow(df) < 3) stop("Not enough complete rows for ANOVA")
  if (length(levels(df[[group_col]])) < 2) stop("ANOVA requires at least 2 groups")

  formula_obj <- stats::as.formula(paste(response_col, "~", group_col))
  fit <- stats::aov(formula_obj, data = df)
  atbl <- summary(fit)[[1]]

  anova_result <- list(
    df_between = safe_num(atbl[1, "Df"]),
    df_within = safe_num(atbl[2, "Df"]),
    ss_between = safe_num(atbl[1, "Sum Sq"]),
    ss_within = safe_num(atbl[2, "Sum Sq"]),
    ms_between = safe_num(atbl[1, "Mean Sq"]),
    ms_within = safe_num(atbl[2, "Mean Sq"]),
    f_statistic = if ("F value" %in% colnames(atbl)) safe_num(atbl[1, "F value"]) else NA,
    p_value = if ("Pr(>F)" %in% colnames(atbl)) safe_num(atbl[1, "Pr(>F)"]) else NA
  )

  # Group summary
  split_vals <- split(df[[response_col]], df[[group_col]])
  group_summary <- lapply(names(split_vals), function(g) {
    compute_group_stats(split_vals[[g]], label = g)
  })

  # Post-hoc comparisons
  warns <- list()
  posthoc_rows <- list()
  if (posthoc_method != "none") {
    if (posthoc_method == "tukey") {
      tk <- stats::TukeyHSD(fit)[[1]]
      for (i in seq_len(nrow(tk))) {
        posthoc_rows[[i]] <- list(
          comparison = rownames(tk)[i],
          diff = as.numeric(tk[i, "diff"]),
          lower = as.numeric(tk[i, "lwr"]),
          upper = as.numeric(tk[i, "upr"]),
          p_adj = as.numeric(tk[i, "p adj"])
        )
      }
    } else if (posthoc_method %in% c("lsd", "duncan") &&
               requireNamespace("agricolae", quietly = TRUE)) {
      lm_fit <- stats::lm(formula_obj, data = df)
      atbl2 <- stats::anova(lm_fit)
      df_err <- atbl2$Df[2]
      ms_err <- atbl2$"Mean Sq"[2]
      comp <- if (posthoc_method == "lsd") {
        agricolae::LSD.test(df[[response_col]], df[[group_col]], df_err, ms_err,
                            alpha = alpha, group = TRUE)
      } else {
        agricolae::duncan.test(df[[response_col]], df[[group_col]], df_err, ms_err,
                               alpha = alpha, group = TRUE)
      }
      if (!is.null(comp$comparison)) {
        cdf <- as.data.frame(comp$comparison)
        cdf$comparison <- rownames(cdf)
        for (i in seq_len(nrow(cdf))) {
          posthoc_rows[[i]] <- as.list(cdf[i, , drop = FALSE])
        }
      }
      # Attach letters to group_summary
      if (!is.null(comp$groups)) {
        gdf <- as.data.frame(comp$groups)
        gdf$group <- rownames(gdf)
        letter_col <- if ("groups" %in% colnames(gdf)) "groups" else colnames(gdf)[1]
        letter_map <- stats::setNames(as.character(gdf[[letter_col]]), gdf$group)
        for (i in seq_along(group_summary)) {
          gname <- group_summary[[i]]$group
          group_summary[[i]]$letters <- if (gname %in% names(letter_map)) letter_map[[gname]] else NULL
        }
      }
    } else if (posthoc_method %in% c("lsd", "duncan")) {
      warns <- c(warns, "Package 'agricolae' not installed; falling back to Tukey HSD.")
      tk <- stats::TukeyHSD(fit)[[1]]
      for (i in seq_len(nrow(tk))) {
        posthoc_rows[[i]] <- list(
          comparison = rownames(tk)[i],
          diff = as.numeric(tk[i, "diff"]),
          lower = as.numeric(tk[i, "lwr"]),
          upper = as.numeric(tk[i, "upr"]),
          p_adj = as.numeric(tk[i, "p adj"])
        )
      }
    }
  }

  build_response(
    "anova_one_way",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      n_groups = as.integer(length(levels(df[[group_col]]))),
      method = "One-way ANOVA",
      posthoc_method = posthoc_method
    ),
    tables = list(
      anova = anova_result,
      group_summary = group_summary,
      posthoc = posthoc_rows
    ),
    warnings = warns
  )
}

handle_anova_welch <- function(req) {
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

  test <- stats::oneway.test(stats::as.formula(paste(response_col, "~", group_col)),
                             data = df, var.equal = FALSE)

  split_vals <- split(df[[response_col]], df[[group_col]])
  group_summary <- lapply(names(split_vals), function(g) {
    compute_group_stats(split_vals[[g]], label = g)
  })

  # Games-Howell post-hoc (manual pairwise Welch t-tests with BH correction)
  levs <- levels(df[[group_col]])
  pairs <- utils::combn(levs, 2, simplify = FALSE)
  p_vals <- numeric(length(pairs))
  posthoc <- list()
  for (idx in seq_along(pairs)) {
    a <- pairs[[idx]][1]
    b <- pairs[[idx]][2]
    xa <- split_vals[[a]]
    xb <- split_vals[[b]]
    pw <- stats::t.test(xa, xb, var.equal = FALSE)
    p_vals[idx] <- pw$p.value
    posthoc[[idx]] <- list(
      comparison = paste0(b, "-", a),
      diff = mean(xb) - mean(xa),
      p_value = pw$p.value
    )
  }
  p_adj <- stats::p.adjust(p_vals, method = "BH")
  for (idx in seq_along(posthoc)) posthoc[[idx]]$p_adj <- p_adj[idx]

  build_response(
    "anova_welch",
    summary = list(
      response_column = response_col,
      group_column = group_col,
      n_groups = as.integer(length(levs)),
      method = "Welch's ANOVA"
    ),
    tables = list(
      anova = list(
        statistic = safe_num(test$statistic),
        num_df = safe_num(test$parameter[1]),
        denom_df = safe_num(test$parameter[2]),
        p_value = as.numeric(test$p.value)
      ),
      group_summary = group_summary,
      posthoc = posthoc
    )
  )
}

handle_anova_multi_way <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  response_col <- params$response_column
  factor_cols <- params$factor_columns
  anova_type <- if (is.null(params$anova_type)) 2 else as.integer(params$anova_type)

  if (is.null(response_col) || !(response_col %in% names(df)))
    stop("params.response_column is required")
  if (is.null(factor_cols) || length(factor_cols) < 2)
    stop("params.factor_columns requires at least 2 factors")

  df[[response_col]] <- suppressWarnings(as.numeric(df[[response_col]]))
  for (fc in factor_cols) df[[fc]] <- as.factor(as.character(df[[fc]]))

  formula_str <- paste(response_col, "~", paste(factor_cols, collapse = " * "))
  formula_obj <- stats::as.formula(formula_str)

  warns <- list()
  if (anova_type %in% c(2, 3) && requireNamespace("car", quietly = TRUE)) {
    lm_fit <- stats::lm(formula_obj, data = df)
    atbl <- car::Anova(lm_fit, type = anova_type)
    anova_rows <- lapply(seq_len(nrow(atbl)), function(i) {
      list(
        term = rownames(atbl)[i],
        sum_sq = safe_num(atbl[i, "Sum Sq"]),
        df = safe_num(atbl[i, "Df"]),
        f_value = if ("F value" %in% colnames(atbl)) safe_num(atbl[i, "F value"]) else NA,
        p_value = if ("Pr(>F)" %in% colnames(atbl)) safe_num(atbl[i, "Pr(>F)"]) else NA
      )
    })
  } else {
    fit <- stats::aov(formula_obj, data = df)
    atbl <- summary(fit)[[1]]
    anova_rows <- lapply(seq_len(nrow(atbl)), function(i) {
      list(
        term = trimws(rownames(atbl)[i]),
        df = safe_num(atbl[i, "Df"]),
        sum_sq = safe_num(atbl[i, "Sum Sq"]),
        mean_sq = safe_num(atbl[i, "Mean Sq"]),
        f_value = if ("F value" %in% colnames(atbl)) safe_num(atbl[i, "F value"]) else NA,
        p_value = if ("Pr(>F)" %in% colnames(atbl)) safe_num(atbl[i, "Pr(>F)"]) else NA
      )
    })
    if (anova_type %in% c(2, 3)) {
      warns <- c(warns, "Package 'car' not installed; used Type I SS instead.")
    }
  }

  build_response(
    "anova_multi_way",
    summary = list(
      response_column = response_col,
      factor_columns = as.list(factor_cols),
      anova_type = anova_type,
      formula = formula_str
    ),
    tables = list(anova = anova_rows),
    warnings = warns
  )
}
