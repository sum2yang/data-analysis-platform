import { GenericChart } from '@/components/GenericChart'
import { contractToEChartsOption } from '@/utils/chartTransform'
import type { ChartContract } from '../types'

interface ViolinChartProps {
  contract: ChartContract
  height?: number
  onChartReady?: (chart: import('echarts').ECharts) => void
}

export function ViolinChart({ contract, height = 400, onChartReady }: ViolinChartProps) {
  const option = contractToEChartsOption(contract)
  return <GenericChart option={option} height={height} onChartReady={onChartReady} />
}
