validate_required <- function(params, required_fields, context = "params") {
  if (is.null(params)) stop(paste0(context, " is required"))
  missing <- character(0)
  for (f in required_fields) {
    if (is.null(params[[f]])) missing <- c(missing, f)
  }
  if (length(missing) > 0) {
    stop(paste0("Missing required fields in ", context, ": ", paste(missing, collapse = ", ")))
  }
  invisible(TRUE)
}

validate_enum <- function(value, allowed, field_name) {
  if (is.null(value)) return(invisible(TRUE))
  val <- tolower(as.character(value))
  if (!(val %in% allowed)) {
    stop(paste0(
      field_name, " must be one of: ",
      paste(allowed, collapse = ", "),
      ". Got: ", val
    ))
  }
  invisible(TRUE)
}

validate_numeric_column <- function(df, col_name) {
  if (!(col_name %in% names(df))) stop(paste0("Column not found: ", col_name))
  vals <- suppressWarnings(as.numeric(df[[col_name]]))
  na_count <- sum(is.na(vals)) - sum(is.na(df[[col_name]]))
  if (na_count > 0) {
    stop(paste0("Column '", col_name, "' contains non-numeric values"))
  }
  invisible(TRUE)
}
