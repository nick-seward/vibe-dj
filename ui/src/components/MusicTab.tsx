import { useState, useEffect, useCallback } from 'react'
import { FolderOpen, Loader2, CheckCircle, XCircle, Music } from 'lucide-react'
import { motion } from 'framer-motion'
import { useValidatePath } from '@/hooks/useConfig'
import { useIndexing } from '@/hooks/useIndexing'
import { useToast } from '@/context/ToastContext'

interface MusicTabProps {
  musicLibrary: string
  onMusicLibraryChange: (value: string) => void
}

export function MusicTab({ musicLibrary, onMusicLibraryChange }: MusicTabProps) {
  const { validating, validation, validatePath, clearValidation } = useValidatePath()
  const { isIndexing, status, error: indexError, startIndexing } = useIndexing()
  const { showToast } = useToast()

  const [hasValidated, setHasValidated] = useState(false)

  // Debounced validation
  useEffect(() => {
    if (!musicLibrary.trim()) {
      clearValidation()
      setHasValidated(false)
      return
    }

    const timer = setTimeout(() => {
      validatePath(musicLibrary)
      setHasValidated(true)
    }, 500)

    return () => clearTimeout(timer)
  }, [musicLibrary, validatePath, clearValidation])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onMusicLibraryChange(e.target.value)
  }

  const handleIndexClick = useCallback(async () => {
    if (!musicLibrary.trim() || !validation?.valid) return

    await startIndexing(musicLibrary, (success, message) => {
      if (success) {
        showToast('success', message)
      } else {
        showToast('error', message)
      }
    })
  }, [musicLibrary, validation, startIndexing, showToast])

  const isButtonDisabled = !musicLibrary.trim() || !validation?.valid || isIndexing

  const getValidationIcon = () => {
    if (validating) {
      return <Loader2 className="w-5 h-5 text-text-muted animate-spin" />
    }
    if (!hasValidated || !musicLibrary.trim()) {
      return null
    }
    if (validation?.valid) {
      return <CheckCircle className="w-5 h-5 text-green-400" />
    }
    return <XCircle className="w-5 h-5 text-red-400" />
  }

  const getProgressMessage = () => {
    if (!status) return null

    if (status.status === 'queued') {
      return 'Waiting to start...'
    }

    if (status.progress?.message) {
      return status.progress.message
    }

    if (status.status === 'running') {
      return 'Indexing in progress...'
    }

    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="musicLibrary" className="block text-sm font-medium text-text-muted mb-2">
          Music Library Path
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <FolderOpen className="w-5 h-5" />
          </div>
          <input
            type="text"
            id="musicLibrary"
            value={musicLibrary}
            onChange={handleInputChange}
            placeholder="/path/to/your/music"
            className="input-field !pl-14 pr-11"
            disabled={isIndexing}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {getValidationIcon()}
          </div>
        </div>
        {hasValidated && validation && !validation.valid && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-red-400 text-sm mt-2"
          >
            {validation.message}
          </motion.p>
        )}
        {hasValidated && validation?.valid && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-green-400 text-sm mt-2"
          >
            Path is valid and accessible
          </motion.p>
        )}
      </div>

      <div>
        <motion.button
          onClick={handleIndexClick}
          disabled={isButtonDisabled}
          whileHover={!isButtonDisabled ? { scale: 1.02 } : {}}
          whileTap={!isButtonDisabled ? { scale: 0.98 } : {}}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {isIndexing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Indexing...
            </>
          ) : (
            <>
              <Music className="w-5 h-5" />
              Index Music Library
            </>
          )}
        </motion.button>
      </div>

      {/* Progress indicator */}
      {isIndexing && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-surface-hover rounded-lg p-4 border border-border"
        >
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            <span className="text-text-muted text-sm">
              {getProgressMessage()}
            </span>
          </div>
          {status?.progress?.phase && (
            <div className="mt-2 text-xs text-text-muted">
              Phase: <span className="text-text">{status.progress.phase}</span>
            </div>
          )}
        </motion.div>
      )}

      {/* Error display */}
      {indexError && !isIndexing && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-4"
        >
          <p className="text-red-400 text-sm">{indexError}</p>
        </motion.div>
      )}
    </div>
  )
}
