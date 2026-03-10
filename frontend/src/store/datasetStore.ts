import { create } from 'zustand'
import type { Dataset } from '@/api/types'

interface DatasetState {
  datasets: Dataset[]
  currentDatasetId: string | null
  setDatasets: (datasets: Dataset[]) => void
  setCurrentDataset: (id: string | null) => void
  getCurrentDataset: () => Dataset | undefined
}

export const useDatasetStore = create<DatasetState>((set, get) => ({
  datasets: [],
  currentDatasetId: null,
  setDatasets: (datasets) => set({ datasets }),
  setCurrentDataset: (id) => set({ currentDatasetId: id }),
  getCurrentDataset: () => {
    const { datasets, currentDatasetId } = get()
    return datasets.find((d) => d.id === currentDatasetId)
  },
}))
