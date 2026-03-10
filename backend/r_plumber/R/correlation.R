handle_correlation <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  columns <- params$columns
  method <- if (is.null(params$method)) "pearson" else tolower(params$method)
  if (!(method %in% c("pearson", "spearman"))) method <- "pearson"

  if (is.null(columns) || length(columns) < 2)
    stop("params.columns requires at least 2 column names")
  columns <- columns[columns %in% names(df)]
  if (length(columns) < 2) stop("At least 2 valid numeric columns are required")

  # Coerce to numeric, skip non-numeric
  warns <- list()
  numeric_cols <- c()
  for (col in columns) {
    v <- suppressWarnings(as.numeric(df[[col]]))
    if (sum(!is.na(v)) > 0) {
      df[[col]] <- v
      numeric_cols <- c(numeric_cols, col)
    } else {
      warns <- c(warns, paste("Skipped non-numeric column:", col))
    }
  }
  if (length(numeric_cols) < 2) stop("Correlation requires at least 2 numeric columns")

  mat <- df[, numeric_cols, drop = FALSE]
  cor_mat <- stats::cor(mat, method = method, use = "pairwise.complete.obs")

  # Build pairwise stats (upper triangle)
  pairwise <- list()
  idx <- 1
  for (i in seq_len(ncol(mat))) {
    if (i >= ncol(mat)) next
    for (j in seq.int(i + 1, ncol(mat))) {
      xi <- mat[[i]]
      xj <- mat[[j]]
      ok <- stats::complete.cases(xi, xj)
      n_ok <- sum(ok)
      p_val <- NA
      if (n_ok >= 3) {
        ct <- suppressWarnings(try(stats::cor.test(xi[ok], xj[ok], method = method), silent = TRUE))
        if (!inherits(ct, "try-error")) p_val <- as.numeric(ct$p.value)
      }
      pairwise[[idx]] <- list(
        var1 = numeric_cols[i],
        var2 = numeric_cols[j],
        n = as.integer(n_ok),
        correlation = as.numeric(cor_mat[i, j]),
        p_value = p_val
      )
      idx <- idx + 1
    }
  }

  # Wide-format correlation matrix
  cor_wide <- lapply(seq_len(nrow(cor_mat)), function(i) {
    row <- list(row = rownames(cor_mat)[i])
    for (j in seq_len(ncol(cor_mat))) {
      row[[colnames(cor_mat)[j]]] <- as.numeric(cor_mat[i, j])
    }
    row
  })

  build_response(
    "correlation",
    summary = list(
      method = method,
      n_variables = as.integer(length(numeric_cols)),
      columns = as.list(numeric_cols)
    ),
    tables = list(
      pairwise_stats = pairwise,
      correlation_matrix = cor_wide
    ),
    warnings = warns
  )
}
