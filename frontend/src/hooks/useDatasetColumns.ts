import { useQuery } from '@tanstack/react-query'
import { useDatasetStore } from '@/store/datasetStore'
import { fetchDatasetColumns } from '@/features/data-mgmt/api'
import type { ColumnInfo } from '@/api/types'

export function useDatasetColumns() {
  const { currentDatasetId } = useDatasetStore()

  const { data: columns = [], isLoading } = useQuery({
    queryKey: ['datasetColumns', currentDatasetId],
    queryFn: () => fetchDatasetColumns(currentDatasetId!),
    enabled: !!currentDatasetId,
    staleTime: 30_000,
    select: (cols): ColumnInfo[] =>
      cols.map((c) => ({
        name: c.name,
        dtype: c.dtype as ColumnInfo['dtype'],
        missing_count: c.null_count,
        unique_count: c.unique_count,
      })),
  })

  return { columns, isLoading, datasetId: currentDatasetId }
}
