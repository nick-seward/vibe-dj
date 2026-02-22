## MODIFIED Requirements

### Requirement: Color Palette
The design system SHALL include semantic color tokens for consistent error, success, warning, and info states, in addition to the existing theme colors.

#### Scenario: Error state styling
- **WHEN** displaying validation errors
- **THEN** use --color-error (#ef4444)
- **AND** ensure consistent error appearance across all forms

#### Scenario: Success state styling
- **WHEN** showing successful operations
- **THEN** use --color-success (#22c55e)
- **AND** maintain visual consistency with success indicators

#### Scenario: Warning state styling
- **WHEN** displaying caution messages
- **THEN** use --color-warning (#f59e0b)
- **AND** apply consistent warning styling

#### Scenario: Info state styling
- **WHEN** showing informational messages
- **THEN** use --color-info (#06b6d4)
- **AND** ensure readable contrast in dark mode

### Requirement: Design Tokens
The design system SHALL define CSS variables for all colors, spacing, border radius, and shadows to provide a centralized token system.

#### Scenario: Color token usage
- **WHEN** applying colors to UI elements
- **THEN** use --color-* variables
- **AND** avoid hardcoded hex values

#### Scenario: Spacing token usage
- **WHEN** setting margins or padding
- **THEN** use --spacing-* variables
- **AND** maintain consistent spacing rhythm

#### Scenario: Border radius token usage
- **WHEN** styling corners
- **THEN** use --border-radius-* variables
- **AND** ensure predictable corner appearances

#### Scenario: Shadow token usage
- **WHEN** adding elevation
- **THEN** use --shadow-* variables
- **AND** maintain elevation hierarchy

### Requirement: Button Variants
The design system SHALL provide primary, secondary, outline, ghost, and danger button variants, each with complete state definitions.

#### Scenario: Outline button styling
- **WHEN** rendering an outline button
- **THEN** use transparent background with primary border
- **AND** change to primary background on hover

#### Scenario: Ghost button styling
- **WHEN** rendering a ghost button
- **THEN** use transparent background with text color
- **AND** apply surface-hover on hover

#### Scenario: Danger button styling
- **WHEN** rendering a danger button
- **THEN** use error background with white text
- **AND** darken error color on hover

#### Scenario: Button loading state
- **WHEN** button is in loading state
- **THEN** show spinner icon
- **AND** disable interaction
- **AND** maintain consistent loading appearance

### Requirement: Consistency Rules
The design system SHALL enforce semantic token usage and accessibility standards.

#### Scenario: No hardcoded colors
- **WHEN** adding new UI elements
- **THEN** use semantic tokens exclusively
- **AND** avoid direct hex color references

#### Scenario: Accessibility compliance
- **WHEN** implementing interactive elements
- **THEN** ensure proper focus indicators
- **AND** maintain contrast ratios
- **AND** support keyboard navigation

### Requirement: Typography
The design system SHALL maintain consistent typography with defined font family, weights, and scales.

#### Scenario: Font family consistency
- **WHEN** setting text styling
- **THEN** use system-ui, -apple-system, sans-serif
- **AND** avoid custom font declarations

#### Scenario: Weight hierarchy
- **WHEN** applying font weights
- **THEN** use font-normal, font-medium, font-bold
- **AND** maintain semantic weight usage
