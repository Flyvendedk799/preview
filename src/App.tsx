import { BrowserRouter, useLocation } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Router from './router/Router'
import { AuthProvider } from './hooks/useAuth'
import { OrganizationProvider } from './hooks/useOrganization'
import { ToastProvider } from './components/ui/Toast'

function AppContent() {
  const location = useLocation()
  const isDashboardRoute = location.pathname.startsWith('/app')

  if (isDashboardRoute) {
    return (
      <Layout>
        <Router />
      </Layout>
    )
  }

  return <Router />
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <OrganizationProvider>
          <ToastProvider>
            <AppContent />
          </ToastProvider>
        </OrganizationProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

