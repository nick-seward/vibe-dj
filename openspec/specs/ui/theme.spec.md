# UI Theme v1.1 Design-System Spec (Semantic Consistency)

## Purpose

This spec defines the v1.1 design-system for the Vibe-DJ user interface, establishing a semantically consistent visual language for colors, typography, spacing, and interactive components. It builds on the baseline foundation to eliminate hardcoded values, introduce semantic design tokens, and ensure strict consistency rules across all UI elements, supporting scalable and maintainable development with a dark theme aesthetic focused on music discovery and playlist generation.

## Requirements

### Color Palette
- **Primary**: #8b5cf6 (purple-500) - Used for primary actions and key interactive elements
- **Primary Hover**: #7c3aed (purple-600) - Hover state for primary elements
- **Secondary**: #ec4899 (pink-500) - Used for secondary actions and accents
- **Accent**: #06b6d4 (cyan-500) - Used for highlights and special emphasis
- **Background**: #0f0f1a - Main background color
- **Surface**: #1a1a2e - Card and surface backgrounds
- **Surface Hover**: #252540 - Hover state for surfaces
- **Text**: #f8fafc - Primary text color
- **Text Muted**: #94a3b8 - Secondary and muted text
- **Border**: #334155 - Border and divider color

### Semantic Color Tokens
- **Error**: #ef4444 - Used for error states, danger buttons, validation messages
- **Success**: #22c55e - Used for success states, confirmation messages
- **Warning**: #f59e0b - Used for warning states, caution messages
- **Info**: #06b6d4 - Used for informational messages

### Design Tokens (CSS Variables)
- **Colors**:
  - --color-primary: #8b5cf6
  - --color-primary-hover: #7c3aed
  - --color-secondary: #ec4899
  - --color-accent: #06b6d4
  - --color-background: #0f0f1a
  - --color-surface: #1a1a2e
  - --color-surface-hover: #252540
  - --color-text: #f8fafc
  - --color-text-muted: #94a3b8
  - --color-border: #334155
  - --color-error: #ef4444
  - --color-success: #22c55e
  - --color-warning: #f59e0b
  - --color-info: #06b6d4
- **Spacing** (prefixed `--space-*` to avoid colliding with Tailwind v4's `--spacing-*` namespace):
  - --space-xs: 0.25rem
  - --space-sm: 0.5rem
  - --space-md: 0.75rem
  - --space-lg: 1rem
  - --space-xl: 1.25rem
  - --space-2xl: 1.5rem
- **Border Radius** (prefixed `--radius-*` to avoid colliding with Tailwind v4's `--border-radius-*` namespace):
  - --radius-sm: 0.25rem
  - --radius-md: 0.5rem
  - --radius-lg: 0.75rem
  - --radius-xl: 1rem
- **Shadows** (prefixed `--elevation-*` to avoid colliding with Tailwind v4's `--shadow-*` namespace):
  - --elevation-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05)
  - --elevation-md: 0 4px 6px -1px rgb(0 0 0 / 0.1)
  - --elevation-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1)

### Typography
- **Font Family**: system-ui, -apple-system, sans-serif
- **Scale**: Uses Tailwind default scale (text-xs, text-sm, text-base, text-lg, text-xl, text-2xl, text-3xl, text-4xl, text-5xl)
- **Weights**: font-normal, font-medium, font-bold
- **Line Heights**: Tailwind defaults (leading-none, leading-tight, leading-snug, leading-normal, leading-relaxed, leading-loose)

### Interactive Components
- **Primary Button**:
  - Background: primary
  - Text: white
  - Hover: primary-hover background
  - Disabled: 50% opacity, cursor not-allowed
  - Padding: px-6 py-2.5
  - Border radius: rounded-lg
  - Font: font-medium

- **Secondary Button**:
  - Background: surface (hover: surface-hover)
  - Text: text
  - Border: border
  - Padding: px-6 py-2.5
  - Border radius: rounded-lg
  - Font: font-medium

- **Outline Button**:
  - Background: transparent
  - Text: primary
  - Border: primary
  - Hover: primary background, white text
  - Disabled: 50% opacity, cursor not-allowed
  - Padding: px-6 py-2.5
  - Border radius: rounded-lg
  - Font: font-medium

- **Ghost Button**:
  - Background: transparent
  - Text: text
  - Hover: surface-hover
  - Disabled: 50% opacity, cursor not-allowed
  - Padding: px-6 py-2.5
  - Border radius: rounded-lg
  - Font: font-medium

- **Danger Button**:
  - Background: error
  - Text: white
  - Hover: error-600 background
  - Disabled: 50% opacity, cursor not-allowed
  - Padding: px-6 py-2.5
  - Border radius: rounded-lg
  - Font: font-medium

#### Input Fields
- Background: surface
- Border: border
- Text: text
- Placeholder: text-muted
- Focus: ring-2 ring-primary, border-transparent
- Padding: px-4 py-2.5
- Border radius: rounded-lg

#### Cards
- Background: surface (hover: surface-hover)
- Border: border (hover: primary/50)
- Padding: p-4
- Border radius: rounded-xl

### Spacing Scale
Uses Tailwind default spacing scale (0.25rem increments from 0 to 96, plus fractions)

### Border Radius
- rounded-lg: 8px
- rounded-xl: 12px
- rounded-full: 9999px

### Transitions
- Duration: duration-200
- Easing: Tailwind default (ease-out for most, ease-in-out for some)

### Shadows
- shadow-sm: Small elevation for subtle depth (--elevation-sm)
- shadow-md: Medium elevation for cards (--elevation-md)
- shadow-lg: Large elevation for modals and overlays (--elevation-lg)

### Tailwind v4 Compatibility

Tailwind v4 uses the `@theme` block as its design token namespace. Variable prefixes like `--spacing-*`, `--shadow-*`, and `--border-radius-*` are **reserved** by Tailwind for utility generation (e.g., `max-w-xl` resolves to `var(--spacing-xl)`). Custom design tokens MUST use non-colliding prefixes:
- Spacing: `--space-*` (not `--spacing-*`)
- Border radius: `--radius-*` (not `--border-radius-*`)
- Shadows: `--elevation-*` (not `--shadow-*`)

Color tokens using `--color-*` are safe because Tailwind v4 uses the same prefix convention for custom colors.

### Consistency Rules
- All colors must use semantic tokens (--color-*) or defined theme variables; no hardcoded hex values
- Button variants must implement all defined states (default, hover, active, disabled, loading) consistently
- Spacing should prefer Tailwind utility classes (p-4, gap-2, etc.); use custom tokens (--space-*) for values outside the standard scale
- Border radius should prefer Tailwind utility classes (rounded-lg, rounded-xl); use custom tokens (--radius-*) for non-standard values
- Shadows should prefer Tailwind utility classes (shadow-sm, shadow-md); use custom tokens (--elevation-*) for non-standard values
- Typography must adhere to defined font family, weights, and line heights
- Dark-mode is the default; ensure all elements are optimized for dark backgrounds
- Interactive elements must follow accessibility standards for focus, contrast, and keyboard navigation

## Scenarios

### Given a user interacts with a primary action button
When the button is enabled and hovered
Then the background changes to primary-hover color
And the transition is smooth with duration-200

### Given a user focuses on an input field
When the field receives focus
Then a 2px ring appears in primary color
And the border becomes transparent

### Given a card component is displayed
When the user hovers over the card
Then the background changes to surface-hover
And the border color changes to primary with 50% opacity

### Given text needs to be muted
When displaying secondary information
Then use text-muted color
And font-weight normal

### Given a heading needs emphasis
When displaying the main title
Then use gradient-text class
And font-bold with appropriate size
