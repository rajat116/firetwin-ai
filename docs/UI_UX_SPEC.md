# UI/UX Specification

**Last Updated**: 2026-09-03  
**Version**: 0.1.0

This document defines the user interface and experience requirements for FireTwin's public web application.

## Design Goals

1. **Scientific Credibility**: Professional, information-dense, evidence-based
2. **Accessibility**: Usable by researchers, students, and portfolio reviewers
3. **Clarity**: Complex geospatial and probabilistic information made understandable
4. **Performance**: Smooth interaction even with large datasets and animations

## Visual Language

### Typography

- **Headings**: System font stack or modern sans-serif (e.g., Inter, IBM Plex Sans)
- **Body**: Same as headings for consistency
- **Monospace**: Code, coordinates, IDs (e.g., SF Mono, Fira Code)
- **Size Scale**: 12px (small) → 14px (body) → 16px (sub-heading) → 20px+ (heading)

### Color System

#### Primary Palette

- **Brand**: `#E85D04` (Fire orange) - Use sparingly for key actions
- **Background**: `#FFFFFF` (light mode), `#1A1A1A` (dark mode)
- **Surface**: `#F5F5F5` (light), `#2A2A2A` (dark)
- **Text**: `#1A1A1A` (light mode), `#F5F5F5` (dark mode)
- **Text Secondary**: `#666666` (light), `#999999` (dark)

#### Functional Colors

- **Success**: `#10B981` (Green)
- **Warning**: `#F59E0B` (Amber)
- **Error**: `#EF4444` (Red)
- **Info**: `#3B82F6` (Blue)

#### Scientific Palettes

**Fire Probability** (Sequential):
```
Low → High: #FFFFCC → #FFEDA0 → #FEB24C → #F03B20 → #BD0026
```

**Burn Severity** (Sequential):
```
None → Extreme: #F7FCF5 → #C7E9C0 → #74C476 → #238B45 → #00441B
```

**Uncertainty** (Diverging):
```
Low ← Medium → High: #2166AC → #F7F7F7 → #B2182B
```

All palettes tested with [ColorBrewer](https://colorbrewer2.org/) for accessibility.

### Spacing System

```
xs:  4px
sm:  8px
md:  16px
lg:  24px
xl:  32px
2xl: 48px
3xl: 64px
```

### Elevation (Z-layers)

```
base:       z-0
surface:    z-10
overlay:    z-20
dropdown:   z-30
modal:      z-40
tooltip:    z-50
notification: z-60
```

## Layout Specifications

### Desktop (≥1280px)

#### Main Layout Grid

```
┌──────────────────────────────────────────────────┐
│  Header (64px fixed)                             │
├─────────┬────────────────────────────┬───────────┤
│         │                            │           │
│  Left   │       Center Map           │  Right    │
│  320px  │       (flexible)           │  360px    │
│         │                            │           │
├─────────┴────────────────────────────┴───────────┤
│  Timeline (120px fixed)                          │
└──────────────────────────────────────────────────┘
```

#### Responsive Breakpoints

- **Desktop Large**: ≥1920px
- **Desktop**: 1280px - 1919px
- **Tablet**: 768px - 1279px
- **Mobile**: <768px

### Component Specifications

#### Fire Catalogue (Left Panel)

**Search & Filter**:
- Search input with autocomplete
- Filter chips: State, Year, Size, Data Quality
- Sort dropdown: Date, Size, Name

**Fire Card**:
```
┌─────────────────────────────┐
│ Fire Name (16px, bold)      │
│ State | YYYY-MM-DD          │
│ Size: XXX acres             │
│ ⚠️ Data: Good/Partial       │
│                             │
│ [▶ View Forecast]           │
└─────────────────────────────┘
```

#### Map Controls

**Top-Right Overlay**:
- 🧭 Compass (reset bearing)
- ➕ Zoom in
- ➖ Zoom out
- 📐 2D/3D toggle
- 📷 Screenshot

**Layer Controls**:
- Checkbox tree structure
- Opacity sliders
- Legend expansion
- Visibility toggle

#### Timeline (Bottom Bar)

```
┌────────────────────────────────────────────────┐
│  T₀  ───●───●───●───●───●───●───● T₂₄         │
│      3h  6h  9h 12h 18h 24h                    │
│                                                 │
│  [◀◀] [▶] [▶▶]  Speed: 1x  Horizon: [6h ▼]   │
└────────────────────────────────────────────────┘
```

- **Observation markers** (●): Click to jump to time
- **Playback controls**: Backward, Play/Pause, Forward
- **Speed**: 0.5x, 1x, 2x, 4x
- **Horizon selector**: 3h, 6h, 12h, 24h

#### Metrics Panel (Right)

**Tabs**:
1. **Metrics**: IoU, Dice, Precision, Recall, Calibration
2. **Uncertainty**: Ensemble spread, confidence intervals
3. **Provenance**: Model version, data versions, run ID
4. **Briefing**: Natural language summary (optional LLM)

**Metric Card**:
```
┌─────────────────────────────┐
│ IoU (Intersection over Union)│
│                             │
│   0.72  ████████░░  ±0.05   │
│                             │
│ Good for 6h horizon         │
│ [ⓘ See methodology]         │
└─────────────────────────────┘
```

### Interaction Patterns

#### Map Inspection

**Click cell** → Popup:
```
┌───────────────────────────┐
│ Lat: 38.5234, Lon: -120.1│
│ Elevation: 1,234m         │
│ Slope: 15°, Aspect: SW    │
│ Fuel: Mixed Conifer       │
│ ───────────────────────   │
│ Fire Prob: 68% (±12%)     │
│ Arrival Time: T+4.2h      │
│ Last Obs: T+3h (VIIRS)    │
│ ───────────────────────   │
│ Model: Hybrid v0.2        │
│ Run: abc123def            │
└───────────────────────────┘
```

#### Model Comparison

**Side-by-side view**:
```
┌─────────────┬─────────────┐
│  Physics    │   Hybrid    │
│             │             │
│   [Map A]   │   [Map B]   │
│             │             │
├─────────────┼─────────────┤
│ IoU: 0.61   │ IoU: 0.74   │
└─────────────┴─────────────┘
```

**Swipe comparison**:
- Drag vertical slider left/right
- Forecast (left) | Observation (right)

#### Scenario Controls

**Wind Adjustment**:
```
Direction: [N▼]  Speed: [●────────] 15 mph
```

**Containment Line Drawing**:
```
┌───────────────────────────┐
│ [✏️ Draw] [⭘ Undo] [✓ Done]│
│                           │
│ Budget: 2.5 / 5.0 km      │
│ Effectiveness: ?          │
│                           │
│ [▶ Simulate]              │
└───────────────────────────┘
```

### Accessibility

#### Keyboard Navigation

- **Tab**: Cycle through focusable elements
- **Space/Enter**: Activate buttons
- **Arrow keys**: Map pan (when focused)
- **+/-**: Zoom in/out
- **Esc**: Close modals/popups

#### Screen Readers

- Semantic HTML: `<header>`, `<nav>`, `<main>`, `<aside>`
- ARIA labels for map controls
- Alt text for images
- Live regions for status updates

#### Focus Indicators

- Visible 2px outline on focus
- Color: `#3B82F6` (blue)
- Contrast ratio ≥3:1

### Animation & Motion

#### Forecast Animation

- **Frame rate**: 30-60 FPS
- **Transition**: Smooth opacity fade between time steps
- **Duration**: 2-4 seconds per horizon (adjustable with speed)
- **Easing**: Linear for time progression

#### UI Transitions

- **Panel slide**: 200ms ease-in-out
- **Fade in/out**: 150ms ease-in-out
- **Loading spinner**: Subtle rotation

#### Reduced Motion

Respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Loading States

#### Initial Load

```
┌───────────────────────────┐
│                           │
│      🔥 FireTwin         │
│                           │
│   Loading terrain...      │
│   ████████░░░░░  75%     │
│                           │
└───────────────────────────┘
```

#### Forecast Computation

```
┌───────────────────────────┐
│ Computing forecast...     │
│                           │
│ [████████░░] 80%         │
│                           │
│ Est. time: 12s            │
│                           │
│ [Cancel]                  │
└───────────────────────────┘
```

#### Partial Results

```
⚠️ Displaying partial results. Full data still loading.
```

### Error States

#### Network Error

```
┌───────────────────────────┐
│ ⚠️ Connection lost        │
│                           │
│ Unable to load forecast   │
│ data. Check your internet │
│ connection.               │
│                           │
│ [Retry]                   │
└───────────────────────────┘
```

#### Invalid Scenario

```
❌ Invalid scenario
Wind speed exceeds model training range (>50 mph).
Results may be unreliable.
```

### Mobile Considerations

- Touch targets: ≥44px × 44px
- Swipe gestures for timeline navigation
- Simplified layer controls (accordion)
- Single-column layout
- Bottom sheet for metrics

## Usability Testing Plan

### Test Scenarios

1. **First-time visitor**: Complete guided demo without help
2. **Fire selection**: Find and select California fire from 2024
3. **Forecast inspection**: Run 6-hour forecast, understand probability
4. **Model comparison**: Compare physics vs. hybrid model
5. **Scenario modification**: Change wind direction and observe impact
6. **Metric interpretation**: Explain what IoU=0.72 means

### Success Metrics

- **Task completion rate**: ≥80%
- **Time on task**: <5min for guided demo
- **User satisfaction**: ≥4/5 on usability scale
- **Errors**: <2 per session

### Participant Recruitment

- 2 ML/data science researchers
- 2 wildfire domain experts or students
- 1 non-technical portfolio reviewer

### Testing Protocol

1. Welcome and consent
2. Think-aloud protocol
3. Observe without intervention
4. Note confusion, errors, and hesitations
5. Post-test survey
6. Iterate on findings

Document results in `docs/design/usability/`.

## Design System Implementation

### Component Library

Use or create:
- Button variants: Primary, Secondary, Tertiary, Danger
- Input fields: Text, Number, Select, Slider
- Cards, Panels, Modals
- Toast notifications
- Progress bars
- Tooltips

### Design Tokens (CSS Variables)

```css
:root {
  --color-brand: #E85D04;
  --color-bg: #FFFFFF;
  --color-text: #1A1A1A;
  --spacing-md: 16px;
  --border-radius: 8px;
  --font-size-body: 14px;
  --transition-fast: 150ms;
}
```

### Responsive Images

Use `srcset` for retina displays:
```html
<img src="screenshot.png"
     srcset="screenshot@2x.png 2x"
     alt="FireTwin forecast">
```

## Design Deliverables

Before implementation:

1. ✅ This specification (complete)
2. ⬜ Low-fidelity wireframes (Phase 1)
3. ⬜ High-fidelity mockups (Phase 9)
4. ⬜ Design tokens and component library
5. ⬜ Usability test findings

Store in `docs/design/`.

## Tools & Resources

- **Design**: Figma, Sketch, or hand-drawn wireframes
- **Prototyping**: Figma, Adobe XD, or HTML/CSS
- **Usability Testing**: Zoom + screen recording
- **Accessibility**: axe DevTools, WAVE, Lighthouse

## References

- [MapLibre GL JS Documentation](https://maplibre.org/maplibre-gl-js/docs/)
- [deck.gl Examples](https://deck.gl/examples)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ColorBrewer 2.0](https://colorbrewer2.org/)
