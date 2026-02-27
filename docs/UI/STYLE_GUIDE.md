# Vibe-DJ UI Style Guide v1.1

**Version:** 1.1 (Semantic Consistency)  
**Last Updated:** 2026-02-23

## Introduction

This style guide documents the v1.1 UI theme system for Vibe-DJ, which introduces semantic design tokens and eliminates hardcoded values for a consistent, maintainable, and accessible user interface.

## Key Changes in v1.1

### 1. Semantic Design Tokens
- All colors now use semantic tokens (`--color-error`, `--color-success`, etc.)
- Eliminated all hardcoded hex values in components
- Introduced spacing, border radius, and shadow tokens

### 2. Button Variant System
- Five standardized button variants (primary, secondary, outline, ghost, danger)
- Consistent styling across all variants
- Built-in loading state support

### 3. Accessibility First
- All colors meet WCAG 2.1 AA contrast requirements
- Semantic focus indicators
- Proper ARIA attributes throughout

### 4. Tailwind v4 Compatibility
- Token naming avoids Tailwind v4 reserved prefixes
- Seamless integration with Tailwind utilities

## Design Principles

### 1. Semantic Over Presentational

**✅ Do:**
```tsx
<p className="text-error">Invalid input</p>
<button className="btn-danger">Delete</button>
```

**❌ Don't:**
```tsx
<p className="text-red-400">Invalid input</p>
<button className="bg-red-600">Delete</button>
```

**Why:** Semantic tokens convey meaning and ensure consistency when colors change.

### 2. Consistency Over Customization

**✅ Do:**
```tsx
<button className="btn-primary">Save</button>
<button className="btn-secondary">Cancel</button>
```

**❌ Don't:**
```tsx
<button className="bg-purple-500 px-4 py-2 rounded">Save</button>
<button className="bg-gray-700 px-5 py-3 rounded-md">Cancel</button>
```

**Why:** Consistent button variants ensure predictable UX and easier maintenance.

### 3. Accessibility by Default

**✅ Do:**
```tsx
<button className="btn-ghost" aria-label="Close settings">
  <X className="w-4 h-4" />
</button>
```

**❌ Don't:**
```tsx
<button onClick={close}>
  <X className="w-4 h-4" />
</button>
```

**Why:** ARIA labels make icon-only buttons accessible to screen readers.

## Color Usage

### When to Use Each Semantic Color

| Color | Use For | Don't Use For |
|-------|---------|---------------|
| `error` | Validation errors, failed operations, danger actions | Generic red styling |
| `success` | Successful operations, confirmations, positive states | Generic green styling |
| `warning` | Caution messages, non-critical alerts | Generic yellow/orange styling |
| `info` | Informational messages, neutral notifications | Generic blue styling |
| `primary` | Primary actions, interactive elements, links | All purple elements |
| `secondary` | Secondary actions, accents | All pink elements |
| `accent` | Highlights, special emphasis | All cyan elements |

### Color Combinations

**Card with Error State:**
```tsx
<div className="bg-error/10 border border-error/30 rounded-lg p-4">
  <p className="text-error text-sm">{errorMessage}</p>
</div>
```

**Success Notification:**
```tsx
<div className="bg-success/20 border border-success/50 rounded-xl p-4">
  <CheckCircle className="w-5 h-5 text-success" />
  <p className="text-success">Operation successful!</p>
</div>
```

## Component Patterns

### Forms

**Input Field:**
```tsx
<input
  type="text"
  className="input-field"
  placeholder="Enter value..."
/>
```

The `.input-field` class provides:
- Semantic surface background
- Border with semantic border color
- Focus ring with semantic primary color
- Proper padding and border radius

**Form with Validation:**
```tsx
<form onSubmit={handleSubmit}>
  <input className="input-field" />
  {error && <p className="text-error text-sm mt-2">{error}</p>}
  
  <div className="flex gap-3 justify-end mt-4">
    <button type="button" className="btn-secondary">Cancel</button>
    <button type="submit" className="btn-primary" disabled={!isValid}>
      Submit
    </button>
  </div>
</form>
```

### Cards

**Standard Card:**
```tsx
<div className="card">
  <h3 className="font-medium text-text">Card Title</h3>
  <p className="text-text-muted text-sm">Card description</p>
</div>
```

The `.card` class provides:
- Semantic surface background
- Hover state with surface-hover
- Border with primary/50 on hover
- Consistent padding and border radius

### Modals

**Modal Structure:**
```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
  <motion.div
    className="bg-surface border border-border rounded-xl p-6 w-full max-w-md shadow-xl"
  >
    <h2 className="text-lg font-semibold text-text mb-4">Modal Title</h2>
    
    {/* Modal content */}
    
    <div className="flex gap-3 justify-end mt-6">
      <button className="btn-secondary">Cancel</button>
      <button className="btn-primary">Confirm</button>
    </div>
  </motion.div>
</div>
```

### Status Indicators

**Loading State:**
```tsx
{loading ? (
  <>
    <Loader2 className="w-5 h-5 animate-spin" />
    Loading...
  </>
) : (
  'Load Data'
)}
```

**Success/Error Indicators:**
```tsx
{status === 'success' && (
  <CheckCircle className="w-5 h-5 text-success" />
)}
{status === 'error' && (
  <XCircle className="w-5 h-5 text-error" />
)}
```

## Typography

### Text Hierarchy

```tsx
{/* Primary heading */}
<h1 className="text-2xl font-bold text-text">Main Title</h1>

{/* Secondary heading */}
<h2 className="text-xl font-semibold text-text">Section Title</h2>

{/* Body text */}
<p className="text-text">Regular content</p>

{/* Muted text */}
<p className="text-text-muted text-sm">Secondary information</p>

{/* Gradient text for emphasis */}
<h1 className="gradient-text text-3xl font-bold">Vibe-DJ</h1>
```

### Font Weights

- `font-normal` - Regular body text
- `font-medium` - Buttons, labels, emphasis
- `font-semibold` - Section headings
- `font-bold` - Main headings, important text

## Spacing

### Prefer Tailwind Utilities

```tsx
{/* Standard spacing */}
<div className="p-4 gap-2 mb-6">Content</div>

{/* Responsive spacing */}
<div className="p-4 md:p-6 lg:p-8">Content</div>
```

### Custom Spacing (Rare)

Only use custom `--space-*` tokens for non-standard values:

```css
.custom-layout {
  padding: var(--space-md);
  gap: var(--space-xs);
}
```

## Animations

### Transitions

All interactive elements use `duration-200` for smooth transitions:

```tsx
<button className="transition-all duration-200 hover:scale-105">
  Hover me
</button>
```

### Framer Motion

Use Framer Motion for complex animations:

```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: 20 }}
  transition={{ duration: 0.2 }}
>
  Content
</motion.div>
```

## Dark Mode

Vibe-DJ uses dark mode by default. All semantic colors are optimized for dark backgrounds:

- Background: `#0f0f1a` (very dark blue-black)
- Surface: `#1a1a2e` (dark blue-gray)
- Text: `#f8fafc` (near white, 16.8:1 contrast)

**No light mode support** is currently implemented. All colors assume a dark background.

## Common Mistakes to Avoid

### 1. Hardcoded Colors

**❌ Don't:**
```tsx
<div style={{ color: '#ef4444' }}>Error</div>
<p className="text-red-400">Error</p>
```

**✅ Do:**
```tsx
<div className="text-error">Error</div>
```

### 2. Inconsistent Button Styling

**❌ Don't:**
```tsx
<button className="bg-purple-500 px-4 py-2 rounded">Save</button>
<button className="bg-purple-600 px-6 py-3 rounded-lg">Submit</button>
```

**✅ Do:**
```tsx
<button className="btn-primary">Save</button>
<button className="btn-primary">Submit</button>
```

### 3. Missing Loading States

**❌ Don't:**
```tsx
<button onClick={handleSubmit} disabled={loading}>
  Submit
</button>
```

**✅ Do:**
```tsx
<button className="btn-primary" disabled={loading}>
  {loading ? (
    <>
      <Loader2 className="w-4 h-4 animate-spin" />
      Submitting...
    </>
  ) : (
    'Submit'
  )}
</button>
```

### 4. Missing ARIA Labels

**❌ Don't:**
```tsx
<button onClick={close}>
  <X className="w-4 h-4" />
</button>
```

**✅ Do:**
```tsx
<button onClick={close} aria-label="Close">
  <X className="w-4 h-4" />
</button>
```

## Migration Checklist

When updating existing components to v1.1:

- [ ] Replace all hardcoded hex colors with semantic tokens
- [ ] Replace Tailwind color classes (e.g., `text-red-400` → `text-error`)
- [ ] Update buttons to use standard variants
- [ ] Add loading states to async operations
- [ ] Verify ARIA labels on icon-only buttons
- [ ] Test keyboard navigation
- [ ] Verify color contrast meets accessibility standards

## Resources

- **Design Tokens:** See `design-tokens.md` for complete token reference
- **Button Variants:** See `button-variants.md` for usage guidelines
- **Accessibility:** See `accessibility-validation.md` for compliance report
- **Testing:** See `test-validation.md` for validation results
- **Specification:** See `theme.spec.md` for complete theme spec

## Questions?

For questions or clarifications about the v1.1 style system, refer to the documentation files in `openspec/changes/ui-theme-v1-1-semantic-consistency/`.
