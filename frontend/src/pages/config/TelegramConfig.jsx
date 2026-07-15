import { useState, useEffect } from 'react'
import { Save, Send } from 'lucide-react'
import { api } from '../../api'

export default function TelegramConfig() {
  const [data, setData] = useState({ enabled: 'false', bot_token: '', chat_id: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const cfg = await api.configSection('telegram')
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
      await api.updateTelegram(data)
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
          <h1 className="text-2xl font-bold text-gray-900">Configuracion Telegram</h1>
          <p className="text-sm text-gray-500">Notificaciones via Telegram Bot</p>
        </div>
        <div className="flex gap-2">
          <button onClick={async () => { setTesting(true); setMsg(''); try { await api.testTelegram(); setMsg('Mensaje de prueba enviado a Telegram'); } catch (e) { setMsg('Error: ' + e.message); } setTesting(false) }} disabled={testing} className="btn-secondary flex items-center gap-2">
            <Send size={16} /> {testing ? 'Enviando...' : 'Probar bot'}
          </button>
          <button onClick={save} disabled={saving} className="btn-primary flex items-center gap-2">
            <Save size={16} /> {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>

      {msg && (
        <div className={`p-3 rounded-lg text-sm ${msg.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {msg}
        </div>
      )}

      <div className="card space-y-4">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Send size={18} className="text-primary-600" />
            <span className="font-medium">Habilitar Telegram</span>
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
            <label className="label">Bot Token</label>
            <input type="password" value={data.bot_token} onChange={(e) => update('bot_token', e.target.value)} className="input" placeholder="123456:ABC-DEF..." />
          </div>
          <div>
            <label className="label">Chat ID</label>
            <input value={data.chat_id} onChange={(e) => update('chat_id', e.target.value)} className="input" placeholder="-100123456789" />
          </div>
        </div>

        <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
          <p className="font-medium mb-1">Como configurar Telegram:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Busca <strong>@BotFather</strong> en Telegram y crea un nuevo bot</li>
            <li>Copia el token que te da y pega arriba</li>
            <li>Busca <strong>@userinfobot</strong> para obtener tu Chat ID</li>
            <li>Envia un mensaje a tu bot para activarlo</li>
          </ol>
        </div>
      </div>
    </div>
  )
}
