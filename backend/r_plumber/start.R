#!/usr/bin/env Rscript
# Start the R Plumber API server
# Usage: Rscript start.R [port]
# Run from: backend/r_plumber/ directory

suppressPackageStartupMessages({
  library(plumber)
  library(jsonlite)
})

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("--file=", "", args_all[grep("--file=", args_all)])
if (length(file_arg) > 0) {
  script_dir <- dirname(normalizePath(file_arg))
} else {
  script_dir <- getwd()
}

args <- commandArgs(trailingOnly = TRUE)
port <- if (length(args) >= 1) as.integer(args[1]) else 8787L

r_dir <- file.path(script_dir, "R")

cat("Loading handler modules from:", r_dir, "\n")
for (f in list.files(r_dir, pattern = "\\.R$", full.names = TRUE)) {
  source(f, local = FALSE)
  cat("  Loaded:", basename(f), "\n")
}

plumber_file <- file.path(script_dir, "plumber.R")
cat("Starting R Plumber API on port", port, "...\n")

pr <- plumber::plumb(plumber_file)
pr$run(host = "0.0.0.0", port = port)
