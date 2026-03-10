import { useRef, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import type { ECharts } from 'echarts'

interface GenericChartProps {
  option: Record<string, unknown>
  height?: number | string
  loading?: boolean
  onChartReady?: (chart: ECharts) => void
}

export function GenericChart({
  option,
  height = 400,
  loading = false,
  onChartReady,
}: GenericChartProps) {
  const chartRef = useRef<ReactECharts>(null)

  useEffect(() => {
    const handleResize = () => {
      chartRef.current?.getEchartsInstance()?.resize()
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <ReactECharts
      ref={chartRef}
      option={option}
      style={{ height, width: '100%' }}
      showLoading={loading}
      onChartReady={onChartReady}
      notMerge
      lazyUpdate
    />
  )
}
