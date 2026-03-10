import { ResultCard } from '@/components/ResultCard'
import { ResultTable } from '@/components/ResultTable'
import { ChartPanel } from '@/features/visualization/ChartPanel'
import type { ChartContract } from '@/features/visualization/types'
import type { AnalysisRunDetail } from '@/features/analysis/types'

interface AnalysisResultsProps {
  result: AnalysisRunDetail | null
  highlightPValue?: boolean
}

export function AnalysisResults({ result, highlightPValue = true }: AnalysisResultsProps) {
  const tables = result?.result?.tables
    ? Object.entries(result.result.tables).map(([title, data]) => ({
        title,
        columns: data.length > 0 ? Object.keys(data[0] as Record<string, unknown>) : [],
        data: data as Record<string, unknown>[],
      }))
    : []

  const chartContracts = (result?.result?.chart_contracts ?? []) as unknown as ChartContract[]

  return (
    <>
      {tables.map((table) => (
        <ResultCard key={table.title} title={table.title}>
          <ResultTable result={table} highlightPValue={highlightPValue} />
        </ResultCard>
      ))}
      {chartContracts.length > 0 && <ChartPanel contracts={chartContracts} />}
      {result?.result?.warnings && result.result.warnings.length > 0 && (
        <ResultCard title="警告">
          <ul>
            {result.result.warnings.map((w, i) => (
              <li key={i} style={{ color: '#faad14' }}>{w}</li>
            ))}
          </ul>
        </ResultCard>
      )}
    </>
  )
}
