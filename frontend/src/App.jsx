import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Sistemas from './pages/Sistemas'
import Alertas from './pages/Alertas'
import Reportes from './pages/Reportes'
import AccountsConfig from './pages/config/AccountsConfig'
import SmtpConfig from './pages/config/SmtpConfig'
import TelegramConfig from './pages/config/TelegramConfig'
import SchedulerConfig from './pages/config/SchedulerConfig'
import LogsViewer from './pages/config/LogsViewer'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="sistemas" element={<Sistemas />} />
          <Route path="alertas" element={<Alertas />} />
          <Route path="reportes" element={<Reportes />} />
          <Route path="config/accounts" element={<AccountsConfig />} />
          <Route path="config/smtp" element={<SmtpConfig />} />
          <Route path="config/telegram" element={<TelegramConfig />} />
          <Route path="config/scheduler" element={<SchedulerConfig />} />
          <Route path="config/logs" element={<LogsViewer />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
