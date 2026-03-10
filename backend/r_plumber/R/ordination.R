handle_pca <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  group_col <- params$group_column
  columns <- params$columns
  scale <- if (is.null(params$scale)) TRUE else as.logical(params$scale)

  # Select numeric columns
  if (!is.null(columns)) {
    num_cols <- columns[columns %in% names(df)]
  } else {
    num_cols <- names(df)[sapply(df, is.numeric)]
    if (!is.null(group_col)) num_cols <- setdiff(num_cols, group_col)
  }
  if (length(num_cols) < 2) stop("PCA requires at least 2 numeric columns")

  mat <- df[, num_cols, drop = FALSE]
  mat <- mat[stats::complete.cases(mat), , drop = FALSE]
  mat <- as.data.frame(lapply(mat, as.numeric))

  pca <- stats::prcomp(mat, scale. = scale, center = TRUE)
  eig <- pca$sdev^2
  explained <- eig / sum(eig)
  cum <- cumsum(explained)

  n_pc <- min(length(eig), 10)
  eigenvalues <- lapply(seq_len(n_pc), function(i) {
    list(axis = paste0("PC", i), eigenvalue = eig[i],
         explained_variance = explained[i], cumulative = cum[i])
  })

  scores_mat <- pca$x[, seq_len(min(ncol(pca$x), 5)), drop = FALSE]
  groups <- if (!is.null(group_col) && group_col %in% names(df)) {
    as.character(df[[group_col]])[stats::complete.cases(df[, num_cols])]
  } else rep("default", nrow(scores_mat))

  scores <- lapply(seq_len(nrow(scores_mat)), function(i) {
    row <- as.list(scores_mat[i, ])
    row$sample_id <- as.character(i)
    row$group <- groups[i]
    row
  })

  build_response(
    "pca",
    summary = list(n_components = n_pc, scale = scale, n_samples = nrow(mat)),
    tables = list(eigenvalues = eigenvalues, scores = scores)
  )
}

handle_pcoa <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  group_col <- params$group_column
  columns <- params$columns
  dist_method <- if (is.null(params$distance_method)) "euclidean" else params$distance_method

  if (!is.null(columns)) {
    num_cols <- columns[columns %in% names(df)]
  } else {
    num_cols <- names(df)[sapply(df, is.numeric)]
    if (!is.null(group_col)) num_cols <- setdiff(num_cols, group_col)
  }
  if (length(num_cols) < 2) stop("PCoA requires at least 2 numeric columns")

  mat <- df[, num_cols, drop = FALSE]
  complete_idx <- stats::complete.cases(mat)
  mat <- as.data.frame(lapply(mat[complete_idx, , drop = FALSE], as.numeric))

  d <- stats::dist(mat, method = dist_method)
  pcoa_res <- stats::cmdscale(d, k = min(nrow(mat) - 1, 5), eig = TRUE)

  eig <- pcoa_res$eig
  eig_pos <- pmax(eig, 0)
  explained <- eig_pos / sum(eig_pos)
  n_ax <- min(sum(eig_pos > 0), 5)

  eigenvalues <- lapply(seq_len(n_ax), function(i) {
    list(axis = paste0("PCoA", i), eigenvalue = eig[i],
         explained_variance = explained[i], cumulative = sum(explained[seq_len(i)]))
  })

  groups <- if (!is.null(group_col) && group_col %in% names(df)) {
    as.character(df[[group_col]])[complete_idx]
  } else rep("default", nrow(pcoa_res$points))

  scores <- lapply(seq_len(nrow(pcoa_res$points)), function(i) {
    row <- as.list(pcoa_res$points[i, seq_len(n_ax)])
    names(row) <- paste0("PCoA", seq_len(n_ax))
    row$sample_id <- as.character(i)
    row$group <- groups[i]
    row
  })

  build_response(
    "pcoa",
    summary = list(distance_method = dist_method, n_axes = n_ax, n_samples = nrow(mat)),
    tables = list(eigenvalues = eigenvalues, scores = scores)
  )
}

handle_nmds <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params

  group_col <- params$group_column
  columns <- params$columns
  dist_method <- if (is.null(params$distance_method)) "bray" else params$distance_method
  k <- if (is.null(params$dimensions)) 2 else as.integer(params$dimensions)

  if (!is.null(columns)) {
    num_cols <- columns[columns %in% names(df)]
  } else {
    num_cols <- names(df)[sapply(df, is.numeric)]
    if (!is.null(group_col)) num_cols <- setdiff(num_cols, group_col)
  }
  if (length(num_cols) < 2) stop("NMDS requires at least 2 numeric columns")

  mat <- df[, num_cols, drop = FALSE]
  complete_idx <- stats::complete.cases(mat)
  mat <- as.data.frame(lapply(mat[complete_idx, , drop = FALSE], as.numeric))

  if (!requireNamespace("vegan", quietly = TRUE))
    stop("Package 'vegan' is required for NMDS")

  nmds <- vegan::metaMDS(mat, distance = dist_method, k = k, trace = 0, trymax = 100)

  groups <- if (!is.null(group_col) && group_col %in% names(df)) {
    as.character(df[[group_col]])[complete_idx]
  } else rep("default", nrow(nmds$points))

  scores <- lapply(seq_len(nrow(nmds$points)), function(i) {
    row <- as.list(nmds$points[i, ])
    names(row) <- paste0("NMDS", seq_len(ncol(nmds$points)))
    row$sample_id <- as.character(i)
    row$group <- groups[i]
    row
  })

  build_response(
    "nmds",
    summary = list(stress = nmds$stress, dimensions = k, distance_method = dist_method,
                   n_samples = nrow(mat), converged = nmds$converged),
    tables = list(scores = scores)
  )
}

handle_rda <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params
  .do_constrained_ordination(df, params, method = "rda")
}

handle_cca <- function(req) {
  body <- parse_body(req)
  df <- parse_data(body)
  params <- body$params
  .do_constrained_ordination(df, params, method = "cca")
}

.do_constrained_ordination <- function(df, params, method = "rda") {
  if (!requireNamespace("vegan", quietly = TRUE))
    stop(paste("Package 'vegan' is required for", toupper(method)))

  species_cols <- params$species_columns
  env_cols <- params$env_columns
  group_col <- params$group_column

  if (is.null(species_cols) || is.null(env_cols))
    stop("params.species_columns and params.env_columns are required")

  sp_mat <- as.data.frame(lapply(df[, species_cols, drop = FALSE], as.numeric))
  env_mat <- as.data.frame(lapply(df[, env_cols, drop = FALSE], as.numeric))
  complete <- stats::complete.cases(sp_mat, env_mat)
  sp_mat <- sp_mat[complete, , drop = FALSE]
  env_mat <- env_mat[complete, , drop = FALSE]

  ord <- if (method == "rda") vegan::rda(sp_mat ~ ., data = env_mat)
         else vegan::cca(sp_mat ~ ., data = env_mat)

  prefix <- toupper(method)
  eig <- ord$CCA$eig
  explained <- eig / sum(eig)
  n_ax <- min(length(eig), 5)

  eigenvalues <- lapply(seq_len(n_ax), function(i) {
    list(axis = paste0(prefix, i), eigenvalue = eig[i],
         explained_variance = explained[i],
         cumulative = sum(explained[seq_len(i)]))
  })

  site_sc <- vegan::scores(ord, display = "sites", choices = seq_len(n_ax))
  groups <- if (!is.null(group_col) && group_col %in% names(df)) {
    as.character(df[[group_col]])[complete]
  } else rep("default", nrow(site_sc))

  site_scores <- lapply(seq_len(nrow(site_sc)), function(i) {
    row <- as.list(site_sc[i, ])
    row$sample_id <- as.character(i)
    row$group <- groups[i]
    row
  })

  bp_sc <- vegan::scores(ord, display = "bp", choices = seq_len(n_ax))
  biplot_scores <- lapply(seq_len(nrow(bp_sc)), function(i) {
    row <- as.list(bp_sc[i, ])
    row$variable <- rownames(bp_sc)[i]
    row
  })

  build_response(
    method,
    summary = list(
      method = toupper(method),
      n_samples = nrow(sp_mat),
      n_species = ncol(sp_mat),
      n_env = ncol(env_mat),
      total_constrained_variance = sum(eig),
      total_variance = ord$tot.chi
    ),
    tables = list(
      eigenvalues = eigenvalues,
      site_scores = site_scores,
      biplot_scores = biplot_scores
    )
  )
}
