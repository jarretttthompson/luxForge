import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', icon: '🎚️' },
  { to: '/mapping', label: 'Mapping', icon: '🧭' },
  { to: '/scenes', label: 'Scenes', icon: '🎬' },
  { to: '/fixtures', label: 'Fixtures', icon: '💡' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  return (
    <aside className="flex w-full max-w-xs flex-col border-r border-gray-800 bg-gray-950">
      <div className="border-b border-gray-800 px-6 py-5">
        <p className="text-sm font-medium text-gray-300">Control Areas</p>
      </div>

      <nav className="flex flex-1 flex-col gap-2 px-4 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-900 hover:text-gray-100',
              ].join(' ')
            }
          >
            <span className="text-base" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
