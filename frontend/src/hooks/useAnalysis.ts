import { useState } from 'react'
import { message } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { submitAnalysis, fetchAnalysisResult } from '@/features/analysis/api'
import { usePolling } from '@/hooks/usePolling'
import { POLL_INTERVAL } from '@/config/constants'
import type { AnalysisRunDetail } from '@/features/analysis/types'

interface AnalysisState {
  runId: string | null
  result: AnalysisRunDetail | null
  polling: boolean
}

/**
 * Polling-only hook for tabs with custom submit logic (dynamic analysis types).
 * Returns state + setters so the caller can wire up their own mutation.
 */
export function useAnalysisPolling() {
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  usePolling(
    async () => {
      if (!runId) return
      const detail = await fetchAnalysisResult(runId)
      if (detail.status === 'succeeded' || detail.status === 'failed') {
        setPolling(false)
        setResult(detail)
        if (detail.status === 'succeeded') {
          message.success('分析完成')
        } else {
          message.error(detail.error_message ?? '分析失败')
        }
      }
    },
    POLL_INTERVAL,
    polling,
  )

  return { runId, setRunId, result, polling, setPolling }
}

interface UseAnalysisReturn {
  submitMutation: ReturnType<typeof useMutation<{ run_id: string }, Error, Record<string, unknown>>>
  result: AnalysisRunDetail | null
  polling: boolean
}

/**
 * All-in-one hook for tabs with a fixed analysis type.
 * Combines submit mutation + polling.
 */
export function useAnalysis(
  datasetId: string | undefined,
  analysisType: string,
): UseAnalysisReturn {
  const { setRunId, result, polling, setPolling } = useAnalysisPolling()

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) =>
      submitAnalysis(datasetId!, analysisType, params),
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('分析任务已提交')
    },
    onError: () => {
      message.error('提交失败')
    },
  })

  return { submitMutation, result, polling }
}
