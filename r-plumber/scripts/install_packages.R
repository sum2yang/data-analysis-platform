packages <- c(
  "plumber",
  "jsonlite",
  "agricolae",
  "vegan",
  "car",
  "PMCMRplus",
  "multcompView",
  "MASS"
)

for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

cat("All packages installed.\n")
