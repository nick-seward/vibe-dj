# Button Variant Usage Guidelines

**Version:** 1.1  
**Last Updated:** 2026-02-23

## Overview

Vibe-DJ provides five button variants, each with specific semantic meaning and use cases. All variants follow consistent styling patterns and accessibility standards.

## Button Variants

### 1. Primary Button (`.btn-primary`)

**Use for:** Main actions, primary CTAs, form submissions

**Styling:**
- Background: `--color-primary` (#8b5cf6)
- Hover: `--color-primary-hover` (#7c3aed)
- Text: White
- Padding: `px-6 py-2.5`
- Border radius: `rounded-lg`
- Disabled: 50% opacity, `cursor-not-allowed`

**Example:**
```tsx
<button className="btn-primary">
  Save Changes
</button>

// With loading state
<button className={`btn-primary ${loading ? 'btn-loading' : ''}`} disabled={loading}>
  {loading ? 'Saving...' : 'Save Changes'}
</button>
```

**When to use:**
- Save/Submit buttons in forms
- Primary action in modals
- Main CTA on a page
- Confirm actions

### 2. Secondary Button (`.btn-secondary`)

**Use for:** Secondary actions, cancel buttons in modals

**Styling:**
- Background: `--color-surface` (#1a1a2e)
- Hover: `--color-surface-hover` (#252540)
- Text: `--color-text` (#f8fafc)
- Border: `--color-border` (#334155)
- Padding: `px-6 py-2.5`
- Border radius: `rounded-lg`

**Example:**
```tsx
<button className="btn-secondary">
  Cancel
</button>
```

**When to use:**
- Cancel buttons in modals
- Secondary actions alongside primary buttons
- Non-critical actions

### 3. Outline Button (`.btn-outline`)

**Use for:** Alternative actions, less prominent CTAs

**Styling:**
- Background: Transparent
- Hover: `--color-primary` background, white text
- Text: `--color-primary` (#8b5cf6)
- Border: `--color-primary`
- Padding: `px-6 py-2.5`
- Border radius: `rounded-lg`
- Disabled: 50% opacity, `cursor-not-allowed`

**Example:**
```tsx
<button className="btn-outline">
  Learn More
</button>
```

**When to use:**
- Alternative actions
- Less prominent CTAs
- Actions that need visual distinction from primary
- Secondary navigation

### 4. Ghost Button (`.btn-ghost`)

**Use for:** Tertiary actions, subtle interactions

**Styling:**
- Background: Transparent
- Hover: `--color-surface-hover` (#252540)
- Text: `--color-text` (#f8fafc)
- No border
- Padding: `px-6 py-2.5`
- Border radius: `rounded-lg`
- Disabled: 50% opacity, `cursor-not-allowed`

**Example:**
```tsx
<button className="btn-ghost">
  Skip
</button>
```

**When to use:**
- Tertiary actions
- Subtle interactions
- Actions that shouldn't draw attention
- Inline actions in lists

### 5. Danger Button (`.btn-danger`)

**Use for:** Destructive actions, delete operations

**Styling:**
- Background: `--color-error` (#ef4444)
- Hover: Darker red (#dc2626)
- Text: White
- Padding: `px-6 py-2.5`
- Border radius: `rounded-lg`
- Disabled: 50% opacity, `cursor-not-allowed`

**Example:**
```tsx
<button className="btn-danger">
  Delete Profile
</button>

// In ProfilesTab delete confirmation
<motion.button
  onClick={handleDeleteConfirm}
  disabled={deleting}
  whileHover={!deleting ? { scale: 1.02 } : {}}
  whileTap={!deleting ? { scale: 0.98 } : {}}
  className="btn-danger flex items-center gap-2 px-4 py-2 text-sm"
>
  {deleting ? (
    <>
      <Loader2 className="w-4 h-4 animate-spin" />
      Deleting...
    </>
  ) : (
    <>
      <Trash2 className="w-4 h-4" />
      Delete
    </>
  )}
</motion.button>
```

**When to use:**
- Delete operations
- Destructive actions
- Actions that cannot be undone
- Critical confirmations

## Loading States

All button variants support loading states using the `.btn-loading` class.

**Implementation:**
```tsx
// Add btn-loading class and disable the button
<button 
  className={`btn-primary ${loading ? 'btn-loading' : ''}`}
  disabled={loading}
>
  {loading ? 'Loading...' : 'Submit'}
</button>

// With spinner icon (recommended)
<button className="btn-primary" disabled={loading}>
  {loading ? (
    <>
      <Loader2 className="w-4 h-4 animate-spin" />
      Saving...
    </>
  ) : (
    'Save Changes'
  )}
</button>
```

**Loading state features:**
- Spinner animation inherits text color for proper contrast
- `cursor-wait` indicates loading
- Button is disabled during loading
- Contextual text (e.g., "Saving...", "Loading...")

## Button Combinations

### Modal Actions
```tsx
<div className="flex gap-3 justify-end">
  <button onClick={onCancel} className="btn-secondary">
    Cancel
  </button>
  <button onClick={onConfirm} className="btn-primary">
    Confirm
  </button>
</div>
```

### Destructive Confirmation
```tsx
<div className="flex gap-3 justify-end">
  <button onClick={onCancel} className="btn-secondary">
    Cancel
  </button>
  <button onClick={onDelete} className="btn-danger">
    Delete
  </button>
</div>
```

### Multiple Actions
```tsx
<div className="flex gap-3">
  <button className="btn-primary">Save</button>
  <button className="btn-outline">Save as Draft</button>
  <button className="btn-ghost">Cancel</button>
</div>
```

## Accessibility

All button variants meet accessibility standards:

- ✅ **Contrast:** All variants meet WCAG 2.1 AA (4.5:1 minimum)
- ✅ **Focus indicators:** 2px ring in primary color (6.1:1 contrast)
- ✅ **Keyboard navigation:** Support Enter and Space keys
- ✅ **Disabled states:** Clear visual indication with reduced opacity
- ✅ **Loading states:** Maintain disabled appearance, prevent interaction

### ARIA Attributes

Use appropriate ARIA attributes for icon-only buttons:

```tsx
<button className="btn-ghost" aria-label="Close settings">
  <X className="w-4 h-4" />
</button>
```

## Common Patterns

### Form Submit Button
```tsx
<button 
  type="submit"
  className="btn-primary w-full"
  disabled={!isValid || submitting}
>
  {submitting ? 'Submitting...' : 'Submit'}
</button>
```

### Icon + Text Button
```tsx
<button className="btn-primary flex items-center gap-2">
  <Save className="w-4 h-4" />
  Save Changes
</button>
```

### Conditional Variant
```tsx
<button 
  className={`${showSuccess ? 'bg-success text-white' : 'btn-primary'}`}
  disabled={showSuccess}
>
  {showSuccess ? (
    <>
      <CheckCircle className="w-4 h-4" />
      Saved
    </>
  ) : (
    'Save'
  )}
</button>
```

## Migration Guide

### From Hardcoded Styles

**Before:**
```tsx
<button className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2.5 rounded-lg">
  Save
</button>
```

**After:**
```tsx
<button className="btn-primary">
  Save
</button>
```

### From Inline Styles

**Before:**
```tsx
<button 
  style={{ 
    backgroundColor: '#ef4444',
    color: 'white',
    padding: '0.625rem 1.5rem',
    borderRadius: '0.5rem'
  }}
>
  Delete
</button>
```

**After:**
```tsx
<button className="btn-danger">
  Delete
</button>
```

## Best Practices

1. **Use semantic variants** - Choose variants based on action meaning, not just appearance
2. **Consistent loading states** - Always show loading feedback for async operations
3. **Proper hierarchy** - Use primary for main actions, secondary for alternatives
4. **Danger for destructive** - Always use danger variant for delete/destructive actions
5. **Accessibility first** - Include ARIA labels for icon-only buttons
6. **Test keyboard navigation** - Ensure all buttons work with keyboard
7. **Maintain consistency** - Use the same variant for similar actions across the app

## See Also

- `design-tokens.md` - Complete design token reference
- `accessibility-validation.md` - Accessibility compliance report
- `theme.spec.md` - Theme specification
