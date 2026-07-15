import { useState, useEffect } from 'react'
import { Save, Clock } from 'lucide-react'
import { api } from '../../api'

export default function SchedulerConfig() {
  const [data, setData] = useState({ check_interval_hours: '24', alert_retention_days: '90' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const cfg = await api.configSection('scheduler')
      const mapped = {}
      for (const [k, v] of Object.entries(cfg)) {
        mapped[k] = v.value
      }
      setData((prev) => ({ ...prev, ...mapped }))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const update = (field, value) => setData((prev) => ({ ...prev, [field]: value }))

  const save = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.updateScheduler(data)
      setMsg('Guardado correctamente')
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSaving(false)
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Cargando...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scheduler</h1>
          <p className="text-sm text-gray-500">Configura la frecuencia de verificacion</p>
        </div>
        <button onClick={save} disabled={saving} className="btn-primary flex items-center gap-2">
          <Save size={16} /> {saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>

      {msg && (
        <div className={`p-3 rounded-lg text-sm ${msg.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {msg}
        </div>
      )}

      <div className="card space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={18} className="text-primary-600" />
          <span className="font-medium">Parametros de ejecucion</span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Intervalo de verificacion (horas)</label>
            <input type="number" min="1" max="168" value={data.check_interval_hours} onChange={(e) => update('check_interval_hours', e.target.value)} className="input" />
            <p className="text-xs text-gray-500 mt-1">Recomendado: 24 horas</p>
          </div>
          <div>
            <label className="label">Retencion de alertas (dias)</label>
            <input type="number" min="7" max="365" value={data.alert_retention_days} onChange={(e) => update('alert_retention_days', e.target.value)} className="input" />
            <p className="text-xs text-gray-500 mt-1">Alertas mas antiguas se eliminan</p>
          </div>
        </div>
      </div>
    </div>
  )
}
