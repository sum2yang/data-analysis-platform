import { GenericChart } from '@/components/GenericChart'
import { contractToEChartsOption } from '@/utils/chartTransform'
import type { ChartContract } from '../types'

interface BoxplotChartProps {
  contract: ChartContract
  height?: number
  onChartReady?: (chart: import('echarts').ECharts) => void
}

export function BoxplotChart({ contract, height = 400, onChartReady }: BoxplotChartProps) {
  const option = contractToEChartsOption(contract)
  return <GenericChart option={option} height={height} onChartReady={onChartReady} />
}
