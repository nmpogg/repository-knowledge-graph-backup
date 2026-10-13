import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/shell/AppShell'
import { AnnouncerProvider } from './components/ui/Announcer'
import { ThemeProvider } from './components/ui/ThemeToggle'
import { LocaleProvider } from './i18n'
import { ConversationPage } from './pages/conversations/ConversationPage'
import { ConversationsPage } from './pages/conversations/ConversationsPage'
import { ExplorerPage } from './pages/explorer/ExplorerPage'
import { JobMonitorPage } from './pages/jobs/JobMonitorPage'
import { RepositoryCreatePage } from './pages/repositories/RepositoryCreatePage'
import { RepositoryDetailPage } from './pages/repositories/RepositoryDetailPage'
import { RepositoryEditPage } from './pages/repositories/RepositoryEditPage'
import { RepositoryListPage } from './pages/repositories/RepositoryListPage'

export default function App() {
  return (
    <LocaleProvider>
      <ThemeProvider>
        <AnnouncerProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<Navigate to="/repositories" replace />} />
                <Route path="repositories" element={<RepositoryListPage />} />
                <Route path="repositories/new" element={<RepositoryCreatePage />} />
                <Route
                  path="repositories/:repositoryId/edit"
                  element={<RepositoryEditPage />}
                />
                <Route path="repositories/:repositoryId" element={<RepositoryDetailPage />} />
                <Route path="jobs/:jobId" element={<JobMonitorPage />} />
                <Route path="explorer" element={<ExplorerPage />} />
                <Route path="conversations" element={<ConversationsPage />} />
                <Route path="conversations/:conversationId" element={<ConversationPage />} />
                <Route path="*" element={<Navigate to="/repositories" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AnnouncerProvider>
      </ThemeProvider>
    </LocaleProvider>
  )
}
