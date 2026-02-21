## Why

The Vibe-DJ UI currently has an ad-hoc design system scattered across CSS classes and component styles. Colors, typography, and component patterns are inconsistently applied, with some elements using hardcoded values outside the defined theme variables. This creates maintenance issues and visual inconsistencies as the application grows.

Establishing a formal baseline design-system spec will:
- Document all current visual elements and patterns
- Identify inconsistencies and improvement opportunities
- Provide a foundation for consistent future development
- Enable better maintainability and scalability

## What Changes

Create a comprehensive design-system specification that captures the existing UI theme as a baseline, including:
- Complete color palette with hex values
- Typography scale and usage patterns
- Interactive component definitions (buttons, inputs, cards)
- Spacing, border radius, and other design tokens
- Identification of gaps and inconsistencies

## Capabilities

### New Capabilities
- `ui/theme`: Baseline design-system specification covering colors, typography, and components

### Modified Capabilities
None - this establishes the initial baseline

## Impact

- New spec file at `openspec/specs/ui/theme.spec.md`
- Design notes in change directory documenting inconsistencies
- No code changes - purely documentation and analysis
