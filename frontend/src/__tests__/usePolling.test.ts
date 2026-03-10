import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { usePolling } from '@/hooks/usePolling'

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls callback immediately on mount if enabled', () => {
    const callback = vi.fn()
    renderHook(() => usePolling(callback, 1000, true))
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('calls callback at specified interval', () => {
    const callback = vi.fn()
    renderHook(() => usePolling(callback, 1000, true))

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(2)

    vi.advanceTimersByTime(2000)
    expect(callback).toHaveBeenCalledTimes(4)
  })

  it('does not call callback when disabled', () => {
    const callback = vi.fn()
    renderHook(() => usePolling(callback, 1000, false))

    vi.advanceTimersByTime(3000)
    expect(callback).toHaveBeenCalledTimes(0)
  })

  it('stops polling when enabled becomes false', () => {
    const callback = vi.fn()
    const { rerender } = renderHook(
      ({ enabled }) => usePolling(callback, 1000, enabled),
      { initialProps: { enabled: true } },
    )

    expect(callback).toHaveBeenCalledTimes(1)
    rerender({ enabled: false })

    vi.advanceTimersByTime(2000)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('stop function clears the interval', () => {
    const callback = vi.fn()
    const { result } = renderHook(() => usePolling(callback, 1000, true))

    result.current.stop()
    vi.advanceTimersByTime(2000)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('updates callback reference without resetting timer', () => {
    const callback1 = vi.fn()
    const callback2 = vi.fn()
    const { rerender } = renderHook(
      ({ cb }) => usePolling(cb, 1000, true),
      { initialProps: { cb: callback1 } },
    )

    vi.advanceTimersByTime(500)
    rerender({ cb: callback2 })

    vi.advanceTimersByTime(500)
    expect(callback1).toHaveBeenCalledTimes(1)
    expect(callback2).toHaveBeenCalledTimes(1)
  })
})
