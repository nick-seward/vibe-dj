import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfigScreen } from '@/components/ConfigScreen'
import { ToastProvider } from '@/context/ToastContext'

// Mock the useConfig hook
vi.mock('@/hooks/useConfig', () => ({
  useConfig: () => ({
    config: {
      music_library: '/test/music',
      navidrome_url: 'http://localhost:4533',
      navidrome_username: 'testuser',
      has_navidrome_password: true,
      default_playlist_size: 20,
      default_bpm_jitter: 5.0,
    },
    loading: false,
    error: null,
    fetchConfig: vi.fn(),
  }),
  useValidatePath: () => ({
    validating: false,
    validation: { valid: true, exists: true, is_directory: true, message: 'Path is valid' },
    validatePath: vi.fn(),
    clearValidation: vi.fn(),
  }),
  useTestNavidrome: () => ({
    testing: false,
    result: null,
    testConnection: vi.fn(),
    clearResult: vi.fn(),
  }),
  useSaveConfig: () => ({
    saving: false,
    result: null,
    saveConfig: vi.fn().mockResolvedValue({ success: true, message: 'Configuration saved successfully' }),
    clearResult: vi.fn(),
  }),
}))

// Mock the ProfileContext so ProfilesTab renders without errors
vi.mock('@/context/ProfileContext', () => ({
  useProfileContext: () => ({
    profiles: [
      { id: 1, display_name: 'Shared', subsonic_url: null, subsonic_username: null, has_subsonic_password: false, created_at: '', updated_at: '' },
    ],
    activeProfileId: 1,
    activeProfile: { id: 1, display_name: 'Shared', subsonic_url: null, subsonic_username: null, has_subsonic_password: false, created_at: '', updated_at: '' },
    loading: false,
    error: null,
    setActiveProfileId: vi.fn(),
    refreshProfiles: vi.fn(),
    createProfile: vi.fn(),
    updateProfile: vi.fn(),
    deleteProfile: vi.fn(),
  }),
}))

// Mock the useIndexing hook
vi.mock('@/hooks/useIndexing', () => ({
  useIndexing: () => ({
    jobId: null,
    status: null,
    isIndexing: false,
    error: null,
    startIndexing: vi.fn(),
    cancelIndexing: vi.fn(),
  }),
}))

const renderWithProviders = (ui: React.ReactElement) => {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

describe('ConfigScreen', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the settings title', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders close button', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    expect(screen.getByLabelText('Close settings')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    await user.click(screen.getByLabelText('Close settings'))
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('calls onClose when Escape key is pressed', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('shows Music, Playlist, and Profiles tabs on desktop', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    // Desktop tabs (hidden on mobile via CSS, but still in DOM)
    const musicButtons = screen.getAllByText('Music')
    const playlistButtons = screen.getAllByText('Playlist')
    const profilesButtons = screen.getAllByText('Profiles')
    
    expect(musicButtons.length).toBeGreaterThan(0)
    expect(playlistButtons.length).toBeGreaterThan(0)
    expect(profilesButtons.length).toBeGreaterThan(0)
    expect(screen.queryByText('SubSonic')).not.toBeInTheDocument()
  })

  it('shows dropdown select for mobile', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    const dropdown = screen.getByLabelText('Select settings tab')
    expect(dropdown).toBeInTheDocument()
    expect(dropdown.tagName).toBe('SELECT')
  })

  it('shows Music tab content by default', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    expect(screen.getByLabelText(/music library path/i)).toBeInTheDocument()
  })

  it('populates music library from config', async () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    await waitFor(() => {
      const input = screen.getByLabelText(/music library path/i) as HTMLInputElement
      expect(input.value).toBe('/test/music')
    })
  })

  it('shows Save button in Music tab', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    expect(screen.getByRole('button', { name: /^save$/i })).toBeInTheDocument()
  })

  it('Save button is disabled when no changes made', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    const saveButton = screen.getByRole('button', { name: /^save$/i })
    expect(saveButton).toBeDisabled()
  })

  it('shows Index Music Library button in Music tab', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    expect(screen.getByRole('button', { name: /index music library/i })).toBeInTheDocument()
  })

  it('switches to Playlist tab when tab button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const playlistButtons = screen.getAllByText('Playlist')
    const tabButton = playlistButtons.find(el => el.tagName === 'BUTTON')

    if (tabButton) {
      await user.click(tabButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/default playlist size/i)).toBeInTheDocument()
      })
    }
  })

  it('shows BPM Jitter slider in Playlist tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'playlist')

    await waitFor(() => {
      expect(screen.getByLabelText(/bpm jitter/i)).toBeInTheDocument()
    })
  })

  it('shows Save button in Playlist tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'playlist')

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^save$/i })).toBeInTheDocument()
    })
  })

  it('switches to Profiles tab when dropdown is changed', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'profiles')

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add profile/i })).toBeInTheDocument()
    })
  })

  it('shows Profiles tab content when Profiles tab button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const profilesButtons = screen.getAllByText('Profiles')
    const tabButton = profilesButtons.find(el => el.tagName === 'BUTTON')

    if (tabButton) {
      await user.click(tabButton)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add profile/i })).toBeInTheDocument()
      })
    }
  })

})
