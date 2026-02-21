# UI Theme Baseline Design-System Spec

## Purpose

This spec defines the baseline design-system for the Vibe-DJ user interface, establishing a consistent visual language for colors, typography, spacing, and interactive components. It serves as the foundation for all UI elements across the application, ensuring a cohesive user experience with a dark theme aesthetic focused on music discovery and playlist generation.

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

### Typography
- **Font Family**: system-ui, -apple-system, sans-serif
- **Scale**: Uses Tailwind default scale (text-xs, text-sm, text-base, text-lg, text-xl, text-2xl, text-3xl, text-4xl, text-5xl)
- **Weights**: font-normal, font-medium, font-bold
- **Line Heights**: Tailwind defaults (leading-none, leading-tight, leading-snug, leading-normal, leading-relaxed, leading-loose)

### Interactive Components

#### Button Variants
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
