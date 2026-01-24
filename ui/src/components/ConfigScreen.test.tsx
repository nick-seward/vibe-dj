import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfigScreen } from './ConfigScreen'
import { ToastProvider } from '@/context/ToastContext'

// Mock the useConfig hook
vi.mock('@/hooks/useConfig', () => ({
  useConfig: () => ({
    config: {
      music_library: '/test/music',
      navidrome_url: 'http://localhost:4533',
      navidrome_username: 'testuser',
      has_navidrome_password: true,
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

  it('shows Music and SubSonic tabs on desktop', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    // Desktop tabs (hidden on mobile via CSS, but still in DOM)
    const musicButtons = screen.getAllByText('Music')
    const subsonicButtons = screen.getAllByText('SubSonic')
    
    expect(musicButtons.length).toBeGreaterThan(0)
    expect(subsonicButtons.length).toBeGreaterThan(0)
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

  it('switches to SubSonic tab when tab button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    // Click the SubSonic tab button (get all and click the button, not the option)
    const subsonicButtons = screen.getAllByText('SubSonic')
    const tabButton = subsonicButtons.find(el => el.tagName === 'BUTTON')
    
    if (tabButton) {
      await user.click(tabButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/subsonic server url/i)).toBeInTheDocument()
      })
    }
  })

  it('switches to SubSonic tab when dropdown is changed', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'subsonic')

    await waitFor(() => {
      expect(screen.getByLabelText(/subsonic server url/i)).toBeInTheDocument()
    })
  })

  it('populates music library from config', () => {
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)
    
    const input = screen.getByLabelText(/music library path/i) as HTMLInputElement
    expect(input.value).toBe('/test/music')
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

  it('shows Save button in SubSonic tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'subsonic')

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^save$/i })).toBeInTheDocument()
    })
  })

  it('shows Test SubSonic Connection button in SubSonic tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'subsonic')

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /test subsonic connection/i })).toBeInTheDocument()
    })
  })

  it('SubSonic Save button is enabled when password is entered', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ConfigScreen onClose={mockOnClose} />)

    const dropdown = screen.getByLabelText('Select settings tab')
    await user.selectOptions(dropdown, 'subsonic')

    await waitFor(() => {
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    })

    const passwordInput = screen.getByLabelText(/password/i)
    await user.type(passwordInput, 'newpassword')

    await waitFor(() => {
      const saveButton = screen.getByRole('button', { name: /^save$/i })
      expect(saveButton).not.toBeDisabled()
    })
  })
})
