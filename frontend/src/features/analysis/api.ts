import { apiClient } from '@/api/client'
import type {
  AnalysisResultEnvelope,
  AnalysisRunAccepted,
  AnalysisRunDetail,
  AnalysisRunStatus,
} from './types'

export async function submitAnalysis(
  datasetId: string,
  analysisType: string,
  params: Record<string, unknown>,
): Promise<AnalysisRunAccepted> {
  const res = await apiClient.post<AnalysisRunAccepted>('/analyses/run', {
    dataset_id: datasetId,
    analysis_type: analysisType,
    params,
  })
  return res.data
}

export async function fetchAnalysisStatus(runId: string): Promise<AnalysisRunStatus> {
  const res = await apiClient.get<AnalysisRunStatus>(`/analysis-runs/${runId}`)
  return res.data
}

/**
 * Fetch run status + result envelope (if available) in a single call.
 * Callers use this for polling: they check status and access result when done.
 */
export async function fetchAnalysisResult(runId: string): Promise<AnalysisRunDetail> {
  const statusRes = await apiClient.get<AnalysisRunStatus>(`/analysis-runs/${runId}`)
  const status = statusRes.data

  let result: AnalysisResultEnvelope | null = null
  if (status.status === 'succeeded') {
    const resultRes = await apiClient.get<AnalysisResultEnvelope>(
      `/analysis-runs/${runId}/result`,
    )
    result = resultRes.data
  }

  return { ...status, result }
}

export async function fetchAnalysisHistory(
  page: number = 1,
  pageSize: number = 20,
): Promise<AnalysisRunStatus[]> {
  const res = await apiClient.get<AnalysisRunStatus[]>('/analysis-runs', {
    params: { page, page_size: pageSize },
  })
  return res.data
}
