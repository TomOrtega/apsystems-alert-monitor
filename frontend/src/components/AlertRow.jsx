const severityConfig = {
  critical: { color: 'text-red-600', bg: 'bg-red-50', dot: 'bg-red-500', label: 'Critico' },
  warning: { color: 'text-yellow-600', bg: 'bg-yellow-50', dot: 'bg-yellow-500', label: 'Advertencia' },
  info: { color: 'text-green-600', bg: 'bg-green-50', dot: 'bg-green-500', label: 'Info' },
}

export default function AlertRow({ alerta }) {
  const cfg = severityConfig[alerta.severidad] || severityConfig.info
  const fecha = alerta.created_at ? new Date(alerta.created_at).toLocaleString('es-ES') : '-'

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3 text-sm text-gray-500">{fecha}</td>
      <td className="px-4 py-3">
        <code className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">{alerta.sid}</code>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{alerta.account_name}</td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`}></span>
          {cfg.label}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 max-w-md truncate">{alerta.mensaje}</td>
    </tr>
  )
}
