import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { MainLayout } from './components/layout/MainLayout'
import { DashboardPage } from './pages/DashboardPage'
import { FixturesPage } from './pages/FixturesPage'
import { MappingPage } from './pages/MappingPage'
import { ScenesPage } from './pages/ScenesPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/mapping" element={<MappingPage />} />
          <Route path="/scenes" element={<ScenesPage />} />
          <Route path="/fixtures" element={<FixturesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
