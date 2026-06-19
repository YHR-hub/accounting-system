import { createContext, useContext, useState, type ReactNode } from 'react'
import { api, type UserOut } from './api'

interface AuthState {
  user: UserOut | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState>({
  user: null,
  login: async () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(() => {
    const raw = localStorage.getItem('user')
    return raw ? (JSON.parse(raw) as UserOut) : null
  })

  const login = async (username: string, password: string) => {
    const res = await api.login(username, password)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    setUser(res.user)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
