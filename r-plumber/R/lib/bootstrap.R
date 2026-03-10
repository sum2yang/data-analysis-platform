bootstrap <- function(root_dir = NULL) {
  if (is.null(root_dir)) {
    root_dir <- getwd()
  }

  # Define null-coalesce operator
  `%||%` <<- function(x, y) if (is.null(x)) y else x

  # Column name sanitizer to prevent formula injection
  sanitize_colnames <<- function(df) {
    original <- names(df)
    safe <- make.names(original, unique = TRUE)
    names(df) <- safe
    attr(df, "original_names") <- original
    attr(df, "name_map") <- stats::setNames(original, safe)
    df
  }

  safe_colname <<- function(name) {
    safe <- make.names(name)
    if (safe != name) {
      if (grepl("[`$(){}|;&]", name)) {
        stop(paste0("Invalid column name (contains unsafe characters): ", name))
      }
    }
    safe
  }

  options(
    scipen = 999,
    warn = 1,
    stringsAsFactors = FALSE
  )

  lib_dir <- file.path(root_dir, "R", "lib")
  lib_files <- c(
    "error_response.R",
    "response_builder.R",
    "data_loader.R",
    "request_validation.R",
    "posthoc_letters.R",
    "ordination_helpers.R"
  )

  for (f in lib_files) {
    path <- file.path(lib_dir, f)
    if (file.exists(path)) {
      source(path, local = FALSE)
    } else {
      warning(paste0("Lib file not found: ", path))
    }
  }

  suppressWarnings(suppressMessages({
    library(jsonlite)
  }))

  invisible(TRUE)
}
