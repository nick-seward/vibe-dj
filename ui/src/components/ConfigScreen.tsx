import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { XCircle, ChevronDown } from 'lucide-react'
import { MusicTab } from './MusicTab'
import { SubSonicTab } from './SubSonicTab'
import { useConfig } from '@/hooks/useConfig'

type ConfigTab = 'music' | 'subsonic'

interface ConfigScreenProps {
  onClose: () => void
}

const tabs: { id: ConfigTab; label: string }[] = [
  { id: 'music', label: 'Music' },
  { id: 'subsonic', label: 'SubSonic' },
]

export function ConfigScreen({ onClose }: ConfigScreenProps) {
  const [activeTab, setActiveTab] = useState<ConfigTab>('music')
  const { config, loading: configLoading, fetchConfig } = useConfig()

  // Local state for form values
  const [musicLibrary, setMusicLibrary] = useState('')
  const [navidromeUrl, setNavidromeUrl] = useState('')
  const [navidromeUsername, setNavidromeUsername] = useState('')
  const [navidromePassword, setNavidromePassword] = useState('')

  // Track original values from config (for change detection)
  const [originalMusicLibrary, setOriginalMusicLibrary] = useState('')
  const [originalNavidromeUrl, setOriginalNavidromeUrl] = useState('')
  const [originalNavidromeUsername, setOriginalNavidromeUsername] = useState('')

  // Initialize form values from config when loaded
  useEffect(() => {
    if (config) {
      setMusicLibrary(config.music_library || '')
      setNavidromeUrl(config.navidrome_url || '')
      setNavidromeUsername(config.navidrome_username || '')
      // Update original values
      setOriginalMusicLibrary(config.music_library || '')
      setOriginalNavidromeUrl(config.navidrome_url || '')
      setOriginalNavidromeUsername(config.navidrome_username || '')
      // Password is never returned from server, keep local value
    }
  }, [config])

  // Callback to refresh config after successful save
  const handleSaveSuccess = useCallback(() => {
    fetchConfig().catch(() => {
      // Error is handled in the hook
    })
  }, [fetchConfig])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  const handleTabChange = (tabId: ConfigTab) => {
    setActiveTab(tabId)
  }

  const handleDropdownChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setActiveTab(e.target.value as ConfigTab)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen gradient-bg"
    >
      <div className="container mx-auto px-4 pt-1 max-w-2xl">
        {/* Header with title and close button */}
        <div className="flex items-center justify-center mb-8 relative">
          <h1 className="text-3xl md:text-4xl font-bold text-text">Settings</h1>
          <button
            onClick={onClose}
            className="absolute right-0 text-text-muted hover:text-text transition-colors p-2 rounded-full hover:bg-surface-hover"
            aria-label="Close settings"
          >
            <XCircle className="w-8 h-8" />
          </button>
        </div>

        {/* Desktop Tabs - hidden on mobile */}
        <div className="hidden sm:block mb-6">
          <div className="flex justify-center gap-2 pb-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`px-6 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-primary to-secondary text-white'
                    : 'text-text-muted hover:text-text hover:bg-surface-hover'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="h-0.5 bg-gradient-to-r from-primary to-secondary rounded-full" />
        </div>

        {/* Mobile Dropdown - hidden on desktop */}
        <div className="sm:hidden mb-6">
          <div className="relative">
            <select
              value={activeTab}
              onChange={handleDropdownChange}
              className="input-field appearance-none pr-10 text-center font-medium"
              aria-label="Select settings tab"
            >
              {tabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.label}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted">
              <ChevronDown className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-surface border border-border rounded-xl p-6">
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
                    originalMusicLibrary={originalMusicLibrary}
                    onMusicLibraryChange={setMusicLibrary}
                    onSaveSuccess={handleSaveSuccess}
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
                    originalUrl={originalNavidromeUrl}
                    originalUsername={originalNavidromeUsername}
                    hasServerPassword={config?.has_navidrome_password || false}
                    onUrlChange={setNavidromeUrl}
                    onUsernameChange={setNavidromeUsername}
                    onPasswordChange={setNavidromePassword}
                    onSaveSuccess={handleSaveSuccess}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>
      </div>
    </motion.div>
  )
}
