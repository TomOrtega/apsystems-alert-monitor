import { Server, AlertTriangle, XCircle, HelpCircle } from 'lucide-react'

const configs = {
  green: { icon: Server, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', label: 'Verdes' },
  yellow: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'Amarillos' },
  red: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'Rojos' },
  grey: { icon: HelpCircle, color: 'text-gray-500', bg: 'bg-gray-50', border: 'border-gray-200', label: 'Grises' },
}

export default function StatusCard({ type, count }) {
  const cfg = configs[type] || configs.grey
  const Icon = cfg.icon
  return (
    <div className={`card border ${cfg.border} ${cfg.bg}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{cfg.label}</p>
          <p className={`text-3xl font-bold ${cfg.color}`}>{count}</p>
        </div>
        <Icon size={32} className={cfg.color} />
      </div>
    </div>
  )
}
