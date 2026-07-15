import { useState, useEffect } from 'react'
import { Save, Mail, TestTube } from 'lucide-react'
import { api } from '../../api'

export default function SmtpConfig() {
  const [data, setData] = useState({ enabled: 'true', host: '', port: '587', user: '', password: '', from_addr: '', alert_to: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const cfg = await api.configSection('smtp')
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
      await api.updateSmtp(data)
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
          <h1 className="text-2xl font-bold text-gray-900">Configuracion SMTP</h1>
          <p className="text-sm text-gray-500">Configura el envio de emails via Microsoft 365</p>
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
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Mail size={18} className="text-primary-600" />
            <span className="font-medium">Habilitar envio de emails</span>
          </div>
          <button
            onClick={() => update('enabled', data.enabled === 'true' ? 'false' : 'true')}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${data.enabled === 'true' ? 'bg-primary-600' : 'bg-gray-300'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${data.enabled === 'true' ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Host SMTP</label>
            <input value={data.host} onChange={(e) => update('host', e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">Puerto</label>
            <input value={data.port} onChange={(e) => update('port', e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">Usuario</label>
            <input value={data.user} onChange={(e) => update('user', e.target.value)} className="input" placeholder="alertas@tudominio.com" />
          </div>
          <div>
            <label className="label">Password</label>
            <input type="password" value={data.password} onChange={(e) => update('password', e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">Direccion remitente</label>
            <input value={data.from_addr} onChange={(e) => update('from_addr', e.target.value)} className="input" placeholder="Monitor Solar <alertas@tudominio.com>" />
          </div>
          <div>
            <label className="label">Destinatario</label>
            <input value={data.alert_to} onChange={(e) => update('alert_to', e.target.value)} className="input" placeholder="soporte@tudominio.com" />
          </div>
        </div>
      </div>
    </div>
  )
}
