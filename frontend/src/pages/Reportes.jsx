import { useState, useEffect } from 'react'
import { api } from '../api'
import { RefreshCw, Download, Loader2, FileText } from 'lucide-react'

const LIGHT_LABELS = { 0: 'Sin datos', 1: 'Normal', 2: 'Alarma inversor', 3: 'ECU offline', 4: 'Sin datos' }
const LIGHT_COLORS = { 0: 'bg-gray-100 text-gray-500', 1: 'bg-green-100 text-green-700', 2: 'bg-yellow-100 text-yellow-700', 3: 'bg-red-100 text-red-700', 4: 'bg-gray-100 text-gray-500' }

export default function Reportes() {
  const [tab, setTab] = useState('historial')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [dias, setDias] = useState(30)
  const [manualReport, setManualReport] = useState(null)
  const [generating, setGenerating] = useState(false)

  const loadHistory = async () => {
    setLoading(true)
    try {
      const d = await api.reportes(dias)
      setData(d)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { if (tab === 'historial') loadHistory() }, [dias, tab])

  const generateManualReport = async () => {
    setGenerating(true)
    setManualReport(null)
    try {
      const report = await api.manualReport()
      setManualReport(report)
    } catch (e) {
      setManualReport({ error: e.message })
    }
    setGenerating(false)
  }

  const agrupados = data.reduce((acc, r) => {
    if (!acc[r.date]) acc[r.date] = []
    acc[r.date].push(r)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reportes</h1>
          <p className="text-sm text-gray-500">Historial diario y reportes manuales</p>
        </div>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          <button onClick={() => setTab('historial')} className={`px-4 py-1.5 text-sm rounded-md transition-colors ${tab === 'historial' ? 'bg-white shadow text-primary-700 font-medium' : 'text-gray-600 hover:text-gray-900'}`}>
            Historial
          </button>
          <button onClick={() => setTab('manual')} className={`px-4 py-1.5 text-sm rounded-md transition-colors ${tab === 'manual' ? 'bg-white shadow text-primary-700 font-medium' : 'text-gray-600 hover:text-gray-900'}`}>
            Reporte manual
          </button>
        </div>
      </div>

      {tab === 'historial' && (
        <>
          <div className="flex gap-2 justify-end">
            {[7, 30, 90].map((d) => (
              <button key={d} onClick={() => setDias(d)} className={`px-3 py-1.5 text-sm rounded-lg ${dias === d ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {d} dias
              </button>
            ))}
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
        </>
      )}

      {tab === 'manual' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-800">Reporte en tiempo real</h3>
                <p className="text-sm text-gray-500">Obtiene el estado actual de todos los sistemas monitoreados via API</p>
              </div>
              <button onClick={generateManualReport} disabled={generating} className="btn-primary flex items-center gap-2">
                {generating ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
                {generating ? 'Generando...' : 'Generar reporte'}
              </button>
            </div>
          </div>

          {manualReport && manualReport.error && (
            <div className="card bg-red-50 text-red-700">{manualReport.error}</div>
          )}

          {manualReport && !manualReport.error && (
            <div className="space-y-4">
              <div className="card bg-blue-50">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-blue-700">Generado: {new Date(manualReport.generated_at).toLocaleString()}</span>
                  <span className="text-blue-700 font-medium">Llamadas API: {manualReport.api_calls_used}</span>
                </div>
              </div>

              {manualReport.accounts.map((acc) => (
                <div key={acc.name} className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-800">{acc.name}</h3>
                    <div className="flex gap-3 text-sm">
                      <span className="text-green-600">{acc.summary.green} verdes</span>
                      <span className="text-yellow-600">{acc.summary.yellow} amarillos</span>
                      <span className="text-red-600">{acc.summary.red} rojos</span>
                      <span className="text-gray-500">{acc.summary.grey} grises</span>
                    </div>
                  </div>

                  {acc.error && <p className="text-red-600 text-sm">{acc.error}</p>}

                  {acc.systems.length > 0 && (
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase">SID</th>
                          <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Estado</th>
                          <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">ECUs</th>
                          <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Capacidad</th>
                          <th className="text-right px-3 py-2 text-xs font-medium text-gray-500 uppercase">Energia hoy</th>
                        </tr>
                      </thead>
                      <tbody>
                        {acc.systems.map((s) => (
                          <tr key={s.sid} className="border-b border-gray-100 last:border-0">
                            <td className="px-3 py-2 text-sm font-mono">{s.sid}</td>
                            <td className="px-3 py-2 text-center">
                              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${LIGHT_COLORS[s.light] || 'bg-gray-100 text-gray-500'}`}>
                                {LIGHT_LABELS[s.light] || 'Sin datos'}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-sm text-center">{Array.isArray(s.ecu_list) ? s.ecu_list.length : 0}</td>
                            <td className="px-3 py-2 text-sm text-center">{s.capacity || '-'}</td>
                            <td className="px-3 py-2 text-sm text-right">
                              {s.summary && s.summary.e_day ? `${s.summary.e_day} kWh` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}

                  {acc.systems.length === 0 && !acc.error && (
                    <p className="text-gray-500 text-sm text-center py-4">No hay sistemas monitoreados en esta cuenta</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
