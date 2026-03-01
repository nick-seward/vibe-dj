import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchForm } from '@/components/SearchForm'

vi.mock('@/context/ProfileContext', () => ({
  useProfileContext: () => ({
    profiles: [],
    activeProfileId: null,
    activeProfile: null,
    loading: false,
    error: null,
    setActiveProfileId: vi.fn(),
    refreshProfiles: vi.fn(),
    createProfile: vi.fn(),
    updateProfile: vi.fn(),
    deleteProfile: vi.fn(),
  }),
}))

describe('SearchForm', () => {
  it('renders all input fields', () => {
    const onSearch = vi.fn()
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={false} onSettingsClick={onSettingsClick} />)

    expect(screen.getByLabelText(/artist/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/song title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/album/i)).toBeInTheDocument()
  })

  it('shows error when submitting with no fields filled', async () => {
    const onSearch = vi.fn()
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={false} onSettingsClick={onSettingsClick} />)

    const button = screen.getByRole('button', { name: /search/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/please enter at least one search field/i)).toBeInTheDocument()
    })

    expect(onSearch).not.toHaveBeenCalled()
  })

  it('calls onSearch with artist when only artist is filled', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn().mockResolvedValue(undefined)
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={false} onSettingsClick={onSettingsClick} />)

    await user.type(screen.getByLabelText(/artist/i), 'The Beatles')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(onSearch).toHaveBeenCalledWith({ artist: 'The Beatles' })
    })
  })

  it('calls onSearch with all fields when all are filled', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn().mockResolvedValue(undefined)
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={false} onSettingsClick={onSettingsClick} />)

    await user.type(screen.getByLabelText(/artist/i), 'The Beatles')
    await user.type(screen.getByLabelText(/song title/i), 'Yesterday')
    await user.type(screen.getByLabelText(/album/i), 'Help!')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(onSearch).toHaveBeenCalledWith({
        artist: 'The Beatles',
        title: 'Yesterday',
        album: 'Help!',
      })
    })
  })

  it('disables inputs and shows loading state when loading', () => {
    const onSearch = vi.fn()
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={true} onSettingsClick={onSettingsClick} />)

    expect(screen.getByLabelText(/artist/i)).toBeDisabled()
    expect(screen.getByLabelText(/song title/i)).toBeDisabled()
    expect(screen.getByLabelText(/album/i)).toBeDisabled()
    expect(screen.getByText(/searching/i)).toBeInTheDocument()
  })

  it('trims whitespace from input values', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn().mockResolvedValue(undefined)
    const onSettingsClick = vi.fn()
    render(<SearchForm onSearch={onSearch} loading={false} onSettingsClick={onSettingsClick} />)

    await user.type(screen.getByLabelText(/artist/i), '  The Beatles  ')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(onSearch).toHaveBeenCalledWith({ artist: 'The Beatles' })
    })
  })
})
