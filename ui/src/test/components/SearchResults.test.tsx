import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchResults } from '@/components/SearchResults'
import { ChoiceListProvider } from '@/context/ChoiceListContext'
import type { PaginatedSearchResult, PageSize, PlaylistSize } from '@/types'

const mockResults: PaginatedSearchResult = {
  songs: [
    {
      id: 1,
      file_path: '/test/song1.mp3',
      title: 'Test Song 1',
      artist: 'Test Artist 1',
      album: 'Test Album 1',
      genre: 'Rock',
      duration: 180,
      last_modified: 1234567890,
    },
    {
      id: 2,
      file_path: '/test/song2.mp3',
      title: 'Test Song 2',
      artist: 'Test Artist 2',
      album: 'Test Album 2',
      genre: 'Pop',
      duration: 200,
      last_modified: 1234567891,
    },
  ],
  total: 100,
  limit: 50,
  offset: 0,
}

const renderWithProvider = (ui: React.ReactElement) => {
  return render(<ChoiceListProvider>{ui}</ChoiceListProvider>)
}

describe('SearchResults', () => {
  const defaultProps = {
    results: mockResults,
    pageSize: 50 as PageSize,
    selectedPlaylistSize: 20 as PlaylistSize,
    onPageSizeChange: vi.fn(),
    onPlaylistSizeChange: vi.fn(),
    onPageChange: vi.fn(),
    onBack: vi.fn(),
    onGeneratePlaylist: vi.fn(),
    loading: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search results with pagination info', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    expect(screen.getByText(/showing 1-2 of 100/i)).toBeInTheDocument()
  })

  it('renders page size dropdown with correct options', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    expect(dropdown).toBeInTheDocument()
    expect(dropdown).toHaveValue('50')

    expect(screen.getByRole('option', { name: '50' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '100' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '150' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '200' })).toBeInTheDocument()
  })

  it('calls onPageSizeChange when dropdown value changes', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    fireEvent.change(dropdown, { target: { value: '100' } })

    expect(defaultProps.onPageSizeChange).toHaveBeenCalledWith(100)
  })

  it('renders playlist size dropdown with selected value', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const playlistSizeDropdown = screen.getByLabelText(/playlist size/i)
    expect(playlistSizeDropdown).toBeInTheDocument()
    expect(playlistSizeDropdown).toHaveValue('20')
  })

  it('calls onPlaylistSizeChange when playlist size changes', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const playlistSizeDropdown = screen.getByLabelText(/playlist size/i)
    fireEvent.change(playlistSizeDropdown, { target: { value: '35' } })

    expect(defaultProps.onPlaylistSizeChange).toHaveBeenCalledWith(35)
  })

  it('calls onGeneratePlaylist with selected playlist size', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const addButtons = screen.getAllByRole('button', { name: /add to choice list/i })
    fireEvent.click(addButtons[0])

    const generateButton = screen.getByRole('button', { name: /generate playlist/i })
    fireEvent.click(generateButton)

    expect(defaultProps.onGeneratePlaylist).toHaveBeenCalledWith(20)
  })

  it('renders pagination controls at both top and bottom when there are multiple pages', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const pageLabels = screen.getAllByText(/page 1 of 2/i)
    expect(pageLabels).toHaveLength(2)

    const prevButtons = screen.getAllByRole('button', { name: /previous/i })
    const nextButtons = screen.getAllByRole('button', { name: /next/i })
    expect(prevButtons).toHaveLength(2)
    expect(nextButtons).toHaveLength(2)
  })

  it('disables previous button on first page', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const prevButtons = screen.getAllByRole('button', { name: /previous/i })
    prevButtons.forEach((btn) => expect(btn).toBeDisabled())
  })

  it('enables next button when there are more pages', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const nextButtons = screen.getAllByRole('button', { name: /next/i })
    nextButtons.forEach((btn) => expect(btn).not.toBeDisabled())
  })

  it('calls onPageChange when next button is clicked', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const nextButtons = screen.getAllByRole('button', { name: /next/i })
    fireEvent.click(nextButtons[0])

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(50)
  })

  it('calls onPageChange when previous button is clicked on page 2', () => {
    const propsOnPage2 = {
      ...defaultProps,
      results: { ...mockResults, offset: 50 },
    }
    renderWithProvider(<SearchResults {...propsOnPage2} />)

    const prevButtons = screen.getAllByRole('button', { name: /previous/i })
    fireEvent.click(prevButtons[0])

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(0)
  })

  it('shows limited message when total exceeds 1000', () => {
    const propsWithLargeTotal = {
      ...defaultProps,
      results: { ...mockResults, total: 2000 },
    }
    renderWithProvider(<SearchResults {...propsWithLargeTotal} />)

    expect(screen.getByText(/limited to 1000/i)).toBeInTheDocument()
  })

  it('does not show pagination controls when only one page', () => {
    const propsWithOnePage = {
      ...defaultProps,
      results: { ...mockResults, total: 30 },
    }
    renderWithProvider(<SearchResults {...propsWithOnePage} />)

    expect(screen.queryByText(/page \d+ of \d+/i)).not.toBeInTheDocument()
  })

  it('disables next button when at max search depth', () => {
    const propsAtMaxDepth = {
      ...defaultProps,
      results: { ...mockResults, offset: 950, total: 2000 },
    }
    renderWithProvider(<SearchResults {...propsAtMaxDepth} />)

    const nextButtons = screen.getAllByRole('button', { name: /next/i })
    nextButtons.forEach((btn) => expect(btn).toBeDisabled())
  })

  it('disables dropdown when loading', () => {
    const propsLoading = {
      ...defaultProps,
      loading: true,
    }
    renderWithProvider(<SearchResults {...propsLoading} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    expect(dropdown).toBeDisabled()
  })

  it('disables pagination buttons when loading', () => {
    const propsLoading = {
      ...defaultProps,
      loading: true,
    }
    renderWithProvider(<SearchResults {...propsLoading} />)

    const nextButtons = screen.getAllByRole('button', { name: /next/i })
    const prevButtons = screen.getAllByRole('button', { name: /previous/i })
    nextButtons.forEach((btn) => expect(btn).toBeDisabled())
    prevButtons.forEach((btn) => expect(btn).toBeDisabled())
  })

  it('shows no results message when songs array is empty', () => {
    const propsNoResults = {
      ...defaultProps,
      results: { ...mockResults, songs: [], total: 0 },
    }
    renderWithProvider(<SearchResults {...propsNoResults} />)

    expect(screen.getByText(/no songs found/i)).toBeInTheDocument()
  })

  it('highlights song card with gradient when selected', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const addButtons = screen.getAllByRole('button', { name: /add to choice list/i })
    fireEvent.click(addButtons[0])

    const selectedButton = screen.getByRole('button', { name: /already in choice list/i })
    const songCard = selectedButton.closest('[class*="card"]')
    expect(songCard).toHaveClass('bg-gradient-to-r')
    expect(songCard).toHaveClass('from-primary/20')
    expect(songCard).toHaveClass('to-secondary/20')
    expect(songCard).toHaveClass('border-primary/60')
  })

  it('does not highlight unselected song cards', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const addButtons = screen.getAllByRole('button', { name: /add to choice list/i })
    const songCard = addButtons[0].closest('[class*="card"]')
    expect(songCard).not.toHaveClass('bg-gradient-to-r')
  })

  it('calls onBack when back button is clicked', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const backButton = screen.getByRole('button', { name: /back to search/i })
    fireEvent.click(backButton)

    expect(defaultProps.onBack).toHaveBeenCalled()
  })
})
