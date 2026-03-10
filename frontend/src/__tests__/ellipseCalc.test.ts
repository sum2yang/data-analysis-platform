import { describe, it, expect } from 'vitest'
import { computeEllipse } from '@/utils/ellipseCalc'

describe('ellipseCalc', () => {
  it('returns empty array for fewer than 3 points', () => {
    expect(computeEllipse([[0, 0], [1, 1]])).toEqual([])
    expect(computeEllipse([[0, 0]])).toEqual([])
    expect(computeEllipse([])).toEqual([])
  })

  it('returns empty array for degenerate points (all same location)', () => {
    expect(computeEllipse([[0, 0], [0, 0], [0, 0]])).toEqual([])
  })

  it('computes correct number of points for known data', () => {
    const points: [number, number][] = [[0, 0], [1, 1], [2, 0]]
    const nPoints = 50
    const ellipse = computeEllipse(points, 0.95, nPoints)

    expect(ellipse).toHaveLength(nPoints + 1)
    expect(ellipse[0]).toEqual(ellipse[nPoints])
  })

  it('uses default nPoints=100 and confidence=0.95', () => {
    const points: [number, number][] = [[0, 0], [10, 0], [0, 10]]
    const ellipse = computeEllipse(points)
    expect(ellipse).toHaveLength(101)
  })

  it('handles axis-aligned data correctly', () => {
    const points: [number, number][] = [[-1, 0], [1, 0], [0, -1], [0, 1]]
    const ellipse = computeEllipse(points)
    expect(ellipse.length).toBeGreaterThan(0)
  })

  it('respects nPoints parameter', () => {
    const points: [number, number][] = [[0, 0], [10, 0], [0, 10]]
    const nPoints = 20
    const ellipse = computeEllipse(points, 0.95, nPoints)
    expect(ellipse).toHaveLength(21)
  })

  it('ellipse center is near the mean of input points', () => {
    const points: [number, number][] = [[0, 0], [10, 0], [0, 10], [10, 10]]
    const ellipse = computeEllipse(points, 0.95, 100)
    const meanX = ellipse.slice(0, -1).reduce((s, p) => s + p[0], 0) / 100
    const meanY = ellipse.slice(0, -1).reduce((s, p) => s + p[1], 0) / 100
    expect(meanX).toBeCloseTo(5, 0)
    expect(meanY).toBeCloseTo(5, 0)
  })
})
