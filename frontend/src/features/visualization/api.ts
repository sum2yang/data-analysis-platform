import { apiClient } from '@/api/client'
import type { ChartContract, ExportRequest } from './types'
import type { AnalysisResultEnvelope } from '@/features/analysis/types'

/**
 * Fetch chart contracts for a given analysis run.
 * Charts are embedded in the result envelope at result.chart_contracts.
 */
export async function fetchChartContracts(runId: string): Promise<ChartContract[]> {
  const res = await apiClient.get<AnalysisResultEnvelope>(
    `/analysis-runs/${runId}/result`,
  )
  const contracts = res.data.chart_contracts ?? []
  return contracts as ChartContract[]
}

/**
 * Request a server-side chart export (matplotlib).
 * Backend: POST /exports/figures with {run_id, chart_index, format}
 */
export async function exportChart(request: ExportRequest): Promise<{ id: string; status: string }> {
  const res = await apiClient.post('/exports/figures', {
    run_id: request.run_id,
    chart_index: request.chart_index ?? 0,
    format: request.format,
  })
  return res.data
}

/**
 * Request a server-side table export.
 * Backend: POST /exports/tables with {run_id, table_key, format}
 */
export async function exportTable(
  runId: string,
  tableName: string,
  format: 'csv' | 'xlsx',
): Promise<{ id: string; status: string }> {
  const res = await apiClient.post('/exports/tables', {
    run_id: runId,
    table_key: tableName,
    format,
  })
  return res.data
}

/**
 * Download a completed export file.
 * Backend: GET /exports/{export_id}/download
 */
export async function downloadExport(exportId: string): Promise<Blob> {
  const res = await apiClient.get(`/exports/${exportId}/download`, {
    responseType: 'blob',
  })
  return res.data
}
