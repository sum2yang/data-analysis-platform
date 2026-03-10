import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import zhCN from 'antd/locale/zh_CN'
import { themeConfig } from '@/config/theme'
import { AppLayout } from '@/layout/AppLayout'
import { TaskDrawer } from '@/layout/TaskDrawer'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { DataMgmtPage } from '@/features/data-mgmt/DataMgmtPage'
import { DescriptivePage } from '@/features/analysis/descriptive/DescriptivePage'
import { AssumptionsPage } from '@/features/analysis/assumptions/AssumptionsPage'
import { DifferencePage } from '@/features/analysis/difference/DifferencePage'
import { CorrelationPage } from '@/features/analysis/correlation/CorrelationPage'
import { OrdinationPage } from '@/features/analysis/ordination/OrdinationPage'
import { VisPage } from '@/features/visualization/VisPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN} theme={themeConfig}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout />
                  <TaskDrawer />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/data" replace />} />
              <Route path="data" element={<DataMgmtPage />} />
              <Route path="analysis">
                <Route
                  path="descriptive"
                  element={<DescriptivePage />}
                />
                <Route
                  path="assumptions"
                  element={<AssumptionsPage />}
                />
                <Route
                  path="difference"
                  element={<DifferencePage />}
                />
                <Route
                  path="correlation"
                  element={<CorrelationPage />}
                />
                <Route
                  path="ordination"
                  element={<OrdinationPage />}
                />
              </Route>
              <Route
                path="visualization"
                element={<VisPage />}
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}
