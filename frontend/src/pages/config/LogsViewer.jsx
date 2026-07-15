import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Trash2, Download } from 'lucide-react'
import { api } from '../../api'

export default function LogsViewer() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [lines, setLines] = useState(100)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const logRef = useRef(null)
  const intervalRef = useRef(null)

  const load = async () => {
    try {
      const d = await api.logs(lines)
      setLogs(d.logs)
      setTotal(d.total)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    load()
    if (autoRefresh) {
      intervalRef.current = setInterval(load, 5000)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [autoRefresh, lines])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const clearLogs = async () => {
    if (!confirm('Eliminar todos los logs?')) return
    try {
      await api.clearLogs()
      await load()
    } catch (e) {
      console.error(e)
    }
  }

  const downloadLogs = () => {
    const blob = new Blob([logs.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `monitor-logs-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Logs</h1>
          <p className="text-sm text-gray-500">{total} lineas totales</p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Actualizar
          </button>
          <button onClick={downloadLogs} className="btn-secondary flex items-center gap-2">
            <Download size={16} /> Descargar
          </button>
          <button onClick={clearLogs} className="btn-danger flex items-center gap-2">
            <Trash2 size={16} /> Limpiar
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="rounded"
          />
          Auto-refresh (5s)
        </label>
        <select value={lines} onChange={(e) => setLines(Number(e.target.value))} className="input w-32">
          <option value={50}>50 lineas</option>
          <option value={100}>100 lineas</option>
          <option value={200}>200 lineas</option>
          <option value={500}>500 lineas</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32 text-gray-500">Cargando...</div>
      ) : (
        <div ref={logRef} className="bg-gray-900 text-green-400 rounded-xl p-4 h-[600px] overflow-y-auto font-mono text-xs leading-relaxed">
          {logs.length === 0 ? (
            <p className="text-gray-500">Sin logs</p>
          ) : (
            logs.map((line, i) => (
              <div key={i} className={`${
                line.includes('[ERROR]') ? 'text-red-400' :
                line.includes('[WARNING]') ? 'text-yellow-400' :
                line.includes('[INFO]') ? 'text-green-400' :
                'text-gray-400'
              }`}>
                {line}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
