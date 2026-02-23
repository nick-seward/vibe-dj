## 1. Update CSS Variables and Design Tokens

- [x] 1.1 Add semantic color variables to index.css @theme block (--color-error, --color-success, --color-warning, --color-info) (bead vibedj-m1x)
- [x] 1.2 Add spacing scale variables (--space-xs: 0.25rem, --space-sm: 0.5rem, --space-md: 0.75rem, --space-lg: 1rem, --space-xl: 1.25rem, --space-2xl: 1.5rem) (bead vibedj-m1x)
- [x] 1.3 Add border radius scale variables (--radius-sm: 0.25rem, --radius-md: 0.5rem, --radius-lg: 0.75rem, --radius-xl: 1rem) (bead vibedj-m1x)
- [x] 1.4 Add shadow scale variables (--elevation-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05), --elevation-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), --elevation-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1)) (bead vibedj-m1x)
- [x] 1.5 Ensure all existing theme colors are defined as CSS variables (--color-primary, etc.) (bead vibedj-m1x)

## 2. Update Tailwind Configuration

- [x] 2.1 Create tailwind.config.js in ui/ directory if not exists (bead vibedj-d8b)
- [x] 2.2 Configure Tailwind theme to reference CSS variables for colors, spacing, border radius, and shadows (bead vibedj-d8b)
- [x] 2.3 Ensure Tailwind builds correctly with new configuration (bead vibedj-d8b)
- [x] 2.4 Test that CSS variables are accessible in component classes (bead vibedj-d8b)

## 3. Implement Button Variants in CSS

- [x] 3.1 Define .btn-outline class with transparent background, primary border, hover to primary background (bead vibedj-f7y)
- [x] 3.2 Define .btn-ghost class with transparent background, text color, hover to surface-hover (bead vibedj-f7y)
- [x] 3.3 Define .btn-danger class with error background, white text, hover to darker error (bead vibedj-f7y)
- [x] 3.4 Add loading state styles for all button variants (spinner icon, disabled appearance) (bead vibedj-f7y)
- [x] 3.5 Ensure all button variants have consistent padding, border radius, and transitions (bead vibedj-f7y)

## 4. Refactor Components for Semantic Tokens

- [x] 4.1 Update all button usages in components to use appropriate variants (primary, secondary, outline, ghost, danger) (bead vibedj-2ta)
- [x] 4.2 Replace all hardcoded colors (red-400, red-500, etc.) with semantic tokens in component classes (bead vibedj-2ta)
- [x] 4.3 Update spacing classes to use design token equivalents where applicable (prefer Tailwind utilities; use --space-* for non-standard values) (bead vibedj-2ta)
- [x] 4.4 Add loading states to buttons in async operations across all components (bead vibedj-2ta)
- [x] 4.5 Update error and success messages to use --color-error and --color-success classes (bead vibedj-2ta)
- [x] 4.6 Ensure input focus rings use semantic primary color consistently (bead vibedj-2ta)

## 5. Component-Specific Updates

- [x] 5.1 SongCard: Replace hardcoded red in remove button with .btn-danger variant and semantic colors (bead vibedj-2ta)
- [x] 5.2 ChoiceListDrawer: Update any hardcoded colors to semantic tokens (bead vibedj-2ta)
- [x] 5.3 ProfilesTab: Standardize button variants and color usage across profile management (bead vibedj-2ta)
- [x] 5.4 MusicTab: Update playlist status indicators and control buttons to use semantic colors (bead vibedj-2ta)
- [x] 5.5 PlaylistView: Ensure regenerate and sync buttons use appropriate variants with loading states (bead vibedj-2ta)
- [x] 5.6 SubSonicTab: Update connection status colors and form validation to semantic tokens (bead vibedj-2ta)
- [x] 5.7 ConfigScreen: Standardize validation error colors and button styling (bead vibedj-2ta)
- [x] 5.8 SearchResults: Ensure card hover effects and action buttons use semantic tokens (bead vibedj-2ta)
- [x] 5.9 SearchForm: Update submit button to include loading state, standardize error colors (bead vibedj-2ta)
- [x] 5.10 ProfileSelector: Update any color usage to semantic tokens (bead vibedj-2ta)
- [x] 5.11 PlaylistTab: Ensure consistent button and card styling (bead vibedj-2ta)
- [x] 5.12 ToastContext: Update notification colors to use semantic error/success/warning/info tokens (bead vibedj-2ta)

## 6. Update Global Styles and Gradients

- [ ] 6.1 Update .gradient-bg to use semantic colors if needed
- [ ] 6.2 Update .gradient-text to use semantic primary and secondary
- [ ] 6.3 Ensure card hover effects use semantic surface-hover
- [ ] 6.4 Update any hardcoded colors in global CSS classes

## 7. Accessibility and Dark Mode Validation

- [ ] 7.1 Verify all semantic colors meet contrast requirements in dark mode
- [ ] 7.2 Ensure focus indicators use semantic colors with sufficient visibility
- [ ] 7.3 Test keyboard navigation with new button variants
- [ ] 7.4 Validate that loading states don't break accessibility

## 8. Testing and Validation

- [ ] 8.1 Run full test suite to ensure no regressions
- [ ] 8.2 Manually test all button variants and states in different components
- [ ] 8.3 Audit all components for remaining hardcoded colors or inconsistent styling
- [ ] 8.4 Verify semantic token usage across the entire codebase
- [ ] 8.5 Test loading states in async operations (search, sync, regenerate)
- [ ] 8.6 Ensure visual consistency across music tab, playlist views, modals, and sidebar

## 9. Documentation Updates

- [ ] 9.1 Update component documentation to reference semantic tokens
- [ ] 9.2 Create usage guidelines for button variants
- [ ] 9.3 Document design token reference for developers
- [ ] 9.4 Update any style guides to reflect v1.1 changes
