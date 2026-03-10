export interface AnalysisResultEnvelope {
  analysis_type: string
  engine: string
  summary: Record<string, unknown> | null
  tables: Record<string, unknown[]>
  assumptions: Record<string, unknown> | null
  warnings: string[]
  chart_contracts: Record<string, unknown>[]
}

export interface AnalysisRunAccepted {
  run_id: string
  status: string
  analysis_type: string
}

export interface AnalysisRunStatus {
  id: string
  analysis_type: string
  status: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface AnalysisRunDetail extends AnalysisRunStatus {
  result: AnalysisResultEnvelope | null
}

export interface DescriptiveParams {
  response_column: string
  group_column?: string
}

export interface AssumptionsParams {
  response_column: string
  group_column: string
}

export interface TTestParams {
  response_column: string
  group_column?: string
  mode: 'independent' | 'paired' | 'one_sample'
  alternative: 'two.sided' | 'less' | 'greater'
  conf_level: number
  mu?: number
  var_equal?: boolean
}

export interface AnovaParams {
  response_column: string
  group_column: string
  type?: 'one_way' | 'two_way'
  posthoc?: 'tukey' | 'duncan' | 'lsd'
  factor2_column?: string
}

export interface NonParametricParams {
  response_column: string
  group_column: string
  test: 'mann_whitney' | 'kruskal_wallis' | 'wilcoxon'
}
