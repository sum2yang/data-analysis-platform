import { apiClient } from '@/api/client'
import type { AnalysisRunAccepted, AnalysisRunDetail, AnalysisRunStatus } from './types'

export async function submitAnalysis(
  datasetId: string,
  analysisType: string,
  params: Record<string, unknown>,
): Promise<AnalysisRunAccepted> {
  const res = await apiClient.post<AnalysisRunAccepted>('/analysis/run', {
    dataset_id: datasetId,
    analysis_type: analysisType,
    params,
  })
  return res.data
}

export async function fetchAnalysisStatus(runId: string): Promise<AnalysisRunStatus> {
  const res = await apiClient.get<AnalysisRunStatus>(`/analysis/runs/${runId}/status`)
  return res.data
}

export async function fetchAnalysisResult(runId: string): Promise<AnalysisRunDetail> {
  const res = await apiClient.get<AnalysisRunDetail>(`/analysis/runs/${runId}`)
  return res.data
}

export async function fetchAnalysisHistory(
  datasetId: string,
  analysisType?: string,
): Promise<AnalysisRunStatus[]> {
  const res = await apiClient.get<AnalysisRunStatus[]>('/analysis/runs', {
    params: { dataset_id: datasetId, analysis_type: analysisType },
  })
  return res.data
}
