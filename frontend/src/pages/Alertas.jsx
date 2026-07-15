import { useState, useEffect } from 'react'
import { api } from '../api'
import AlertRow from '../components/AlertRow'

export default function Alertas() {
  const [data, setData] = useState({ alertas: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [filtroSeveridad, setFiltroSeveridad] = useState('')
  const [filtroCuenta, setFiltroCuenta] = useState('')
  const [page, setPage] = useState(0)
  const limit = 20

  const load = async () => {
    setLoading(true)
    try {
      const d = await api.alertas({
        severidad: filtroSeveridad || undefined,
        cuenta: filtroCuenta || undefined,
        limit,
        offset: page * limit,
      })
      setData(d)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [filtroSeveridad, filtroCuenta, page])

  const totalPages = Math.ceil(data.total / limit)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Alertas</h1>
        <p className="text-sm text-gray-500">{data.total} alertas totales</p>
      </div>

      <div className="flex gap-4">
        <div>
          <label className="label">Severidad</label>
          <select value={filtroSeveridad} onChange={(e) => { setFiltroSeveridad(e.target.value); setPage(0) }} className="input w-48">
            <option value="">Todas</option>
            <option value="critical">Critico</option>
            <option value="warning">Advertencia</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div>
          <label className="label">Cuenta</label>
          <select value={filtroCuenta} onChange={(e) => { setFiltroCuenta(e.target.value); setPage(0) }} className="input w-48">
            <option value="">Todas</option>
            <option value="Residencial">Residencial</option>
            <option value="Comercial">Comercial</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32 text-gray-500">Cargando...</div>
      ) : data.alertas.length === 0 ? (
        <div className="card text-center text-gray-500 py-8">No hay alertas</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Fecha</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">SID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Severidad</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mensaje</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.alertas.map((a) => (
                <AlertRow key={a.id} alerta={a} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="btn-secondary disabled:opacity-50">
            Anterior
          </button>
          <span className="text-sm text-gray-500">Pagina {page + 1} de {totalPages}</span>
          <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1} className="btn-secondary disabled:opacity-50">
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}
