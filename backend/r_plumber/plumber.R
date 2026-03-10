# Data Analysis Platform - R Plumber API
# All analysis endpoints matching ANALYSIS_TYPE_TO_ENDPOINT in analysis_tasks.py
#
# Handler modules (R/*.R) are pre-loaded by start.R before plumb() is called.
# Do NOT add library() or source() calls here - Plumber parses this file for
# annotated endpoints only.

#* @get /health
#* @serializer unboxedJSON
function() {
  list(status = "ok")
}

#* @post /descriptive
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_descriptive(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /assumptions
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_assumptions(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /t-test
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_t_test(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /anova/one-way
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_anova_one_way(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /anova/multi-way
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_anova_multi_way(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /anova/welch
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_anova_welch(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /nonparametric/kruskal-wallis
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_kruskal_wallis(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /nonparametric/mann-whitney
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_mann_whitney(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /correlation
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_correlation(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /regression/linear
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_regression_linear(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /regression/glm
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_regression_glm(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /ordination/pca
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_pca(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /ordination/pcoa
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_pcoa(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /ordination/nmds
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_nmds(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /ordination/rda
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_rda(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}

#* @post /ordination/cca
#* @serializer unboxedJSON
function(req, res) {
  tryCatch(
    handle_cca(req),
    error = function(e) {
      res$status <- 400L
      list(error = conditionMessage(e))
    }
  )
}
