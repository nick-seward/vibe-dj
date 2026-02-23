# Design Token Reference

**Version:** 1.1  
**Last Updated:** 2026-02-23

## Overview

Vibe-DJ uses a semantic design token system to ensure consistent, maintainable styling across the application. All tokens are defined as CSS custom properties in the `@theme` block and are accessible via Tailwind utility classes.

## Color Tokens

### Primary Colors

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--color-primary` | `#8b5cf6` | `bg-primary`, `text-primary`, `border-primary` | Primary actions, interactive elements |
| `--color-primary-hover` | `#7c3aed` | `bg-primary-hover`, `hover:bg-primary-hover` | Hover state for primary elements |
| `--color-secondary` | `#ec4899` | `bg-secondary`, `text-secondary`, `border-secondary` | Secondary actions, accents |
| `--color-accent` | `#06b6d4` | `bg-accent`, `text-accent`, `border-accent` | Highlights, special emphasis |

### Surface Colors

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--color-background` | `#0f0f1a` | `bg-background` | Main app background |
| `--color-surface` | `#1a1a2e` | `bg-surface` | Card and surface backgrounds |
| `--color-surface-hover` | `#252540` | `bg-surface-hover`, `hover:bg-surface-hover` | Hover state for surfaces |

### Text Colors

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--color-text` | `#f8fafc` | `text-text` | Primary text |
| `--color-text-muted` | `#94a3b8` | `text-text-muted` | Secondary, muted text |

### Border Colors

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--color-border` | `#334155` | `border-border` | Borders and dividers |

### Semantic Status Colors

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--color-error` | `#ef4444` | `text-error`, `bg-error`, `border-error` | Error states, danger buttons, validation |
| `--color-success` | `#22c55e` | `text-success`, `bg-success`, `border-success` | Success states, confirmations |
| `--color-warning` | `#f59e0b` | `text-warning`, `bg-warning`, `border-warning` | Warning states, caution messages |
| `--color-info` | `#3b82f6` | `text-info`, `bg-info`, `border-info` | Informational messages |

## Spacing Tokens

**Prefix:** `--space-*` (to avoid collision with Tailwind v4's `--spacing-*`)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `0.25rem` (4px) | Extra small spacing for tight layouts |
| `--space-sm` | `0.5rem` (8px) | Small spacing |
| `--space-md` | `0.75rem` (12px) | Medium spacing |
| `--space-lg` | `1rem` (16px) | Large spacing |
| `--space-xl` | `1.25rem` (20px) | Extra large spacing |
| `--space-2xl` | `1.5rem` (24px) | 2x extra large spacing |

**Note:** Prefer Tailwind's standard spacing utilities (`p-4`, `gap-2`, etc.) for common values. Use custom `--space-*` tokens only for non-standard spacing needs.

## Border Radius Tokens

**Prefix:** `--radius-*` (to avoid collision with Tailwind v4's `--border-radius-*`)

| Token | Value | Tailwind Equivalent | Usage |
|-------|-------|---------------------|-------|
| `--radius-sm` | `0.25rem` (4px) | `rounded` | Small radius |
| `--radius-md` | `0.5rem` (8px) | `rounded-lg` | Medium radius (buttons) |
| `--radius-lg` | `0.75rem` (12px) | `rounded-xl` | Large radius (cards) |
| `--radius-xl` | `1rem` (16px) | - | Extra large radius |

**Note:** Prefer Tailwind's standard radius utilities (`rounded-lg`, `rounded-xl`) for common values.

## Shadow Tokens

**Prefix:** `--elevation-*` (to avoid collision with Tailwind v4's `--shadow-*`)

| Token | Value | Tailwind Equivalent | Usage |
|-------|-------|---------------------|-------|
| `--elevation-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | `shadow-sm` | Subtle depth |
| `--elevation-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | `shadow-md` | Cards, elevated elements |
| `--elevation-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | `shadow-lg` | Modals, overlays |

**Note:** Prefer Tailwind's standard shadow utilities (`shadow-sm`, `shadow-md`) for common values.

## Usage Guidelines

### Using Color Tokens

**✅ Correct:**
```tsx
// Use semantic tokens via Tailwind classes
<p className="text-error">Error message</p>
<button className="bg-primary hover:bg-primary-hover">Click me</button>
<div className="border-success/50">Success border</div>
```

**❌ Incorrect:**
```tsx
// Don't use hardcoded colors
<p className="text-red-400">Error message</p>
<button className="bg-purple-500 hover:bg-purple-600">Click me</button>
<div style={{ borderColor: '#22c55e' }}>Success border</div>
```

### Using Spacing Tokens

**✅ Correct:**
```tsx
// Prefer Tailwind utilities for standard spacing
<div className="p-4 gap-2 mb-6">Content</div>

// Use custom tokens for non-standard values
<div style={{ padding: 'var(--space-md)' }}>Custom spacing</div>
```

### Using CSS Variables Directly

When Tailwind utilities aren't sufficient, access tokens via CSS variables:

```css
.custom-gradient {
  background: linear-gradient(
    135deg,
    var(--color-surface) 0%,
    var(--color-surface-hover) 50%,
    var(--color-background) 100%
  );
}
```

## Accessibility

All color tokens meet WCAG 2.1 AA contrast requirements (4.5:1 minimum) when used on appropriate backgrounds:

- **Text colors** on `--color-background`: 8.2:1 to 16.8:1 (AAA compliant)
- **Semantic colors** on `--color-background`: 5.2:1 to 6.9:1 (AA compliant)
- **Button text** on button backgrounds: 4.8:1 to 16.8:1 (AA compliant)

See `accessibility-validation.md` for detailed contrast ratios.

## Tailwind v4 Compatibility

This token system is designed for Tailwind v4 compatibility:

- Color tokens use `--color-*` prefix (safe, matches Tailwind convention)
- Spacing tokens use `--space-*` prefix (avoids collision with `--spacing-*`)
- Border radius tokens use `--radius-*` prefix (avoids collision with `--border-radius-*`)
- Shadow tokens use `--elevation-*` prefix (avoids collision with `--shadow-*`)

## Migration from Hardcoded Values

When updating existing code:

1. **Replace hardcoded hex colors** with semantic tokens
2. **Replace Tailwind color classes** (e.g., `text-red-400` → `text-error`)
3. **Use semantic meaning** (e.g., error states use `--color-error`, not just "red")
4. **Maintain consistency** across similar UI patterns

## See Also

- `button-variants.md` - Button variant usage guidelines
- `accessibility-validation.md` - Accessibility compliance report
- `theme.spec.md` - Complete theme specification
