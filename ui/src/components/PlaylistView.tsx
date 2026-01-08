import { useState } from 'react'
import { RefreshCw, Send, ArrowLeft, Loader2, Music, PartyPopper, ChevronDown, ChevronUp } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { PlaylistResponse } from '@/types'

interface NavidromeCredentials {
  url?: string
  username?: string
  password?: string
}

interface PlaylistViewProps {
  playlist: PlaylistResponse
  onRegenerate: () => Promise<void>
  onSyncToNavidrome: (playlistName: string, credentials?: NavidromeCredentials) => Promise<boolean>
  onStartOver: () => void
  regenerating: boolean
}

export function PlaylistView({
  playlist,
  onRegenerate,
  onSyncToNavidrome,
  onStartOver,
  regenerating,
}: PlaylistViewProps) {
  const [showNameModal, setShowNameModal] = useState(false)
  const [playlistName, setPlaylistName] = useState('')
  const [showCredentials, setShowCredentials] = useState(false)
  const [navidromeUrl, setNavidromeUrl] = useState('')
  const [navidromeUsername, setNavidromeUsername] = useState('')
  const [navidromePassword, setNavidromePassword] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [syncSuccess, setSyncSuccess] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)

  const handleSync = async () => {
    if (!playlistName.trim()) return

    setSyncing(true)
    setSyncError(null)

    try {
      const credentials: NavidromeCredentials | undefined = 
        (navidromeUrl || navidromeUsername || navidromePassword)
          ? {
              url: navidromeUrl || undefined,
              username: navidromeUsername || undefined,
              password: navidromePassword || undefined,
            }
          : undefined

      await onSyncToNavidrome(playlistName.trim(), credentials)
      setSyncSuccess(true)
      setShowNameModal(false)
      setPlaylistName('')
      setNavidromeUrl('')
      setNavidromeUsername('')
      setNavidromePassword('')
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-center justify-between gap-4 mb-6"
      >
        <button
          onClick={onStartOver}
          className="flex items-center gap-2 text-text-muted hover:text-text transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Start Over
        </button>

        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onRegenerate}
            disabled={regenerating}
            className="btn-secondary flex items-center gap-2"
          >
            {regenerating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
            Regenerate
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowNameModal(true)}
            disabled={syncSuccess}
            className="btn-primary flex items-center gap-2"
          >
            {syncSuccess ? (
              <>
                <PartyPopper className="w-5 h-5" />
                Sent!
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Send to Navidrome
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* Success celebration */}
      <AnimatePresence>
        {syncSuccess && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="mb-6 p-4 bg-green-500/20 border border-green-500/50 rounded-xl text-center"
          >
            <PartyPopper className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <p className="text-green-400 font-medium">
              Playlist sent to Navidrome successfully!
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Seed songs */}
      <div className="mb-6">
        <h3 className="text-text-muted text-sm font-medium mb-3 flex items-center gap-2">
          <Music className="w-4 h-4" />
          Based on your seeds
        </h3>
        <div className="flex flex-wrap gap-2">
          {playlist.seed_songs.map((song) => (
            <span
              key={song.id}
              className="px-3 py-1.5 bg-primary/20 text-primary rounded-full text-sm"
            >
              {song.title} – {song.artist}
            </span>
          ))}
        </div>
      </div>

      {/* Playlist */}
      <div>
        <h3 className="text-text font-medium mb-4">
          Your Playlist ({playlist.songs.length} songs)
        </h3>
        <div className="space-y-2">
          {playlist.songs.map((song, index) => (
            <motion.div
              key={song.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              className="card flex items-center gap-4"
            >
              <span className="text-text-muted text-sm w-8 text-right">
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-text truncate">{song.title}</h4>
                <p className="text-sm text-text-muted truncate">
                  {song.artist} • {song.album}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Playlist name modal */}
      <AnimatePresence>
        {showNameModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
            onClick={() => setShowNameModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-surface border border-border rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-text mb-4">
                Send to Navidrome
              </h3>
              
              <label className="block text-sm font-medium text-text-muted mb-1">
                Playlist Name
              </label>
              <input
                type="text"
                value={playlistName}
                onChange={(e) => setPlaylistName(e.target.value)}
                placeholder="Enter playlist name..."
                className="input-field mb-4"
                autoFocus
              />

              {/* Collapsible credentials section */}
              <button
                type="button"
                onClick={() => setShowCredentials(!showCredentials)}
                className="flex items-center gap-2 text-sm text-text-muted hover:text-text mb-2 transition-colors"
              >
                {showCredentials ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                Override server credentials (optional)
              </button>

              <AnimatePresence>
                {showCredentials && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-3 mb-4 p-3 bg-background/50 rounded-lg border border-border">
                      <p className="text-xs text-text-muted">
                        Leave empty to use server environment variables
                      </p>
                      <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">
                          Navidrome URL
                        </label>
                        <input
                          type="url"
                          value={navidromeUrl}
                          onChange={(e) => setNavidromeUrl(e.target.value)}
                          placeholder="http://192.168.1.100:4533"
                          className="input-field text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">
                          Username
                        </label>
                        <input
                          type="text"
                          value={navidromeUsername}
                          onChange={(e) => setNavidromeUsername(e.target.value)}
                          placeholder="username"
                          className="input-field text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">
                          Password
                        </label>
                        <input
                          type="password"
                          value={navidromePassword}
                          onChange={(e) => setNavidromePassword(e.target.value)}
                          placeholder="••••••••"
                          className="input-field text-sm"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {syncError && (
                <p className="text-red-400 text-sm mb-4">{syncError}</p>
              )}
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowNameModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSync}
                  disabled={!playlistName.trim() || syncing}
                  className="btn-primary flex items-center gap-2"
                >
                  {syncing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
