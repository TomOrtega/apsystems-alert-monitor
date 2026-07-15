import { useState, useEffect } from 'react'
import { Search, CheckSquare, Square, Loader2, X, Monitor } from 'lucide-react'
import { api } from '../../api'

const LIGHT_LABELS = { 0: 'Sin datos', 1: 'Normal', 2: 'Alarma inversor', 3: 'ECU offline', 4: 'Sin datos' }
const LIGHT_COLORS = { 0: 'text-gray-400', 1: 'text-green-600', 2: 'text-yellow-600', 3: 'text-red-600', 4: 'text-gray-500' }

export default function DescubrirSistemas({ accountIndex, accountName, onClose }) {
  const [systems, setSystems] = useState([])
  const [loading, setLoading] = useState(false)
  const [discovering, setDiscovering] = useState(false)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [selected, setSelected] = useState(new Set())

  const loadDiscovered = async () => {
    setLoading(true)
    try {
      const data = await api.getDiscoveredSystems(accountIndex)
      setSystems(data)
      setSelected(new Set(data.filter((s) => s.monitorear).map((s) => s.sid)))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { loadDiscovered() }, [accountIndex])

  const handleDiscover = async () => {
    setDiscovering(true)
    setMsg('')
    try {
      const result = await api.discoverSystems(accountIndex)
      setMsg(`Descubiertos ${result.total} sistemas (${result.calls_used} llamadas API)`)
      await loadDiscovered()
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setDiscovering(false)
  }

  const toggleSid = (sid) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(sid)) next.delete(sid)
      else next.add(sid)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === systems.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(systems.map((s) => s.sid)))
    }
  }

  const saveSelection = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.updateMonitoredSystems(accountIndex, Array.from(selected))
      setMsg(`Guardado: ${selected.size} sistemas monitoreados`)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <Monitor size={20} className="text-primary-600" />
            <div>
              <h2 className="text-lg font-bold text-gray-900">Descubrir sistemas</h2>
              <p className="text-sm text-gray-500">Cuenta: {accountName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="p-4 border-b bg-gray-50 flex items-center gap-3">
          <button onClick={handleDiscover} disabled={discovering} className="btn-primary flex items-center gap-2">
            {discovering ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            {discovering ? 'Descubriendo...' : 'Descubrir sistemas'}
          </button>
          <button onClick={saveSelection} disabled={saving || systems.length === 0} className="btn-primary flex items-center gap-2">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <CheckSquare size={16} />}
            {saving ? 'Guardando...' : `Guardar seleccion (${selected.size})`}
          </button>
          {systems.length > 0 && (
            <button onClick={toggleAll} className="btn-secondary text-sm">
              {selected.size === systems.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
            </button>
          )}
        </div>

        {msg && (
          <div className={`mx-4 mt-3 p-3 rounded-lg text-sm ${msg.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {msg}
          </div>
        )}

        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <Loader2 size={20} className="animate-spin mr-2" /> Cargando...
            </div>
          ) : systems.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              <Monitor size={48} className="mx-auto mb-4 text-gray-300" />
              <p>No hay sistemas descubiertos</p>
              <p className="text-sm mt-1">Haz click en "Descubrir sistemas" para buscar en la API</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase w-10"></th>
                  <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase">SID</th>
                  <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Luz</th>
                  <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">ECUs</th>
                  <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Capacidad</th>
                  <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Timezone</th>
                </tr>
              </thead>
              <tbody>
                {systems.map((s) => (
                  <tr key={s.sid} className={`border-b border-gray-100 last:border-0 cursor-pointer ${selected.has(s.sid) ? 'bg-primary-50' : 'hover:bg-gray-50'}`} onClick={() => toggleSid(s.sid)}>
                    <td className="px-3 py-2">
                      {selected.has(s.sid) ? <CheckSquare size={16} className="text-primary-600" /> : <Square size={16} className="text-gray-300" />}
                    </td>
                    <td className="px-3 py-2 text-sm font-mono">{s.sid}</td>
                    <td className={`px-3 py-2 text-sm text-center font-medium ${LIGHT_COLORS[s.light] || 'text-gray-400'}`}>
                      {LIGHT_LABELS[s.light] || 'Sin datos'}
                    </td>
                    <td className="px-3 py-2 text-sm text-center">{Array.isArray(s.ecu_list) ? s.ecu_list.length : 0}</td>
                    <td className="px-3 py-2 text-sm text-center">{s.capacity || '-'}</td>
                    <td className="px-3 py-2 text-sm text-center text-gray-500">{s.timezone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
