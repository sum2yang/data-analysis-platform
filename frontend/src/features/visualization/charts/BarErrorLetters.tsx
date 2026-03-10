import { GenericChart } from '@/components/GenericChart'
import { contractToEChartsOption } from '@/utils/chartTransform'
import type { ChartContract } from '../types'

interface BarErrorLettersProps {
  contract: ChartContract
  height?: number
  onChartReady?: (chart: import('echarts').ECharts) => void
}

export function BarErrorLetters({ contract, height = 400, onChartReady }: BarErrorLettersProps) {
  const option = contractToEChartsOption(contract)
  return <GenericChart option={option} height={height} onChartReady={onChartReady} />
}
