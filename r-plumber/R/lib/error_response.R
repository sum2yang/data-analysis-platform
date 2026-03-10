error_response <- function(res, status, message, details = NULL) {
  res$status <- status
  body <- list(
    error = TRUE,
    message = message
  )
  if (!is.null(details)) {
    body$details <- details
  }
  body
}

validation_error <- function(res, message, details = NULL) {
  error_response(res, 422L, message, details)
}

not_found_error <- function(res, message = "Resource not found") {
  error_response(res, 404L, message)
}

internal_error <- function(res, message = "Internal server error", details = NULL) {
  error_response(res, 500L, message, details)
}
