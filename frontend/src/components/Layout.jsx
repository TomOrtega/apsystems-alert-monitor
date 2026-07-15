import { Outlet, NavLink } from 'react-router-dom'
import { LayoutDashboard, Server, Bell, BarChart3, Settings, FileText, Mail, Send, Clock, RefreshCw } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/sistemas', icon: Server, label: 'Sistemas' },
  { to: '/alertas', icon: Bell, label: 'Alertas' },
  { to: '/reportes', icon: BarChart3, label: 'Reportes' },
]

const configItems = [
  { to: '/config/accounts', icon: Settings, label: 'Cuentas API' },
  { to: '/config/smtp', icon: Mail, label: 'SMTP' },
  { to: '/config/telegram', icon: Send, label: 'Telegram' },
  { to: '/config/scheduler', icon: Clock, label: 'Scheduler' },
  { to: '/config/logs', icon: FileText, label: 'Logs' },
]

function SidebarLink({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-primary-50 text-primary-700'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }`
      }
    >
      <Icon size={18} />
      {label}
    </NavLink>
  )
}

export default function Layout() {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-primary-700">APsystems Monitor</h1>
          <p className="text-xs text-gray-500">Panel de control solar</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <SidebarLink key={item.to} {...item} />
          ))}
          <div className="pt-4 pb-2">
            <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Configuracion</p>
          </div>
          {configItems.map((item) => (
            <SidebarLink key={item.to} {...item} />
          ))}
        </nav>
        <div className="p-3 border-t border-gray-200">
          <p className="text-xs text-gray-400 text-center">v1.0.0</p>
        </div>
      </aside>
      <main className="flex-1 overflow-auto bg-gray-50">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
