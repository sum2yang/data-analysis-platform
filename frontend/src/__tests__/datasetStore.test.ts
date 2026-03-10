import { describe, it, expect, beforeEach } from 'vitest'
import { useDatasetStore } from '@/store/datasetStore'
import type { Dataset } from '@/api/types'

describe('datasetStore', () => {
  const mockDatasets: Dataset[] = [
    { id: 'd1', name: 'DS 1', original_filename: 'f1.csv', file_type: 'csv', created_at: '', updated_at: '' },
    { id: 'd2', name: 'DS 2', original_filename: 'f2.xlsx', file_type: 'xlsx', created_at: '', updated_at: '' },
  ]

  beforeEach(() => {
    useDatasetStore.setState({ datasets: [], currentDatasetId: null })
  })

  it('setDatasets updates the list', () => {
    useDatasetStore.getState().setDatasets(mockDatasets)
    expect(useDatasetStore.getState().datasets).toEqual(mockDatasets)
  })

  it('setCurrentDataset updates the current ID', () => {
    useDatasetStore.getState().setCurrentDataset('d1')
    expect(useDatasetStore.getState().currentDatasetId).toBe('d1')
  })

  it('getCurrentDataset returns the correct dataset', () => {
    useDatasetStore.setState({ datasets: mockDatasets, currentDatasetId: 'd2' })
    const current = useDatasetStore.getState().getCurrentDataset()
    expect(current).toEqual(mockDatasets[1])
  })

  it('getCurrentDataset returns undefined if not found', () => {
    useDatasetStore.setState({ datasets: mockDatasets, currentDatasetId: 'invalid' })
    expect(useDatasetStore.getState().getCurrentDataset()).toBeUndefined()
  })

  it('getCurrentDataset returns undefined when no dataset selected', () => {
    useDatasetStore.setState({ datasets: mockDatasets, currentDatasetId: null })
    expect(useDatasetStore.getState().getCurrentDataset()).toBeUndefined()
  })
})
