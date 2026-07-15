import { useState, useEffect } from 'react'
import { RefreshCw, Zap } from 'lucide-react'
import { api } from '../api'
import StatusCard from '../components/StatusCard'
import AlertRow from '../components/AlertRow'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const d = await api.dashboard()
      setData(d)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const triggerCheck = async () => {
    setChecking(true)
    try {
      await api.triggerCheck()
      await load()
    } catch (e) {
      console.error(e)
    }
    setChecking(false)
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Cargando...</div>
  if (!data) return <div className="flex items-center justify-center h-64 text-red-500">Error cargando datos</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">{data.total_sistemas} sistemas monitoreados</p>
        </div>
        <button onClick={triggerCheck} disabled={checking} className="btn-primary flex items-center gap-2">
          <RefreshCw size={16} className={checking ? 'animate-spin' : ''} />
          {checking ? 'Verificando...' : 'Verificar ahora'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatusCard type="green" count={data.counts.green} />
        <StatusCard type="yellow" count={data.counts.yellow} />
        <StatusCard type="red" count={data.counts.red} />
        <StatusCard type="grey" count={data.counts.grey} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold mb-4">Ultimas Alertas</h2>
          {data.recent_alertas.length === 0 ? (
            <p className="text-gray-500 text-sm">No hay alertas recientes</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Fecha</th>
                    <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">SID</th>
                    <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                    <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Severidad</th>
                    <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Mensaje</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.recent_alertas.map((a) => (
                    <AlertRow key={a.id} alerta={a} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Uso API</h2>
          {Object.keys(data.api_usage).length === 0 ? (
            <p className="text-gray-500 text-sm">Sin uso registrado</p>
          ) : (
            <div className="space-y-4">
              {Object.entries(data.api_usage).map(([name, used]) => (
                <div key={name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">{name}</span>
                    <span className="text-gray-500">{used}/1000</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${used > 800 ? 'bg-red-500' : used > 500 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min((used / 1000) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-sm">
              <Zap size={16} className="text-yellow-500" />
              <span className="text-gray-600">Alertas 24h: <strong>{data.alertas_24h}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
