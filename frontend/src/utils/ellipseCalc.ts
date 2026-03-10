export function computeEllipse(
  points: [number, number][],
  confidence = 0.95,
  nPoints = 100,
): [number, number][] {
  if (points.length < 3) return []

  const n = points.length
  const meanX = points.reduce((s, p) => s + p[0], 0) / n
  const meanY = points.reduce((s, p) => s + p[1], 0) / n

  let sxx = 0, syy = 0, sxy = 0
  for (const [x, y] of points) {
    const dx = x - meanX
    const dy = y - meanY
    sxx += dx * dx
    syy += dy * dy
    sxy += dx * dy
  }
  sxx /= n - 1
  syy /= n - 1
  sxy /= n - 1

  const trace = sxx + syy
  const det = sxx * syy - sxy * sxy
  const disc = Math.sqrt(Math.max(0, trace * trace / 4 - det))
  const lambda1 = trace / 2 + disc
  const lambda2 = trace / 2 - disc

  if (lambda1 <= 0 || lambda2 <= 0) return []

  const chiSq = -2 * Math.log(1 - confidence)
  const a = Math.sqrt(chiSq * lambda1)
  const b = Math.sqrt(chiSq * lambda2)

  let angle = 0
  if (sxy !== 0) {
    angle = Math.atan2(lambda1 - sxx, sxy)
  } else if (sxx >= syy) {
    angle = 0
  } else {
    angle = Math.PI / 2
  }

  const result: [number, number][] = []
  for (let i = 0; i < nPoints; i++) {
    const t = (2 * Math.PI * i) / nPoints
    const cosT = Math.cos(t)
    const sinT = Math.sin(t)
    const x = a * cosT * Math.cos(angle) - b * sinT * Math.sin(angle) + meanX
    const y = a * cosT * Math.sin(angle) + b * sinT * Math.cos(angle) + meanY
    result.push([x, y])
  }
  result.push(result[0])

  return result
}
