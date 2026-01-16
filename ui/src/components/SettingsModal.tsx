import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { MusicTab } from './MusicTab'
import { SubSonicTab } from './SubSonicTab'
import { useConfig } from '@/hooks/useConfig'

type SettingsTab = 'music' | 'subsonic'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('music')
  const { config, loading: configLoading } = useConfig()

  // Local state for form values (session-only storage)
  const [musicLibrary, setMusicLibrary] = useState('')
  const [navidromeUrl, setNavidromeUrl] = useState('')
  const [navidromeUsername, setNavidromeUsername] = useState('')
  const [navidromePassword, setNavidromePassword] = useState('')

  // Initialize form values from config when loaded
  useEffect(() => {
    if (config) {
      setMusicLibrary(config.music_library || '')
      setNavidromeUrl(config.navidrome_url || '')
      setNavidromeUsername(config.navidrome_username || '')
      // Password is never returned from server, keep local value
    }
  }, [config])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  const tabs: { id: SettingsTab; label: string }[] = [
    { id: 'music', label: 'Music' },
    { id: 'subsonic', label: 'SubSonic' },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-lg md:max-h-[80vh] bg-surface border border-border rounded-xl z-50 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-xl font-semibold text-text">Settings</h2>
              <button
                onClick={onClose}
                className="text-text-muted hover:text-text transition-colors p-1 rounded-lg hover:bg-surface-hover"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex justify-center gap-1 px-6 py-3 border-b border-border">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative px-6 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'text-text'
                      : 'text-text-muted hover:text-text'
                  }`}
                >
                  {tab.label}
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-primary/20 border border-primary/30 rounded-lg -z-10"
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                    />
                  )}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {configLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <AnimatePresence mode="wait">
                  {activeTab === 'music' && (
                    <motion.div
                      key="music"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ duration: 0.15 }}
                    >
                      <MusicTab
                        musicLibrary={musicLibrary}
                        onMusicLibraryChange={setMusicLibrary}
                      />
                    </motion.div>
                  )}
                  {activeTab === 'subsonic' && (
                    <motion.div
                      key="subsonic"
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.15 }}
                    >
                      <SubSonicTab
                        url={navidromeUrl}
                        username={navidromeUsername}
                        password={navidromePassword}
                        hasServerPassword={config?.has_navidrome_password || false}
                        onUrlChange={setNavidromeUrl}
                        onUsernameChange={setNavidromeUsername}
                        onPasswordChange={setNavidromePassword}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
