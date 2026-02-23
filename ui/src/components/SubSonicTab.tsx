import { useState, useCallback } from 'react'
import { Globe, User, Lock, Eye, EyeOff, Loader2, CheckCircle, XCircle, Save } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTestNavidrome, useSaveConfig } from '@/hooks/useConfig'
import { useToast } from '@/context/ToastContext'

interface SubSonicTabProps {
  url: string
  username: string
  password: string
  originalUrl: string
  originalUsername: string
  hasServerPassword: boolean
  onUrlChange: (value: string) => void
  onUsernameChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onSaveSuccess: () => void
}

export function SubSonicTab({
  url,
  username,
  password,
  originalUrl,
  originalUsername,
  hasServerPassword,
  onUrlChange,
  onUsernameChange,
  onPasswordChange,
  onSaveSuccess,
}: SubSonicTabProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [showSaveSuccess, setShowSaveSuccess] = useState(false)
  const { testing, result, testConnection, clearResult } = useTestNavidrome()
  const { saving, saveConfig } = useSaveConfig()
  const { showToast } = useToast()

  // Determine if values have changed from original
  const hasUrlChange = url !== originalUrl
  const hasUsernameChange = username !== originalUsername
  const hasPasswordChange = password.length > 0
  const hasChanges = hasUrlChange || hasUsernameChange || hasPasswordChange

  // Save button is disabled if: no changes, or currently saving/testing
  const isSaveDisabled = !hasChanges || saving || testing

  const handleSave = useCallback(async () => {
    if (isSaveDisabled) return

    const updates: { navidrome_url?: string; navidrome_username?: string; navidrome_password?: string } = {}

    // Only include fields that have changed
    if (hasUrlChange) {
      updates.navidrome_url = url
    }
    if (hasUsernameChange) {
      updates.navidrome_username = username
    }
    if (hasPasswordChange) {
      updates.navidrome_password = password
    }

    const result = await saveConfig(updates)

    if (result.success) {
      showToast('success', result.message)
      setShowSaveSuccess(true)

      // Hide checkmark after 2 seconds, then refresh config
      setTimeout(() => {
        setShowSaveSuccess(false)
        onSaveSuccess()
      }, 2000)
    } else {
      showToast('error', result.message)
    }
  }, [isSaveDisabled, hasUrlChange, hasUsernameChange, hasPasswordChange, url, username, password, saveConfig, showToast, onSaveSuccess])

  const handleTestConnection = async () => {
    // Allow testing with stored password (hasServerPassword) even if password field is empty
    const hasUsablePassword = password.trim() || hasServerPassword
    if (!url.trim() || !username.trim() || !hasUsablePassword) return

    clearResult()
    // Pass empty string if using stored password - backend will use stored password
    const testResult = await testConnection(url, username, password.trim() || '')

    if (testResult.success) {
      showToast('success', testResult.message)
    } else {
      showToast('error', testResult.message)
    }
  }

  // Enable test button if user typed password OR if password is stored on server
  const isTestDisabled = !url.trim() || !username.trim() || (!password.trim() && !hasServerPassword) || testing

  const getResultIcon = () => {
    if (!result) return null
    if (result.success) {
      return <CheckCircle className="w-5 h-5 text-success" />
    }
    return <XCircle className="w-5 h-5 text-error" />
  }

  return (
    <div className="space-y-6">
      {/* Header with Save Button */}
      <div className="flex justify-end">
        <motion.button
          onClick={handleSave}
          disabled={isSaveDisabled && !showSaveSuccess}
          whileHover={!isSaveDisabled ? { scale: 1.02 } : {}}
          whileTap={!isSaveDisabled ? { scale: 0.98 } : {}}
          className={`flex items-center gap-2 font-medium px-4 py-2 rounded-lg transition-all duration-200 ${
            showSaveSuccess
              ? 'bg-success text-white cursor-default'
              : 'btn-primary'
          }`}
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : showSaveSuccess ? (
            <>
              <CheckCircle className="w-4 h-4" />
              Saved
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save
            </>
          )}
        </motion.button>
      </div>

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
          className="btn-secondary w-full flex items-center justify-center gap-2"
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
              ? 'bg-success/10 border-success/30'
              : 'bg-error/10 border-error/30'
          }`}
        >
          <div className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-success" />
            ) : (
              <XCircle className="w-5 h-5 text-error" />
            )}
            <p className={`text-sm ${result.success ? 'text-success' : 'text-error'}`}>
              {result.message}
            </p>
          </div>
        </motion.div>
      )}
    </div>
  )
}
