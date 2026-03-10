#* PCA (Principal Component Analysis)
#* @post /ordination/pca
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params

    columns <- if (!is.null(params$columns)) as.character(unlist(params$columns)) else NULL
    sample_id_col <- params$sample_id_column
    group_col <- params$group_column

    prep <- prepare_species_matrix(df, columns, sample_id_col)
    mat <- prep$mat
    if (ncol(mat) < 2) stop("PCA requires at least 2 numeric columns")
    if (nrow(mat) < 3) stop("Not enough rows for PCA")

    scale_mode <- tolower(params$scale_mode %||% "scale")
    n_comp <- min(as.integer(params$components %||% 5), ncol(mat), nrow(mat) - 1)

    fit <- stats::prcomp(mat,
      center = scale_mode %in% c("center", "scale"),
      scale. = scale_mode == "scale"
    )

    var_eig <- fit$sdev^2
    eigen_rows <- eigenvalue_table(var_eig, "PC")

    scores <- fit$x[, seq_len(n_comp), drop = FALSE]
    score_rows <- score_matrix_to_rows(scores, "sample_id", prep$sample_ids)

    loadings <- fit$rotation[, seq_len(n_comp), drop = FALSE]
    loading_rows <- score_matrix_to_rows(loadings, "variable", rownames(loadings))

    groups <- NULL
    ellipses <- NULL
    if (!is.null(group_col) && group_col %in% names(df)) {
      groups <- as.character(df[[group_col]])[seq_len(nrow(mat))]
      for (i in seq_along(score_rows)) score_rows[[i]]$group <- groups[i]
      ellipses <- compute_group_ellipses(scores, groups)
    }

    build_response(
      analysis_type = "pca",
      summary = list(
        method = "PCA (prcomp)",
        n_samples = nrow(mat),
        n_variables = ncol(mat),
        scale_mode = scale_mode,
        components_returned = n_comp
      ),
      tables = list(
        eigenvalues = eigen_rows,
        scores = score_rows,
        loadings = loading_rows,
        ellipses = ellipses
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* PCoA (Principal Coordinates Analysis)
#* @post /ordination/pcoa
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params

    columns <- if (!is.null(params$columns)) as.character(unlist(params$columns)) else NULL
    sample_id_col <- params$sample_id_column
    group_col <- params$group_column
    dist_method <- normalize_distance(params$distance)

    prep <- prepare_species_matrix(df, columns, sample_id_col)
    mat <- prep$mat
    if (nrow(mat) < 3) stop("Not enough rows for PCoA")

    dist_mat <- vegan::vegdist(mat, method = dist_method)
    pcoa_fit <- stats::cmdscale(dist_mat, k = min(nrow(mat) - 1, 5), eig = TRUE)

    n_axes <- ncol(pcoa_fit$points)
    colnames(pcoa_fit$points) <- paste0("PCoA", seq_len(n_axes))

    pos_eig <- pcoa_fit$eig[pcoa_fit$eig > 0]
    eigen_rows <- eigenvalue_table(pos_eig, "PCoA")

    score_rows <- score_matrix_to_rows(pcoa_fit$points, "sample_id", prep$sample_ids)

    groups <- NULL
    ellipses <- NULL
    if (!is.null(group_col) && group_col %in% names(df)) {
      groups <- as.character(df[[group_col]])[seq_len(nrow(mat))]
      for (i in seq_along(score_rows)) score_rows[[i]]$group <- groups[i]
      ellipses <- compute_group_ellipses(pcoa_fit$points, groups)
    }

    build_response(
      analysis_type = "pcoa",
      summary = list(
        method = "PCoA (cmdscale)",
        distance = dist_method,
        n_samples = nrow(mat),
        n_variables = ncol(mat),
        axes_returned = n_axes
      ),
      tables = list(
        eigenvalues = eigen_rows,
        scores = score_rows,
        ellipses = ellipses
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* NMDS (Non-metric Multidimensional Scaling)
#* @post /ordination/nmds
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    df <- load_data(body)
    params <- body$params

    columns <- if (!is.null(params$columns)) as.character(unlist(params$columns)) else NULL
    sample_id_col <- params$sample_id_column
    group_col <- params$group_column
    dist_method <- normalize_distance(params$distance)
    k <- as.integer(params$dimensions %||% 2)

    prep <- prepare_species_matrix(df, columns, sample_id_col)
    mat <- prep$mat
    if (nrow(mat) < 3) stop("Not enough rows for NMDS")

    nmds_fit <- vegan::metaMDS(mat, distance = dist_method, k = k,
                               trymax = 100, trace = 0)

    scores_mat <- vegan::scores(nmds_fit, display = "sites")
    colnames(scores_mat) <- paste0("NMDS", seq_len(ncol(scores_mat)))
    score_rows <- score_matrix_to_rows(scores_mat, "sample_id", prep$sample_ids)

    species_scores <- NULL
    tryCatch({
      sp <- vegan::scores(nmds_fit, display = "species")
      colnames(sp) <- paste0("NMDS", seq_len(ncol(sp)))
      species_scores <- score_matrix_to_rows(sp, "species", rownames(sp))
    }, error = function(e) NULL)

    groups <- NULL
    ellipses <- NULL
    if (!is.null(group_col) && group_col %in% names(df)) {
      groups <- as.character(df[[group_col]])[seq_len(nrow(mat))]
      for (i in seq_along(score_rows)) score_rows[[i]]$group <- groups[i]
      ellipses <- compute_group_ellipses(scores_mat, groups)
    }

    build_response(
      analysis_type = "nmds",
      summary = list(
        method = "NMDS (metaMDS)",
        distance = dist_method,
        dimensions = k,
        stress = as.numeric(nmds_fit$stress),
        n_samples = nrow(mat),
        n_variables = ncol(mat),
        converged = nmds_fit$converged
      ),
      tables = list(
        scores = score_rows,
        species_scores = species_scores,
        ellipses = ellipses
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* RDA (Redundancy Analysis)
#* @post /ordination/rda
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    params <- body$params
    validate_required(params, c("species_columns", "env_columns"))

    df <- load_data(body)
    sample_id_col <- params$sample_id_column
    group_col <- params$group_column

    species_cols <- as.character(unlist(params$species_columns))
    env_cols <- as.character(unlist(params$env_columns))
    validate_columns(df, c(species_cols, env_cols))

    if (!is.null(sample_id_col) && sample_id_col %in% names(df)) {
      row_ids <- as.character(df[[sample_id_col]])
    } else {
      row_ids <- as.character(seq_len(nrow(df)))
    }

    sp_mat <- df[, species_cols, drop = FALSE]
    for (nm in names(sp_mat)) sp_mat[[nm]] <- suppressWarnings(as.numeric(sp_mat[[nm]]))

    env_mat <- df[, env_cols, drop = FALSE]
    for (nm in names(env_mat)) env_mat[[nm]] <- suppressWarnings(as.numeric(env_mat[[nm]]))

    complete <- stats::complete.cases(sp_mat) & stats::complete.cases(env_mat)
    sp_mat <- sp_mat[complete, , drop = FALSE]
    env_mat <- env_mat[complete, , drop = FALSE]
    row_ids <- row_ids[complete]
    if (nrow(sp_mat) < 3) stop("Not enough complete rows for RDA")

    rda_fit <- vegan::rda(sp_mat ~ ., data = env_mat)
    rda_sum <- summary(rda_fit)

    site_scores <- vegan::scores(rda_fit, display = "sites", scaling = 2)
    colnames(site_scores) <- paste0("RDA", seq_len(ncol(site_scores)))
    site_rows <- score_matrix_to_rows(site_scores, "sample_id", row_ids)

    sp_scores <- vegan::scores(rda_fit, display = "species", scaling = 2)
    colnames(sp_scores) <- paste0("RDA", seq_len(ncol(sp_scores)))
    sp_rows <- score_matrix_to_rows(sp_scores, "species", rownames(sp_scores))

    bp_scores <- vegan::scores(rda_fit, display = "bp", scaling = 2)
    colnames(bp_scores) <- paste0("RDA", seq_len(ncol(bp_scores)))
    bp_rows <- score_matrix_to_rows(bp_scores, "variable", rownames(bp_scores))

    eig <- rda_fit$CCA$eig
    eigen_rows <- eigenvalue_table(eig, "RDA")

    perm_test <- NULL
    tryCatch({
      perm <- vegan::anova.cca(rda_fit, permutations = 999)
      perm_test <- list(
        f_value = safe_num(perm[1, "F"]),
        p_value = safe_num(perm[1, "Pr(>F)"]),
        permutations = 999
      )
    }, error = function(e) NULL)

    groups <- NULL
    ellipses <- NULL
    if (!is.null(group_col) && group_col %in% names(df)) {
      groups <- as.character(df[[group_col]])[complete]
      for (i in seq_along(site_rows)) site_rows[[i]]$group <- groups[i]
      ellipses <- compute_group_ellipses(site_scores, groups)
    }

    build_response(
      analysis_type = "rda",
      summary = list(
        method = "RDA (vegan::rda)",
        n_samples = nrow(sp_mat),
        n_species = ncol(sp_mat),
        n_env = ncol(env_mat),
        constrained_variance = as.numeric(rda_fit$CCA$tot.chi),
        total_variance = as.numeric(rda_fit$tot.chi),
        proportion_constrained = as.numeric(rda_fit$CCA$tot.chi / rda_fit$tot.chi),
        permutation_test = perm_test
      ),
      tables = list(
        eigenvalues = eigen_rows,
        site_scores = site_rows,
        species_scores = sp_rows,
        biplot_scores = bp_rows,
        ellipses = ellipses
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}

#* CCA (Canonical Correspondence Analysis)
#* @post /ordination/cca
#* @serializer unboxedJSON
function(req, res) {
  tryCatch({
    body <- req$body
    params <- body$params
    validate_required(params, c("species_columns", "env_columns"))

    df <- load_data(body)
    sample_id_col <- params$sample_id_column
    group_col <- params$group_column

    species_cols <- as.character(unlist(params$species_columns))
    env_cols <- as.character(unlist(params$env_columns))
    validate_columns(df, c(species_cols, env_cols))

    if (!is.null(sample_id_col) && sample_id_col %in% names(df)) {
      row_ids <- as.character(df[[sample_id_col]])
    } else {
      row_ids <- as.character(seq_len(nrow(df)))
    }

    sp_mat <- df[, species_cols, drop = FALSE]
    for (nm in names(sp_mat)) sp_mat[[nm]] <- suppressWarnings(as.numeric(sp_mat[[nm]]))

    env_mat <- df[, env_cols, drop = FALSE]
    for (nm in names(env_mat)) env_mat[[nm]] <- suppressWarnings(as.numeric(env_mat[[nm]]))

    complete <- stats::complete.cases(sp_mat) & stats::complete.cases(env_mat)
    sp_mat <- sp_mat[complete, , drop = FALSE]
    env_mat <- env_mat[complete, , drop = FALSE]
    row_ids <- row_ids[complete]
    if (nrow(sp_mat) < 3) stop("Not enough complete rows for CCA")

    cca_fit <- vegan::cca(sp_mat ~ ., data = env_mat)

    site_scores <- vegan::scores(cca_fit, display = "sites", scaling = 2)
    colnames(site_scores) <- paste0("CCA", seq_len(ncol(site_scores)))
    site_rows <- score_matrix_to_rows(site_scores, "sample_id", row_ids)

    sp_scores <- vegan::scores(cca_fit, display = "species", scaling = 2)
    colnames(sp_scores) <- paste0("CCA", seq_len(ncol(sp_scores)))
    sp_rows <- score_matrix_to_rows(sp_scores, "species", rownames(sp_scores))

    bp_scores <- vegan::scores(cca_fit, display = "bp", scaling = 2)
    colnames(bp_scores) <- paste0("CCA", seq_len(ncol(bp_scores)))
    bp_rows <- score_matrix_to_rows(bp_scores, "variable", rownames(bp_scores))

    eig <- cca_fit$CCA$eig
    eigen_rows <- eigenvalue_table(eig, "CCA")

    perm_test <- NULL
    tryCatch({
      perm <- vegan::anova.cca(cca_fit, permutations = 999)
      perm_test <- list(
        f_value = safe_num(perm[1, "F"]),
        p_value = safe_num(perm[1, "Pr(>F)"]),
        permutations = 999
      )
    }, error = function(e) NULL)

    groups <- NULL
    ellipses <- NULL
    if (!is.null(group_col) && group_col %in% names(df)) {
      groups <- as.character(df[[group_col]])[complete]
      for (i in seq_along(site_rows)) site_rows[[i]]$group <- groups[i]
      ellipses <- compute_group_ellipses(site_scores, groups)
    }

    build_response(
      analysis_type = "cca",
      summary = list(
        method = "CCA (vegan::cca)",
        n_samples = nrow(sp_mat),
        n_species = ncol(sp_mat),
        n_env = ncol(env_mat),
        constrained_inertia = as.numeric(cca_fit$CCA$tot.chi),
        total_inertia = as.numeric(cca_fit$tot.chi),
        proportion_constrained = as.numeric(cca_fit$CCA$tot.chi / cca_fit$tot.chi),
        permutation_test = perm_test
      ),
      tables = list(
        eigenvalues = eigen_rows,
        site_scores = site_rows,
        species_scores = sp_rows,
        biplot_scores = bp_rows,
        ellipses = ellipses
      )
    )
  }, error = function(e) {
    validation_error(res, conditionMessage(e))
  })
}
