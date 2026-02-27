## Why

The baseline UI theme spec established the foundation for Vibe-DJ's design system, but analysis revealed several inconsistencies and gaps: hardcoded colors for error states, missing button variants, lack of semantic tokens, and scattered ad-hoc styles across components. Without semantic consistency, the design system cannot scale effectively, leading to maintenance issues and visual inconsistencies as new features are added.

This change evolves the baseline to v1.1 by introducing semantic design tokens, eliminating hardcoded values, and ensuring strict consistency rules. This creates a production-ready, maintainable system that future development can reliably reference.

## What Changes

- Update the ui/theme spec to v1.1 with semantic token definitions
- Add comprehensive color scales (primary, accent, error, success, neutral)
- Define consistent button variants (primary, secondary, ghost, danger) with all states
- Establish centralized spacing, border-radius, and shadow scales
- Update CSS custom properties and Tailwind configuration
- Refactor all components to use semantic tokens exclusively
- Add dark-mode support validation (already dark, but ensure completeness)
- Eliminate all hardcoded colors and ad-hoc styles

## Capabilities

### New Capabilities
None - this evolves the existing system

### Modified Capabilities
- `ui/theme`: Evolve from baseline to v1.1 with semantic tokens, consistency rules, and comprehensive component definitions

## Impact

- All UI components (buttons, inputs, cards, modals, player controls)
- CSS variables in index.css
- Tailwind configuration (if updated)
- Component styling consistency across music tab, playlist view, search forms, etc.
- No breaking changes to functionality, only improved maintainability
