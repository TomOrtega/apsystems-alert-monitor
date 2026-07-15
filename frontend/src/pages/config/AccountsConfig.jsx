import { useState, useEffect } from 'react'
import { Plus, Trash2, Save, Server, Search } from 'lucide-react'
import { api } from '../../api'
import DescubrirSistemas from './DescubrirSistemas'

export default function AccountsConfig() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [discoverAccount, setDiscoverAccount] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.accounts()
      setAccounts(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const updateField = (index, field, value) => {
    setAccounts((prev) => prev.map((a, i) => i === index ? { ...a, [field]: value } : a))
  }

  const addAccount = () => {
    setAccounts((prev) => [...prev, { index: Date.now(), name: '', app_id: '', app_secret: '', base_url: 'https://api.apsystemsema.com:9282', systems: '' }])
  }

  const removeAccount = async (index) => {
    if (!confirm('Eliminar esta cuenta?')) return
    try {
      if (accounts.length <= 2) {
        setMsg('Debe haber al menos 2 cuentas')
        return
      }
      await api.deleteAccount(index)
      await load()
      setMsg('Cuenta eliminada')
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  const save = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.updateAccounts(accounts.map((a) => ({
        name: a.name,
        app_id: a.app_id,
        app_secret: a.app_secret,
        base_url: a.base_url,
        systems: a.systems,
      })))
      setMsg('Guardado correctamente')
      await load()
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
          <h1 className="text-2xl font-bold text-gray-900">Cuentas API</h1>
          <p className="text-sm text-gray-500">Configura tus cuentas de APsystems OpenAPI</p>
        </div>
        <div className="flex gap-2">
          <button onClick={addAccount} className="btn-secondary flex items-center gap-2">
            <Plus size={16} /> Agregar
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

      <div className="space-y-4">
        {accounts.map((acc, idx) => (
          <div key={acc.index || idx} className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Server size={18} className="text-primary-600" />
                <h3 className="font-semibold">Cuenta {idx + 1}: {acc.name || 'Sin nombre'}</h3>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setDiscoverAccount({ index: acc.index, name: acc.name })} className="btn-secondary text-sm flex items-center gap-1">
                  <Search size={14} /> Descubrir sistemas
                </button>
                <button onClick={() => removeAccount(acc.index)} className="text-red-500 hover:text-red-700 p-1">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Nombre</label>
                <input value={acc.name} onChange={(e) => updateField(idx, 'name', e.target.value)} className="input" placeholder="Residencial" />
              </div>
              <div>
                <label className="label">App ID</label>
                <input value={acc.app_id} onChange={(e) => updateField(idx, 'app_id', e.target.value)} className="input" placeholder="tu_app_id" />
              </div>
              <div>
                <label className="label">App Secret</label>
                <input type="password" value={acc.app_secret} onChange={(e) => updateField(idx, 'app_secret', e.target.value)} className="input" placeholder="tu_secret" />
              </div>
              <div>
                <label className="label">Base URL</label>
                <input value={acc.base_url} onChange={(e) => updateField(idx, 'base_url', e.target.value)} className="input" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {discoverAccount && (
        <DescubrirSistemas
          accountIndex={discoverAccount.index}
          accountName={discoverAccount.name}
          onClose={() => setDiscoverAccount(null)}
        />
      )}
    </div>
  )
}
