import { useState, useEffect } from 'react'
import { api } from '../api'

const lightConfig = {
  1: { color: 'text-green-600', bg: 'bg-green-50', label: 'Verde - Normal', dot: 'bg-green-500' },
  2: { color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Amarillo - Alarma', dot: 'bg-yellow-500' },
  3: { color: 'text-red-600', bg: 'bg-red-50', label: 'Rojo - ECU offline', dot: 'bg-red-500' },
  4: { color: 'text-gray-500', bg: 'bg-gray-50', label: 'Gris - Sin datos', dot: 'bg-gray-400' },
}

export default function Sistemas() {
  const [sistemas, setSistemas] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtroCuenta, setFiltroCuenta] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [cuentas, setCuentas] = useState([])

  const load = async () => {
    setLoading(true)
    try {
      const [s, acc] = await Promise.all([api.sistemas(filtroCuenta || undefined, filtroEstado || undefined), api.accounts()])
      setSistemas(s)
      setCuentas(acc)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [filtroCuenta, filtroEstado])

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Cargando...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Sistemas</h1>
        <p className="text-sm text-gray-500">{sistemas.length} sistemas</p>
      </div>

      <div className="flex gap-4">
        <div>
          <label className="label">Cuenta</label>
          <select value={filtroCuenta} onChange={(e) => setFiltroCuenta(e.target.value)} className="input w-48">
            <option value="">Todas</option>
            {cuentas.map((c) => (
              <option key={c.index} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Estado</label>
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} className="input w-48">
            <option value="">Todos</option>
            <option value="green">Verde</option>
            <option value="yellow">Amarillo</option>
            <option value="red">Rojo</option>
            <option value="grey">Gris</option>
          </select>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">SID</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Cuenta</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Estado</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Capacidad</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ultima verif.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sistemas.map((s) => {
              const cfg = lightConfig[s.light] || lightConfig[4]
              return (
                <tr key={s.sid} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <code className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">{s.sid}</code>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.account_name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`}></span>
                      {cfg.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.capacity || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {s.updated_at ? new Date(s.updated_at).toLocaleString('es-ES') : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
