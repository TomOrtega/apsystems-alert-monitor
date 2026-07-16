import { useState, useEffect } from 'react'
import { Search, CheckSquare, Square, Loader2, X, Monitor, Plus, Trash2, Zap } from 'lucide-react'
import { api } from '../../api'

const LIGHT_LABELS = { 0: 'Sin datos', 1: 'Normal', 2: 'Alarma inversor', 3: 'ECU offline', 4: 'Sin datos' }
const LIGHT_COLORS = { 0: 'text-gray-400', 1: 'text-green-600', 2: 'text-yellow-600', 3: 'text-red-600', 4: 'text-gray-500' }

export default function DescubrirSistemas({ accountIndex, accountName, onClose }) {
  const [systems, setSystems] = useState([])
  const [loading, setLoading] = useState(false)
  const [discovering, setDiscovering] = useState(false)
  const [saving, setSaving] = useState(false)
  const [checking, setChecking] = useState(false)
  const [msg, setMsg] = useState('')
  const [selected, setSelected] = useState(new Set())
  const [newSid, setNewSid] = useState('')
  const [addingSid, setAddingSid] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [apiTotal, setApiTotal] = useState(null)

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
    setApiTotal(null)
    try {
      const result = await api.discoverSystems(accountIndex)
      setApiTotal(result.total_api || result.total)
      setMsg(`Descubiertos ${result.total} sistemas de la API`)
      await loadDiscovered()
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setDiscovering(false)
  }

  const handleAddSid = async () => {
    const sid = newSid.trim()
    if (!sid) return
    setAddingSid(true)
    setMsg('')
    try {
      await api.addSystemManually(accountIndex, sid, accountName)
      setNewSid('')
      setMsg(`SID ${sid} anadido`)
      await loadDiscovered()
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setAddingSid(false)
  }

  const handleDeleteSid = async (sid) => {
    setDeleting(sid)
    try {
      const newSelected = new Set(selected)
      newSelected.delete(sid)
      setSelected(newSelected)
      await api.updateMonitoredSystems(accountIndex, Array.from(newSelected))
      await loadDiscovered()
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setDeleting(null)
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

  const saveAndCheck = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.updateMonitoredSystems(accountIndex, Array.from(selected))
      setMsg(`Guardado: ${selected.size} sistemas. Ejecutando verificacion...`)
      setChecking(true)
      try {
        const result = await api.triggerCheck()
        setMsg(`Guardado ${selected.size} sistemas. Check completado: ${result.alertas_generadas} alertas generadas`)
      } catch (e2) {
        setMsg(`Guardado ${selected.size} sistemas. Error en check: ${e2.message}`)
      }
      setChecking(false)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <Monitor size={20} className="text-primary-600" />
            <div>
              <h2 className="text-lg font-bold text-gray-900">Gestionar sistemas</h2>
              <p className="text-sm text-gray-500">Cuenta: {accountName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="p-4 border-b bg-gray-50 space-y-3">
          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={handleDiscover} disabled={discovering} className="btn-primary flex items-center gap-2">
              {discovering ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              {discovering ? 'Descubriendo todos...' : 'Descubrir SIDs (API)'}
            </button>
            <button onClick={saveAndCheck} disabled={saving || checking} className="btn-primary flex items-center gap-2">
              {saving || checking ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              {checking ? 'Verificando...' : saving ? 'Guardando...' : `Guardar y verificar (${selected.size})`}
            </button>
            {systems.length > 0 && (
              <button onClick={toggleAll} className="btn-secondary text-sm">
                {selected.size === systems.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              value={newSid}
              onChange={(e) => setNewSid(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddSid()}
              placeholder="Anadir SID manualmente (ej: D21E065700463105)"
              className="input flex-1"
            />
            <button onClick={handleAddSid} disabled={addingSid || !newSid.trim()} className="btn-primary flex items-center gap-2">
              {addingSid ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              Anadir
            </button>
          </div>
        </div>

        {msg && (
          <div className={`mx-4 mt-3 p-3 rounded-lg text-sm ${msg.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
            {msg}
          </div>
        )}

        <div className="mx-4 mt-3 p-3 rounded-lg text-sm bg-blue-50 text-blue-700">
          Descubre todos los SIDs de la API ({apiTotal ? `${apiTotal} sistemas en tu cuenta` : 'puede tardar unos segundos'}) o anadelos manualmente.
          Los sistemas descubiertos se seleccionan automaticamente para monitorear.
        </div>

        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <Loader2 size={20} className="animate-spin mr-2" /> Cargando...
            </div>
          ) : systems.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              <Monitor size={48} className="mx-auto mb-4 text-gray-300" />
              <p>No hay sistemas configurados</p>
              <p className="text-sm mt-1">Descubre SIDs de la API o anadelos manualmente</p>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-500 mb-2">{systems.length} sistemas ({selected.size} seleccionados)</p>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase w-10"></th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500 uppercase">SID</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Luz</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">ECUs</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Capacidad</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">Timezone</th>
                    <th className="text-center px-3 py-2 text-xs font-medium text-gray-500 uppercase w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {systems.map((s) => (
                    <tr key={s.sid} className={`border-b border-gray-100 last:border-0 ${selected.has(s.sid) ? 'bg-primary-50' : 'hover:bg-gray-50'}`}>
                      <td className="px-3 py-2 cursor-pointer" onClick={() => toggleSid(s.sid)}>
                        {selected.has(s.sid) ? <CheckSquare size={16} className="text-primary-600" /> : <Square size={16} className="text-gray-300" />}
                      </td>
                      <td className="px-3 py-2 text-sm font-mono cursor-pointer" onClick={() => toggleSid(s.sid)}>{s.sid}</td>
                      <td className={`px-3 py-2 text-sm text-center font-medium cursor-pointer ${LIGHT_COLORS[s.light] || 'text-gray-400'}`} onClick={() => toggleSid(s.sid)}>
                        {LIGHT_LABELS[s.light] || 'Sin datos'}
                      </td>
                      <td className="px-3 py-2 text-sm text-center cursor-pointer" onClick={() => toggleSid(s.sid)}>{Array.isArray(s.ecu_list) ? s.ecu_list.length : 0}</td>
                      <td className="px-3 py-2 text-sm text-center cursor-pointer" onClick={() => toggleSid(s.sid)}>{s.capacity || '-'}</td>
                      <td className="px-3 py-2 text-sm text-center text-gray-500 cursor-pointer" onClick={() => toggleSid(s.sid)}>{s.timezone}</td>
                      <td className="px-3 py-2 text-center">
                        <button onClick={() => handleDeleteSid(s.sid)} disabled={deleting === s.sid} className="text-red-400 hover:text-red-600 p-1">
                          {deleting === s.sid ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
