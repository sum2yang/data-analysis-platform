normalize_distance <- function(m) {
  if (is.null(m)) return("bray")
  m <- tolower(as.character(m))
  if (m %in% c("bray", "bray-curtis", "braycurtis")) return("bray")
  if (m %in% c("jaccard")) return("jaccard")
  if (m %in% c("euclidean")) return("euclidean")
  if (m %in% c("manhattan")) return("manhattan")
  if (m %in% c("canberra")) return("canberra")
  m
}

prepare_species_matrix <- function(df, columns, sample_id_col = NULL) {
  if (!is.null(sample_id_col) && sample_id_col %in% names(df)) {
    row_ids <- as.character(df[[sample_id_col]])
    df <- df[, setdiff(names(df), sample_id_col), drop = FALSE]
  } else {
    row_ids <- as.character(seq_len(nrow(df)))
  }

  if (is.null(columns) || length(columns) == 0) {
    columns <- names(df)
  }
  columns <- columns[columns %in% names(df)]

  numeric_cols <- c()
  for (nm in columns) {
    if (is.numeric(df[[nm]])) {
      numeric_cols <- c(numeric_cols, nm)
    } else {
      v <- suppressWarnings(as.numeric(df[[nm]]))
      if (sum(!is.na(v)) == sum(!is.na(df[[nm]])) && sum(!is.na(v)) > 0) {
        df[[nm]] <- v
        numeric_cols <- c(numeric_cols, nm)
      }
    }
  }

  mat <- df[, numeric_cols, drop = FALSE]
  mat <- mat[stats::complete.cases(mat), , drop = FALSE]
  row_ids <- row_ids[seq_len(nrow(mat))]
  rownames(mat) <- row_ids

  list(mat = mat, sample_ids = row_ids, columns = numeric_cols)
}

score_matrix_to_rows <- function(mat, id_col = "sample_id", ids = NULL) {
  if (is.null(mat)) return(NULL)
  if (is.null(ids)) ids <- rownames(mat)
  if (is.null(ids)) ids <- as.character(seq_len(nrow(mat)))

  lapply(seq_len(nrow(mat)), function(i) {
    row <- list()
    row[[id_col]] <- ids[i]
    for (j in seq_len(ncol(mat))) {
      row[[colnames(mat)[[j]]]] <- as.numeric(mat[i, j])
    }
    row
  })
}

eigenvalue_table <- function(eigenvalues, axis_prefix = "Axis") {
  total <- sum(eigenvalues[eigenvalues > 0])
  cum <- 0
  lapply(seq_along(eigenvalues), function(i) {
    ev <- eigenvalues[i]
    pct <- if (total > 0) ev / total else 0
    cum <<- cum + pct
    list(
      axis = paste0(axis_prefix, i),
      eigenvalue = as.numeric(ev),
      explained_variance = as.numeric(pct),
      cumulative = as.numeric(cum)
    )
  })
}

compute_group_ellipses <- function(scores, groups, axes = c(1, 2), conf = 0.95) {
  if (is.null(groups) || ncol(scores) < 2) return(NULL)
  unique_groups <- unique(groups)
  ellipses <- list()
  for (g in unique_groups) {
    idx <- which(groups == g)
    if (length(idx) < 3) next
    pts <- scores[idx, axes, drop = FALSE]
    center <- colMeans(pts)
    cov_mat <- stats::cov(pts)
    chi_val <- stats::qchisq(conf, df = 2)
    eig <- eigen(cov_mat)
    angles <- seq(0, 2 * pi, length.out = 61)
    unit_circle <- cbind(cos(angles), sin(angles))
    transform <- eig$vectors %*% diag(sqrt(pmax(eig$values, 0) * chi_val))
    ell_pts <- sweep(unit_circle %*% t(transform), 2, center, "+")
    ellipses[[length(ellipses) + 1]] <- list(
      group = as.character(g),
      center_x = center[1],
      center_y = center[2],
      points = lapply(seq_len(nrow(ell_pts)), function(i) {
        list(x = ell_pts[i, 1], y = ell_pts[i, 2])
      })
    )
  }
  if (length(ellipses) == 0) return(NULL)
  ellipses
}
