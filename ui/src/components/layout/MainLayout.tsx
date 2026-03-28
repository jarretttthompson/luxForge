import { Outlet } from 'react-router-dom'

import { useWebSocket } from '../../hooks/useWebSocket'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function MainLayout() {
  useWebSocket()

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Sidebar />

        <div className="flex min-h-screen flex-1 flex-col">
          <Header />
          <main className="flex-1 bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 px-6 py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
