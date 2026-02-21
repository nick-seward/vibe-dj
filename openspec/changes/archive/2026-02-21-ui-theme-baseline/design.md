# Design Notes for UI Theme Baseline

## Inconsistencies Identified

### Color Usage Outside Theme Variables
- Error states use `text-red-400` and `bg-red-500` which are not defined in the theme CSS variables
- These should be added as semantic tokens: `--color-error`, `--color-error-bg` or similar

### Inconsistent Button States
- Some buttons have custom hover states (e.g., `hover:bg-primary/30`) that use opacity variants not defined as variables
- Missing button variants: ghost, outline, danger states
- Loading states are handled with custom icons but no standardized loading button style

### Typography Gaps
- No defined line-heights in theme variables
- Missing responsive typography scale definitions
- Heading hierarchy not formally defined beyond font weights

### Semantic Token Opportunities
- Add semantic colors: error, success, warning, info
- Add semantic variants for interactive states: focus, active, disabled
- Define component-specific tokens (e.g., card variants, input variants)

### Spacing and Layout
- No defined spacing scale in CSS variables
- Border radius scale incomplete (missing rounded-md, etc.)
- No shadow definitions (currently none used)

### Missing Design Tokens
- Z-index scale not defined
- Animation/transition timing not standardized beyond duration-200
- No elevation/shadow system

## Recommendations
- Extend CSS variables to include all used colors and semantic variants
- Create a more comprehensive design token system
- Define component variants in a consistent way (consider using class-variance-authority or similar)
- Add missing visual elements like shadows and z-index scale
- Standardize error/success states with theme colors
