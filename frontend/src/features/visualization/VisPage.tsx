import { useState } from 'react'
import { Layout, List, Tag, Input, Empty, Spin, Typography, message } from 'antd'
import {
  HistoryOutlined,
  SearchOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDatasetStore } from '@/store/datasetStore'
import { fetchAnalysisHistory } from '@/features/analysis/api'
import type { AnalysisRunStatus } from '@/features/analysis/types'
import { ChartPanel } from './ChartPanel'
import { ExportCenter } from './ExportCenter'
import { fetchChartContracts } from './api'

const { Sider, Content } = Layout
const { Search } = Input
const { Text } = Typography

const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  descriptive: '描述统计',
  assumptions: '假设检验',
  t_test: 't检验',
  anova_one_way: '单因素方差分析',
  anova_multi_way: '多因素方差分析',
  anova_welch: 'Welch方差分析',
  kruskal_wallis: 'Kruskal-Wallis检验',
  mann_whitney: 'Mann-Whitney U检验',
  correlation: '相关分析',
  regression_linear: '线性回归',
  regression_glm: '广义线性模型',
  pca: 'PCA主成分分析',
  pcoa: 'PCoA主坐标分析',
  nmds: 'NMDS分析',
  rda: 'RDA冗余分析',
  cca: 'CCA典范对应分析',
}

const STATUS_COLORS: Record<string, string> = {
  succeeded: 'green',
  failed: 'red',
  running: 'blue',
  queued: 'orange',
  cancelled: 'default',
  pending: 'default',
}

const STATUS_LABELS: Record<string, string> = {
  succeeded: '完成',
  failed: '失败',
  running: '运行中',
  queued: '排队中',
  cancelled: '已取消',
  pending: '待处理',
}

function formatTime(isoStr: string): string {
  const d = new Date(isoStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

export function VisPage() {
  const { currentDatasetId } = useDatasetStore()
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [manualRunId, setManualRunId] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  // Fetch analysis run history
  const { data: runs = [], isLoading: runsLoading } = useQuery({
    queryKey: ['analysis-runs'],
    queryFn: () => fetchAnalysisHistory(1, 100),
    staleTime: 10_000,
  })

  // Fetch chart contracts for the selected run
  const {
    data: contracts,
    isLoading: chartsLoading,
  } = useQuery({
    queryKey: ['chartContracts', selectedRunId],
    queryFn: () => fetchChartContracts(selectedRunId!),
    enabled: !!selectedRunId,
  })

  // Filter runs: only show succeeded (have results) + optionally filter by type
  const filteredRuns = runs.filter((r) => {
    if (typeFilter) {
      const label = ANALYSIS_TYPE_LABELS[r.analysis_type] ?? r.analysis_type
      if (
        !label.toLowerCase().includes(typeFilter.toLowerCase()) &&
        !r.analysis_type.toLowerCase().includes(typeFilter.toLowerCase())
      ) {
        return false
      }
    }
    return true
  })

  const tableNames =
    contracts?.flatMap((c) =>
      Object.keys(c.metadata).filter((k) => k.startsWith('table_')),
    ) ?? []

  const handleManualSearch = (val: string) => {
    if (!val.trim()) {
      message.warning('请输入运行 ID')
      return
    }
    setSelectedRunId(val.trim())
  }

  return (
    <Layout style={{ minHeight: '100%', background: 'transparent' }}>
      <Sider
        width={300}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          overflow: 'auto',
          height: '100%',
        }}
      >
        <div style={{ padding: '16px 12px 8px' }}>
          <Text strong style={{ fontSize: 14 }}>
            <HistoryOutlined style={{ marginRight: 6 }} />
            分析历史
          </Text>
        </div>
        <div style={{ padding: '0 12px 8px' }}>
          <Input
            placeholder="筛选分析类型..."
            prefix={<SearchOutlined />}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            allowClear
            size="small"
          />
        </div>
        {runsLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin size="small" />
          </div>
        ) : filteredRuns.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={currentDatasetId ? '暂无分析记录' : '请先选择数据集'}
            style={{ padding: '24px 0' }}
          />
        ) : (
          <List
            size="small"
            dataSource={filteredRuns}
            renderItem={(run: AnalysisRunStatus) => (
              <List.Item
                onClick={() => {
                  if (run.status === 'succeeded') {
                    setSelectedRunId(run.id)
                  }
                }}
                style={{
                  padding: '8px 12px',
                  cursor: run.status === 'succeeded' ? 'pointer' : 'default',
                  background: selectedRunId === run.id ? '#e6f4ff' : undefined,
                  borderLeft:
                    selectedRunId === run.id
                      ? '3px solid #1677ff'
                      : '3px solid transparent',
                }}
              >
                <div style={{ width: '100%' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Text
                      strong
                      ellipsis
                      style={{ fontSize: 13, maxWidth: 180 }}
                    >
                      <ExperimentOutlined style={{ marginRight: 4 }} />
                      {ANALYSIS_TYPE_LABELS[run.analysis_type] ??
                        run.analysis_type}
                    </Text>
                    <Tag color={STATUS_COLORS[run.status] ?? 'default'}>
                      {STATUS_LABELS[run.status] ?? run.status}
                    </Tag>
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {formatTime(run.created_at)}
                  </Text>
                </div>
              </List.Item>
            )}
          />
        )}

        {/* Manual run ID search fallback */}
        <div
          style={{
            padding: '12px',
            borderTop: '1px solid #f0f0f0',
            marginTop: 8,
          }}
        >
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
            按 ID 查找
          </Text>
          <Search
            placeholder="运行 ID"
            enterButton="查看"
            value={manualRunId}
            onChange={(e) => setManualRunId(e.target.value)}
            onSearch={handleManualSearch}
            size="small"
          />
        </div>
      </Sider>

      <Content style={{ padding: '0 16px' }}>
        {selectedRunId ? (
          <>
            <ChartPanel
              contracts={contracts ?? []}
              loading={chartsLoading}
            />
            <div style={{ marginTop: 16 }}>
              <ExportCenter runId={selectedRunId} tableNames={tableNames} />
            </div>
          </>
        ) : (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <Empty description="从左侧选择一个已完成的分析查看图表" />
          </div>
        )}
      </Content>
    </Layout>
  )
}
