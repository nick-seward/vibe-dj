import { useState } from 'react'
import { Globe, User, Lock, Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTestNavidrome } from '@/hooks/useConfig'
import { useToast } from '@/context/ToastContext'

interface SubSonicTabProps {
  url: string
  username: string
  password: string
  hasServerPassword: boolean
  onUrlChange: (value: string) => void
  onUsernameChange: (value: string) => void
  onPasswordChange: (value: string) => void
}

export function SubSonicTab({
  url,
  username,
  password,
  hasServerPassword,
  onUrlChange,
  onUsernameChange,
  onPasswordChange,
}: SubSonicTabProps) {
  const [showPassword, setShowPassword] = useState(false)
  const { testing, result, testConnection, clearResult } = useTestNavidrome()
  const { showToast } = useToast()

  const handleTestConnection = async () => {
    if (!url.trim() || !username.trim() || !password.trim()) return

    clearResult()
    const testResult = await testConnection(url, username, password)

    if (testResult.success) {
      showToast('success', testResult.message)
    } else {
      showToast('error', testResult.message)
    }
  }

  const isTestDisabled = !url.trim() || !username.trim() || !password.trim() || testing

  const getResultIcon = () => {
    if (!result) return null
    if (result.success) {
      return <CheckCircle className="w-5 h-5 text-green-400" />
    }
    return <XCircle className="w-5 h-5 text-red-400" />
  }

  return (
    <div className="space-y-6">
      {/* URL Field */}
      <div>
        <label htmlFor="navidromeUrl" className="block text-sm font-medium text-text-muted mb-2">
          SubSonic Server URL
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <Globe className="w-5 h-5" />
          </div>
          <input
            type="url"
            id="navidromeUrl"
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder="http://192.168.1.100:4533"
            className="input-field !pl-14"
            disabled={testing}
          />
        </div>
      </div>

      {/* Username Field */}
      <div>
        <label htmlFor="navidromeUsername" className="block text-sm font-medium text-text-muted mb-2">
          Username
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <User className="w-5 h-5" />
          </div>
          <input
            type="text"
            id="navidromeUsername"
            value={username}
            onChange={(e) => onUsernameChange(e.target.value)}
            placeholder="Enter username"
            className="input-field !pl-14"
            disabled={testing}
          />
        </div>
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="navidromePassword" className="block text-sm font-medium text-text-muted mb-2">
          Password
          {hasServerPassword && !password && (
            <span className="ml-2 text-xs text-text-muted/70">(configured on server)</span>
          )}
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <Lock className="w-5 h-5" />
          </div>
          <input
            type={showPassword ? 'text' : 'password'}
            id="navidromePassword"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder={hasServerPassword ? '••••••••' : 'Enter password'}
            className="input-field !pl-14 pr-11"
            disabled={testing}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Test Connection Button */}
      <div>
        <motion.button
          onClick={handleTestConnection}
          disabled={isTestDisabled}
          whileHover={!isTestDisabled ? { scale: 1.02 } : {}}
          whileTap={!isTestDisabled ? { scale: 0.98 } : {}}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {testing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Testing Connection...
            </>
          ) : (
            <>
              {getResultIcon() || <Globe className="w-5 h-5" />}
              Test SubSonic Connection
            </>
          )}
        </motion.button>
      </div>

      {/* Result display */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-lg p-4 border ${
            result.success
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}
        >
          <div className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <p className={`text-sm ${result.success ? 'text-green-400' : 'text-red-400'}`}>
              {result.message}
            </p>
          </div>
        </motion.div>
      )}

      {/* Info text */}
      <p className="text-xs text-text-muted">
        These credentials will be used when syncing playlists to your SubSonic/Navidrome server.
        They are stored only for this session.
      </p>
    </div>
  )
}
