export interface AxisConfig {
  label: string
  type: 'category' | 'value'
  data?: unknown[]
}

export interface AnnotationConfig {
  type: 'letter' | 'line' | 'band' | 'arrow'
  position?: { x: number; y: number } | { from: { x: number; y: number }; to: { x: number; y: number } }
  text?: string
  style?: Record<string, unknown>
}

export interface SeriesConfig {
  name: string
  type: 'bar' | 'scatter' | 'line' | 'boxplot' | 'violin' | 'heatmap'
  data: unknown[]
  error_bars?: number[]
  color?: string
}

export interface ChartContract {
  chart_type:
    | 'bar_error_letters'
    | 'boxplot'
    | 'violin'
    | 'heatmap'
    | 'scatter'
    | 'biplot'
    | 'ordination_scatter'
    | 'rda_biplot'
    | 'regression_plot'
  title: string
  x_axis?: AxisConfig
  y_axis?: AxisConfig
  series: SeriesConfig[]
  annotations: AnnotationConfig[]
  legend: string[]
  metadata: Record<string, unknown>
}

export interface ExportRequest {
  run_id: string
  chart_index?: number
  format: 'png' | 'svg' | 'pdf'
  width?: number
  height?: number
  dpi?: number
}
