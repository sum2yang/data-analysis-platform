import { apiClient } from '@/api/client'
import type {
  DatasetListItem,
  DatasetDetail,
  DatasetPreview,
  DatasetProfile,
  DatasetUploadResponse,
  DatasetColumn,
  PaginatedResponse,
} from '@/api/types'
import type { JoinRequest, CleanRequest, ColumnTypeUpdate } from './types'

export async function fetchDatasets(page = 1, pageSize = 20): Promise<PaginatedResponse<DatasetListItem>> {
  const res = await apiClient.get<PaginatedResponse<DatasetListItem>>('/datasets', {
    params: { page, page_size: pageSize },
  })
  return res.data
}

export async function fetchDatasetDetail(id: string): Promise<DatasetDetail> {
  const res = await apiClient.get<DatasetDetail>(`/datasets/${id}`)
  return res.data
}

export async function fetchDatasetPreview(id: string, rows = 100): Promise<DatasetPreview> {
  const res = await apiClient.get<DatasetPreview>(`/datasets/${id}/preview`, {
    params: { rows },
  })
  return res.data
}

export async function fetchDatasetProfile(id: string): Promise<DatasetProfile> {
  const res = await apiClient.get<DatasetProfile>(`/datasets/${id}/profile`)
  return res.data
}

export async function uploadDataset(file: File, name?: string): Promise<DatasetUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)
  const res = await apiClient.post<DatasetUploadResponse>('/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function deleteDataset(id: string): Promise<void> {
  await apiClient.delete(`/datasets/${id}`)
}

export async function joinDatasets(data: JoinRequest): Promise<DatasetUploadResponse> {
  const res = await apiClient.post<DatasetUploadResponse>('/datasets/join', data)
  return res.data
}

export async function cleanDataset(data: CleanRequest): Promise<DatasetUploadResponse> {
  const res = await apiClient.post<DatasetUploadResponse>('/datasets/clean', data)
  return res.data
}

export async function updateColumnTypes(
  datasetId: string,
  updates: ColumnTypeUpdate[],
): Promise<DatasetUploadResponse> {
  const res = await apiClient.post<DatasetUploadResponse>(`/datasets/${datasetId}/columns/types`, {
    updates,
  })
  return res.data
}

export async function fetchDatasetColumns(datasetId: string): Promise<DatasetColumn[]> {
  const res = await apiClient.get<DatasetColumn[]>(`/datasets/${datasetId}/columns`)
  return res.data
}
