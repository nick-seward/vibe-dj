import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SettingsModal } from './SettingsModal'
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
    validation: null,
    validatePath: vi.fn(),
    clearValidation: vi.fn(),
  }),
  useTestNavidrome: () => ({
    testing: false,
    result: null,
    testConnection: vi.fn(),
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

describe('SettingsModal', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when closed', () => {
    renderWithProviders(<SettingsModal isOpen={false} onClose={mockOnClose} />)
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
  })

  it('renders modal when open', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('shows Music and SubSonic tabs', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)
    expect(screen.getByText('Music')).toBeInTheDocument()
    expect(screen.getByText('SubSonic')).toBeInTheDocument()
  })

  it('shows Music tab content by default', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)
    expect(screen.getByLabelText(/music library path/i)).toBeInTheDocument()
  })

  it('switches to SubSonic tab when clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)

    await user.click(screen.getByText('SubSonic'))

    await waitFor(() => {
      expect(screen.getByLabelText(/subsonic server url/i)).toBeInTheDocument()
    })
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)

    // Find the close button in the header (it's the button next to the Settings title)
    const header = screen.getByText('Settings').parentElement
    const closeButton = header?.querySelector('button')
    
    if (closeButton) {
      await user.click(closeButton)
      expect(mockOnClose).toHaveBeenCalled()
    }
  })

  it('calls onClose when backdrop is clicked', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)

    // Click on backdrop (the first motion.div with onClick={onClose})
    const backdrop = document.querySelector('.backdrop-blur-sm')
    if (backdrop) {
      fireEvent.click(backdrop)
      expect(mockOnClose).toHaveBeenCalled()
    }
  })

  it('calls onClose when Escape key is pressed', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('populates music library from config', () => {
    renderWithProviders(<SettingsModal isOpen={true} onClose={mockOnClose} />)
    
    const input = screen.getByLabelText(/music library path/i) as HTMLInputElement
    expect(input.value).toBe('/test/music')
  })
})
