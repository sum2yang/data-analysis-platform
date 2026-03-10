import { useEffect, useRef, useCallback } from 'react'

export function usePolling(
  callback: () => void | Promise<void>,
  interval: number,
  enabled = true,
) {
  const savedCallback = useRef(callback)
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = undefined
    }
  }, [])

  useEffect(() => {
    if (!enabled) {
      stop()
      return
    }
    savedCallback.current()
    timerRef.current = setInterval(() => savedCallback.current(), interval)
    return stop
  }, [interval, enabled, stop])

  return { stop }
}
