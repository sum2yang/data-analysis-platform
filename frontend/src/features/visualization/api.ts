import { apiClient } from '@/api/client'
import type { ChartContract, ExportRequest } from './types'

export async function fetchChartContracts(runId: string): Promise<ChartContract[]> {
  const res = await apiClient.get<ChartContract[]>(`/analysis/runs/${runId}/charts`)
  return res.data
}

export async function exportChart(request: ExportRequest): Promise<Blob> {
  const res = await apiClient.post('/exports/chart', request, {
    responseType: 'blob',
  })
  return res.data
}

export async function exportTable(runId: string, tableName: string, format: 'csv' | 'xlsx'): Promise<Blob> {
  const res = await apiClient.get(`/exports/table/${runId}/${tableName}`, {
    params: { format },
    responseType: 'blob',
  })
  return res.data
}
