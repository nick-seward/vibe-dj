import { useState, useEffect, useCallback } from 'react'
import { FolderOpen, Loader2, CheckCircle, XCircle, Music, Save, BarChart3, Clock, Disc3, Users } from 'lucide-react'
import { motion } from 'framer-motion'
import { useValidatePath, useSaveConfig } from '@/hooks/useConfig'
import { useIndexing } from '@/hooks/useIndexing'
import { useLibraryStats } from '@/hooks/useLibraryStats'
import { useToast } from '@/context/ToastContext'

function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

interface MusicTabProps {
  musicLibrary: string
  originalMusicLibrary: string
  onMusicLibraryChange: (value: string) => void
  onSaveSuccess: () => void
}

export function MusicTab({ musicLibrary, originalMusicLibrary, onMusicLibraryChange, onSaveSuccess }: MusicTabProps) {
  const { validating, validation, validatePath, clearValidation } = useValidatePath()
  const { isIndexing, status, error: indexError, startIndexing } = useIndexing()
  const { saving, saveConfig } = useSaveConfig()
  const { stats, loading: statsLoading } = useLibraryStats()
  const { showToast } = useToast()

  const [hasValidated, setHasValidated] = useState(false)
  const [showSaveSuccess, setShowSaveSuccess] = useState(false)

  // Determine if the value has changed from the original
  const hasChanges = musicLibrary !== originalMusicLibrary

  // Save button is disabled if: no changes, invalid path, currently saving, or currently indexing
  const isSaveDisabled = !hasChanges || !validation?.valid || saving || isIndexing

  const handleSave = useCallback(async () => {
    if (isSaveDisabled) return

    const result = await saveConfig({ music_library: musicLibrary })

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
  }, [isSaveDisabled, musicLibrary, saveConfig, showToast, onSaveSuccess])

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
      {/* Header with Save Button */}
      <div className="flex justify-end">
        <motion.button
          onClick={handleSave}
          disabled={isSaveDisabled && !showSaveSuccess}
          whileHover={!isSaveDisabled ? { scale: 1.02 } : {}}
          whileTap={!isSaveDisabled ? { scale: 0.98 } : {}}
          className={`flex items-center gap-2 font-medium px-4 py-2 rounded-lg transition-all duration-200 ${
            showSaveSuccess
              ? 'bg-green-600 text-white cursor-default'
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

      {/* Index Button */}
      <div>
        <motion.button
          onClick={handleIndexClick}
          disabled={isButtonDisabled}
          whileHover={!isButtonDisabled ? { scale: 1.02 } : {}}
          whileTap={!isButtonDisabled ? { scale: 0.98 } : {}}
          className="btn-secondary w-full flex items-center justify-center gap-2"
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
          {status?.progress?.processed != null && status?.progress?.total != null && status.progress.total > 0 && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-text-muted mb-1">
                <span>{status.progress.processed} / {status.progress.total}</span>
                <span>{Math.round((status.progress.processed / status.progress.total) * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-primary rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(status.progress.processed / status.progress.total) * 100}%` }}
                  transition={{ duration: 0.3, ease: 'easeOut' }}
                />
              </div>
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

      {/* Library Stats */}
      {!statsLoading && stats && stats.total_songs > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="flex items-center gap-2 text-text-muted">
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-medium">Library Statistics</span>
          </div>

          {/* Indexing completeness */}
          <div className="bg-surface rounded-lg p-4 border border-border">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-text-muted">Indexing Completeness</span>
              <span className="text-text">
                {stats.songs_with_features} / {stats.total_songs} songs analyzed
              </span>
            </div>
            <div className="w-full h-2 bg-surface-hover rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{ width: `${(stats.songs_with_features / stats.total_songs) * 100}%` }}
              />
            </div>
            {stats.last_indexed && (
              <p className="text-xs text-text-muted mt-2">
                Last indexed: {new Date(stats.last_indexed * 1000).toLocaleString()}
              </p>
            )}
          </div>

          {/* Library stats grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 text-text-muted mb-1">
                <Music className="w-3.5 h-3.5" />
                <span className="text-xs">Songs</span>
              </div>
              <p className="text-lg font-semibold text-text">{stats.total_songs.toLocaleString()}</p>
            </div>
            <div className="bg-surface rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 text-text-muted mb-1">
                <Users className="w-3.5 h-3.5" />
                <span className="text-xs">Artists</span>
              </div>
              <p className="text-lg font-semibold text-text">{stats.artist_count.toLocaleString()}</p>
            </div>
            <div className="bg-surface rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 text-text-muted mb-1">
                <Disc3 className="w-3.5 h-3.5" />
                <span className="text-xs">Albums</span>
              </div>
              <p className="text-lg font-semibold text-text">{stats.album_count.toLocaleString()}</p>
            </div>
            <div className="bg-surface rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 text-text-muted mb-1">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-xs">Play Time</span>
              </div>
              <p className="text-lg font-semibold text-text">{formatDuration(stats.total_duration)}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
