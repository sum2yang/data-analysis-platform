export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  username: string
  email?: string
}

export interface DatasetColumn {
  id: string
  name: string
  dtype: string
  position: number
  null_count: number
  unique_count: number
}

export interface DatasetRevision {
  id: string
  version: number
  row_count: number
  col_count: number
  source_type: string
  created_at: string
}

export interface DatasetUploadResponse {
  id: string
  name: string
  revision_id: string
  row_count: number
  col_count: number
  columns: DatasetColumn[]
}

export interface DatasetListItem {
  id: string
  name: string
  original_filename: string
  file_type: string
  created_at: string
  updated_at: string
}

export interface DatasetDetail {
  id: string
  name: string
  description: string | null
  original_filename: string
  file_type: string
  created_at: string
  updated_at: string
  revisions: DatasetRevision[]
}

export interface DatasetPreview {
  columns: string[]
  rows: unknown[][]
  total_rows_shown: number
}

export interface DatasetProfile {
  row_count: number
  col_count: number
  columns: Record<string, unknown>
}

export interface ColumnInfo {
  name: string
  dtype: 'numeric' | 'categorical' | 'datetime' | 'text'
  missing_count: number
  unique_count: number
}

export interface Dataset {
  id: string
  name: string
  original_filename: string
  file_type: string
  created_at: string
  updated_at: string
}

export interface TaskInfo {
  id: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  result?: unknown
  error?: string
  created_at: string
}

export interface AnalysisRequest {
  dataset_id: string
  method: string
  params: Record<string, unknown>
}

export interface AnalysisResult {
  task_id: string
  tables?: TableResult[]
  charts?: ChartResult[]
  summary?: string
}

export interface TableResult {
  title: string
  columns: string[]
  data: Record<string, unknown>[]
}

export interface ChartResult {
  title: string
  type: string
  option: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiError {
  detail: string
  status: number
}
