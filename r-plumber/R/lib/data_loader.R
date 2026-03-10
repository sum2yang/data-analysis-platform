load_data <- function(body) {
  if (!is.null(body$data)) {
    df <- tryCatch(
      as.data.frame(body$data, stringsAsFactors = FALSE),
      error = function(e) NULL
    )
    if (is.null(df)) stop("Invalid inline data format")
    return(df)
  }

  if (!is.null(body$manifest)) {
    path <- body$manifest$path
    fmt <- tolower(body$manifest$format %||% "csv")
    if (is.null(path)) stop("manifest.path is required")
    path <- normalizePath(path, mustWork = FALSE)
    allowed_root <- normalizePath(Sys.getenv("DATA_ROOT", "./data"), mustWork = FALSE)
    if (!startsWith(path, allowed_root)) {
      stop("Access denied: manifest path outside allowed directory")
    }
    if (!file.exists(path)) stop(paste0("File not found: ", path))

    df <- switch(fmt,
      csv = utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE),
      tsv = utils::read.delim(path, stringsAsFactors = FALSE, check.names = FALSE),
      stop(paste0("Unsupported format: ", fmt))
    )
    return(df)
  }

  stop("Request must contain 'data' (inline) or 'manifest' (file reference)")
}

validate_columns <- function(df, required_cols, context = "data") {
  missing <- setdiff(required_cols, names(df))
  if (length(missing) > 0) {
    stop(paste0(
      "Missing required columns in ", context, ": ",
      paste(missing, collapse = ", ")
    ))
  }
  invisible(TRUE)
}
