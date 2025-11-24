import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin, signup as apiSignup, fetchCurrentUser, getAuthToken, setAuthToken, removeAuthToken } from '../api/client'
import type { User } from '../api/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => void
  hasActiveSubscription: () => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken()
      if (token) {
        try {
          const userData = await fetchCurrentUser()
          setUser(userData)
        } catch (err) {
          // Token invalid, remove it
          removeAuthToken()
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)
      const tokenData = await apiLogin(email, password)
      setAuthToken(tokenData.access_token)
      const userData = await fetchCurrentUser()
      setUser(userData)
      navigate('/app')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const signup = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)
      await apiSignup(email, password)
      // Auto-login after signup
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    removeAuthToken()
    setUser(null)
    navigate('/')
  }

  const hasActiveSubscription = (): boolean => {
    if (!user) return false
    
    // Check if user has active subscription or is trialing
    if (user.subscription_status === 'active' || user.subscription_status === 'trialing') {
      return true
    }
    
    // Check if user is within trial period
    if (user.trial_ends_at) {
      const trialEnd = new Date(user.trial_ends_at)
      if (trialEnd > new Date()) {
        return true
      }
    }
    
    return false
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, signup, logout, hasActiveSubscription }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

