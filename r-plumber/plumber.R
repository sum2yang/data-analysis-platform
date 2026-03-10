library(plumber)

root_dir <- getwd()
source(file.path(root_dir, "R", "lib", "bootstrap.R"))
bootstrap(root_dir)

pr <- plumber$new()

pr$handle("GET", "/", function(req, res) {
  res$serializer <- serializer_unboxed_json()
  list(
    service = "R Plumber Analysis API",
    version = "1.0.0",
    endpoints = list(
      "/health",
      "/descriptive",
      "/assumptions",
      "/t-test",
      "/anova/one-way",
      "/anova/multi-way",
      "/anova/welch",
      "/nonparametric/kruskal-wallis",
      "/nonparametric/mann-whitney",
      "/correlation",
      "/regression/linear",
      "/regression/glm",
      "/ordination/pca",
      "/ordination/pcoa",
      "/ordination/nmds",
      "/ordination/rda",
      "/ordination/cca"
    )
  )
})

mount_endpoint <- function(pr, prefix, file_path) {
  if (file.exists(file_path)) {
    child <- plumber$new(file_path)
    pr$mount(prefix, child)
  } else {
    warning(paste0("Endpoint file not found: ", file_path))
  }
}

api_dir <- file.path(root_dir, "R", "api")

mount_endpoint(pr, "/", file.path(api_dir, "health.R"))
mount_endpoint(pr, "/", file.path(api_dir, "descriptive.R"))
mount_endpoint(pr, "/", file.path(api_dir, "assumptions.R"))
mount_endpoint(pr, "/", file.path(api_dir, "difference.R"))
mount_endpoint(pr, "/", file.path(api_dir, "regression.R"))
mount_endpoint(pr, "/", file.path(api_dir, "ordination.R"))

pr$registerHooks(list(
  preroute = function(data, req, res) {
    data$request_start <- Sys.time()
  },
  postroute = function(data, req, res) {
    elapsed <- as.numeric(difftime(Sys.time(), data$request_start, units = "secs"))
    res$setHeader("X-Response-Time", paste0(round(elapsed * 1000), "ms"))
  }
))

pr$setErrorHandler(function(req, res, err) {
  res$status <- 500L
  list(
    error = TRUE,
    message = conditionMessage(err)
  )
})

host <- Sys.getenv("PLUMBER_HOST", "0.0.0.0")
port <- as.integer(Sys.getenv("PLUMBER_PORT", "8787"))

cat(sprintf("Starting R Plumber API on %s:%d\n", host, port))
pr$run(host = host, port = port)
