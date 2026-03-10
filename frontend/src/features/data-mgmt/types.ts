export interface UploadOptions {
  file: File
  name?: string
}

export interface JoinRequest {
  left_dataset_id: string
  right_dataset_id: string
  left_key: string
  right_key: string
  how: 'inner' | 'left' | 'right' | 'outer'
  name: string
}

export interface CleanOperation {
  type: 'drop_na' | 'fill_na' | 'drop_duplicates' | 'rename' | 'drop_columns' | 'change_type'
  params: Record<string, unknown>
}

export interface CleanRequest {
  dataset_id: string
  operations: CleanOperation[]
}

export interface ColumnTypeUpdate {
  column: string
  new_dtype: string
}
