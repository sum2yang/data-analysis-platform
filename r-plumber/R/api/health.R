#* Health check
#* @get /health
#* @serializer unboxedJSON
function(req, res) {
  list(
    status = "ok",
    engine = "R",
    version = as.character(getRversion()),
    timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z")
  )
}
