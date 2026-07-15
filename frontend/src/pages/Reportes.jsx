import { useState, useEffect } from 'react'
import { api } from '../api'

export default function Reportes() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [dias, setDias] = useState(30)

  const load = async () => {
    setLoading(true)
    try {
      const d = await api.reportes(dias)
      setData(d)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [dias])

  const agrupados = data.reduce((acc, r) => {
    if (!acc[r.date]) acc[r.date] = []
    acc[r.date].push(r)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reportes Diarios</h1>
          <p className="text-sm text-gray-500">{data.length} registros</p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={`px-3 py-1.5 text-sm rounded-lg ${dias === d ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {d} dias
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32 text-gray-500">Cargando...</div>
      ) : Object.keys(agrupados).length === 0 ? (
        <div className="card text-center text-gray-500 py-8">Sin datos de reportes</div>
      ) : (
        <div className="space-y-4">
          {Object.entries(agrupados).map(([fecha, rows]) => (
            <div key={fecha} className="card">
              <h3 className="font-semibold text-gray-800 mb-3">{fecha}</h3>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Total</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-green-600 uppercase">Verdes</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-yellow-600 uppercase">Amarillos</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-red-600 uppercase">Rojos</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Grises</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">API calls</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Alertas</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.account_name} className="border-b border-gray-100 last:border-0">
                      <td className="px-3 py-2 text-sm font-medium">{r.account_name}</td>
                      <td className="px-3 py-2 text-sm text-center">{r.total_sistemas}</td>
                      <td className="px-3 py-2 text-sm text-center text-green-600 font-medium">{r.green_count}</td>
                      <td className="px-3 py-2 text-sm text-center text-yellow-600 font-medium">{r.yellow_count}</td>
                      <td className="px-3 py-2 text-sm text-center text-red-600 font-medium">{r.red_count}</td>
                      <td className="px-3 py-2 text-sm text-center text-gray-500">{r.grey_count}</td>
                      <td className="px-3 py-2 text-sm text-center text-gray-500">{r.api_calls_used}</td>
                      <td className="px-3 py-2 text-sm text-center text-gray-500">{r.alertas_generadas}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
