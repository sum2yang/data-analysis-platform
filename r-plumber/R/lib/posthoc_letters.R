normalize_posthoc_method <- function(m) {
  if (is.null(m)) return("tukey")
  m <- tolower(as.character(m))
  if (m %in% c("tukey", "tukey hsd", "hsd", "tukey_hsd")) return("tukey")
  if (m %in% c("lsd")) return("lsd")
  if (m %in% c("duncan")) return("duncan")
  if (m %in% c("none", "null", "")) return("none")
  m
}

normalize_welch_posthoc <- function(m) {
  if (is.null(m)) return("games-howell")
  m <- tolower(as.character(m))
  if (m %in% c("games-howell", "games howell", "games_howell")) return("games-howell")
  if (m %in% c("tamhane", "tamhane t2", "tamhane_t2", "t2")) return("tamhane-t2")
  if (m %in% c("dunnett", "dunnett t3", "dunnett_t3", "t3")) return("dunnett-t3")
  if (m %in% c("none", "")) return("none")
  m
}

safe_group_shapiro <- function(x) {
  x <- x[!is.na(x)]
  n <- length(x)
  if (n < 3 || n > 5000) {
    return(list(statistic = NA, p_value = NA, note = "Shapiro requires 3-5000 non-missing values"))
  }
  res <- stats::shapiro.test(x)
  list(statistic = unname(res$statistic), p_value = res$p.value, note = NULL)
}

group_summary_rows <- function(df_raw, df_clean, response_col, group_col) {
  split_clean <- split(df_clean[[response_col]], df_clean[[group_col]])
  lapply(names(split_clean), function(g) {
    x <- as.numeric(split_clean[[g]])
    x <- x[!is.na(x)]
    list(
      group = as.character(g),
      n = length(x),
      mean = if (length(x) > 0) mean(x) else NA,
      sd = if (length(x) > 1) stats::sd(x) else NA,
      se = if (length(x) > 1) stats::sd(x) / sqrt(length(x)) else NA,
      median = if (length(x) > 0) stats::median(x) else NA,
      min = if (length(x) > 0) min(x) else NA,
      max = if (length(x) > 0) max(x) else NA,
      missing_count = sum(df_raw[[group_col]] == g & is.na(df_raw[[response_col]]), na.rm = TRUE)
    )
  })
}

pairwise_matrix_to_rows <- function(p_matrix) {
  if (is.null(p_matrix) || !is.matrix(p_matrix)) return(NULL)
  rows <- list()
  idx <- 1
  for (i in seq_len(nrow(p_matrix))) {
    for (j in seq_len(ncol(p_matrix))) {
      p <- p_matrix[i, j]
      if (!is.na(p)) {
        rows[[idx]] <- list(
          group1 = as.character(rownames(p_matrix)[[i]]),
          group2 = as.character(colnames(p_matrix)[[j]]),
          p_adj = as.numeric(p)
        )
        idx <- idx + 1
      }
    }
  }
  if (length(rows) == 0) return(NULL)
  rows
}

full_p_matrix <- function(p_matrix, group_levels) {
  full <- matrix(
    NA_real_,
    nrow = length(group_levels),
    ncol = length(group_levels),
    dimnames = list(group_levels, group_levels)
  )
  diag(full) <- 1
  if (is.null(p_matrix) || !is.matrix(p_matrix)) return(full)
  for (i in seq_len(nrow(p_matrix))) {
    for (j in seq_len(ncol(p_matrix))) {
      p <- p_matrix[i, j]
      if (!is.na(p)) {
        r <- rownames(p_matrix)[[i]]
        cc <- colnames(p_matrix)[[j]]
        if (r %in% group_levels && cc %in% group_levels) {
          full[r, cc] <- as.numeric(p)
          full[cc, r] <- as.numeric(p)
        }
      }
    }
  }
  full
}

letters_from_p_matrix <- function(full_matrix, alpha) {
  if (!requireNamespace("multcompView", quietly = TRUE)) {
    return(list(rows = NULL, warning = "Package 'multcompView' not installed"))
  }
  lower_idx <- lower.tri(full_matrix, diag = FALSE)
  vals <- full_matrix[lower_idx]
  nm <- outer(rownames(full_matrix), colnames(full_matrix),
              FUN = function(a, b) paste(a, b, sep = "-"))
  names(vals) <- nm[lower_idx]
  keep <- !is.na(vals)
  vals <- vals[keep]
  if (length(vals) == 0) {
    return(list(rows = NULL, warning = "No pairwise p-values available for lettering"))
  }
  letters_obj <- multcompView::multcompLetters(vals, compare = "<",
                                               threshold = alpha, Letters = letters)
  rows <- lapply(names(letters_obj$Letters), function(g) {
    list(group = g, letters = unname(letters_obj$Letters[[g]]))
  })
  list(rows = rows, warning = NULL)
}

attach_letters_to_summary <- function(group_rows, letters_rows) {
  if (is.null(letters_rows)) return(group_rows)
  letter_map <- setNames(
    vapply(letters_rows, function(x) as.character(x$letters), FUN.VALUE = character(1)),
    vapply(letters_rows, function(x) as.character(x$group), FUN.VALUE = character(1))
  )
  for (i in seq_along(group_rows)) {
    g <- group_rows[[i]]$group
    group_rows[[i]]$letters <- if (g %in% names(letter_map)) letter_map[[g]] else NULL
  }
  group_rows
}

run_agricolae_posthoc <- function(df, response_col, group_col, method, alpha) {
  anova_model <- stats::anova(stats::lm(
    stats::as.formula(paste(response_col, "~", group_col)), data = df
  ))
  df_error <- anova_model$Df[2]
  ms_error <- anova_model$"Mean Sq"[2]

  comp <- switch(method,
    "lsd" = agricolae::LSD.test(
      y = df[[response_col]], trt = df[[group_col]],
      DFerror = df_error, MSerror = ms_error, alpha = alpha, group = TRUE
    ),
    "duncan" = agricolae::duncan.test(
      y = df[[response_col]], trt = df[[group_col]],
      DFerror = df_error, MSerror = ms_error, alpha = alpha, group = TRUE
    ),
    "tukey" = agricolae::HSD.test(
      y = df[[response_col]], trt = df[[group_col]],
      DFerror = df_error, MSerror = ms_error, alpha = alpha, group = TRUE
    ),
    NULL
  )
  comp
}

extract_posthoc_results <- function(comp) {
  posthoc_rows <- NULL
  letters_rows <- NULL

  if (!is.null(comp$comparison)) {
    cmp_df <- as.data.frame(comp$comparison)
    cmp_df$comparison <- rownames(cmp_df)
    rownames(cmp_df) <- NULL
    posthoc_rows <- lapply(seq_len(nrow(cmp_df)), function(i) {
      row_list <- as.list(cmp_df[i, , drop = FALSE])
      lapply(row_list, function(v) {
        if (length(v) == 1 && is.na(v)) return(NULL)
        if (length(v) == 1) return(v[[1]])
        v
      })
    })
  }

  if (!is.null(comp$groups)) {
    groups_df <- as.data.frame(comp$groups)
    groups_df$group <- rownames(groups_df)
    rownames(groups_df) <- NULL
    letters_col <- if ("groups" %in% colnames(groups_df)) "groups" else colnames(groups_df)[1]
    mean_col <- if ("means" %in% colnames(groups_df)) "means" else NULL
    letters_rows <- lapply(seq_len(nrow(groups_df)), function(i) {
      list(
        group = as.character(groups_df$group[[i]]),
        mean = if (!is.null(mean_col)) safe_num(groups_df[i, mean_col]) else NA,
        letters = as.character(groups_df[[letters_col]][[i]])
      )
    })
  }

  list(posthoc = posthoc_rows, letters = letters_rows)
}

prepare_grouped_data <- function(body) {
  df <- load_data(body)
  params <- body$params
  validate_required(params, c("response_column", "group_column"))

  response_col <- as.character(params$response_column)
  group_col <- as.character(params$group_column)
  validate_columns(df, c(response_col, group_col))

  alpha <- if (is.null(params$alpha)) 0.05 else as.numeric(params$alpha)
  if (is.na(alpha) || alpha <= 0 || alpha >= 1) alpha <- 0.05

  df_raw <- df
  df_raw[[response_col]] <- suppressWarnings(as.numeric(df_raw[[response_col]]))
  df_raw[[group_col]] <- as.character(df_raw[[group_col]])

  df_clean <- df_raw[stats::complete.cases(df_raw[, c(response_col, group_col)]), , drop = FALSE]
  df_clean[[group_col]] <- as.factor(df_clean[[group_col]])

  list(
    df_raw = df_raw,
    df = df_clean,
    response_col = response_col,
    group_col = group_col,
    alpha = alpha,
    params = params
  )
}

run_assumptions <- function(df, response_col, group_col) {
  assumptions <- list()
  split_clean <- split(df[[response_col]], df[[group_col]])

  n_all <- sum(!is.na(df[[response_col]]))
  if (n_all >= 3 && n_all <= 5000) {
    sh <- stats::shapiro.test(df[[response_col]])
    assumptions$normality <- list(
      test = "Shapiro-Wilk",
      statistic = unname(sh$statistic),
      p_value = sh$p.value
    )
  } else {
    assumptions$normality <- list(test = "Shapiro-Wilk", statistic = NA, p_value = NA,
                                  note = "Skipped: sample size must be 3-5000")
  }

  assumptions$normality_by_group <- lapply(names(split_clean), function(g) {
    c(list(group = g), safe_group_shapiro(as.numeric(split_clean[[g]])))
  })

  if (requireNamespace("car", quietly = TRUE)) {
    lev <- car::leveneTest(df[[response_col]], df[[group_col]])
    assumptions$homogeneity <- list(
      test = "Levene",
      statistic = if ("F value" %in% colnames(lev)) safe_num(lev[1, "F value"]) else NA,
      p_value = if ("Pr(>F)" %in% colnames(lev)) safe_num(lev[1, "Pr(>F)"]) else NA
    )
  }

  assumptions
}
