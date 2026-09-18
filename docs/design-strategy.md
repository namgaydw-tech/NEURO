# NEURO_PREDICT — UX & Design System Strategy

Scope: unified app shell + Dashboard flagship (v2). All other screens migrate onto this system incrementally.

---

## 1. Product & Users

**Product:** Clinical AI platform for neurological disease prediction (EEG + clinical data),
operating-theater scheduling, pharmacy operations, and a research library.
Ships as responsive web PWA and is packaged via Capacitor for Android/iOS.

**Primary users**
| Role | Primary goal | Frequency |
|---|---|---|
| Neurologist / clinician | Triage patients, run AI analyses, review diagnosis reports | Daily |
| OT coordinator | Book theaters, avoid slot conflicts | Daily |
| Pharmacist (3FA-cleared) | Verify prescriptions, manage medication records | Daily |
| Researcher | Browse EEG archive and papers | Weekly |

**Critical constraint:** this is a *clinical* tool. Trust, legibility, and error-recovery outrank
visual drama. The legacy "Neon Tokyo" glow is retired to a single accent used for *signal*,
not decoration.

## 2. User Journeys (top 3)

1. **Triage** — Sign in → Dashboard → scan KPI row → open a flagged patient from
   "Awaiting review" → run analysis → read report.
2. **Schedule** — Dashboard "Schedule OT" quick action → pick theater/slot → confirm →
   see booking in "Today's theaters".
3. **Recover** — Backend offline → dashboard shows inline error state with Retry →
   connection restored → stale-while-revalidate refresh (no layout shift).

## 3. Information Architecture

```
App shell
├── Overview
│   └── Dashboard            ← flagship, most-visited, first in nav (serial position)
├── Analysis
│   ├── AI Analysis
│   ├── Prediction Center
│   ├── Diagnosis Report
│   └── EEG Archive
├── Operations
│   ├── OT Scheduling
│   └── Pharmacy
└── Knowledge
    └── Research Papers
```

- **Critical actions** on Dashboard: run analysis, open patient, book OT.
- **Destructive actions** (cancel booking, delete record) are never co-located with
  frequent controls; they live inside their context screens behind confirmation dialogs.
- **Navigation:** ≤ 5 items visible at any level (Hick's Law). Desktop = persistent sidebar;
  tablet portrait = collapsible sidebar (overlay); mobile = bottom bar (4 primary) + drawer
  for the long tail.

## 4. Responsive Strategy

| Range | Shell |
|---|---|
| 320–479px | Single column, bottom nav, drawer, header search collapses to icon-button, stats 2-up → 1-up |
| 480–767px | + search field visible, stats 2-up |
| 768–1023px | Overlay sidebar (persistent toggle), 2-col dashboard grid, stats 4-up |
| 1024–1439px | Persistent sidebar, 2-col content grid, denser tables |
| ≥1440px | Content max-width grows (1320px), 3-col opportunity zones |

Techniques: CSS Grid + `clamp()` fluid type/spacing, `100dvh`, `env(safe-area-inset-*)`,
container-friendly auto-fit grids, zero JS-driven layout (removed the resize hack).

## 5. Design Tokens (`shared/design-system.css`)

- **Color:** semantic tokens (`--color-surface`, `--color-text-secondary`…), dark default,
  independently authored light theme (not an inversion).
- **Contrast fixes:** muted text raised to ≥ 4.5:1 on its background; primary buttons switched
  from white-on-#e83e6c (2.9:1 fail) to dark-ink-on-pink in light mode / ink-on-pink in dark,
  plus a `--color-on-primary` token.
- **Spacing:** 4px base scale; **Radii:** 6–20px scale; **Elevation:** 4 levels;
  **Motion:** 3 durations + 2 easings, all gated by `prefers-reduced-motion`.
- **Z-index ladder:** sidebar 40 < header 50 < modal 100 < toast 110.

## 6. Component Architecture (`shared/design-system.css` + `shared/ui.js`)

Buttons (primary/secondary/ghost/danger + sizes, loading & disabled states) · Inputs (label,
hint, error with `aria-describedby`) · Badges (status, never color-alone: icon + text) ·
Cards (+interactive) · Stat cards (+trend) · Table (wrapped, scrollable, sticky header ready) ·
Tabs · Modal (focus trap, Escape, focus restore) · Toasts (role=status/alert, tokenized) ·
Skeletons · Empty state (icon, title, description, one CTA) · Error state (what/why + Retry) ·
Progress bar · Avatar.

All interactive components meet ≥ 44×44px touch targets on coarse pointers.

## 7. Accessibility Strategy (WCAG 2.2 AA)

- Semantic landmarks: `header/nav/main/aside`; single `h1` per page.
- Skip link → main content (first Tab stop).
- Focus: 2px `:focus-visible` ring, offset, never removed; logical DOM order.
- Drawer: `aria-expanded` on trigger, focus trap while open, Escape closes, focus returns to trigger.
- Status colors always paired with text/icon (von Restorff used for *risk badges* only).
- Forms: visible persistent labels, `aria-invalid`, errors linked via `aria-describedby`.
- Live regions: toasts (`role=status`), async errors (`role=alert`).
- Touch: ≥44px targets, 8px separation between destructive and frequent controls.
- Contrast: all text ≥ 4.5:1, large text ≥ 3:1, verified for both themes.

## 8. State Matrix (Dashboard)

| Zone | Loading | Empty | Error |
|---|---|---|---|
| KPI stats | `—` placeholder with skeleton pulse | "0" with neutral caption | "—" + amber sync badge |
| Patients | 3 skeleton rows | Icon + "No patients yet" + CTA | Message + **Retry** button |
| Activity | 3 skeleton lines | Icon + explanation | Message + **Retry** button |
| Theaters today | skeleton chips | "Nothing scheduled" + CTA | Message + **Retry** |

Global: offline banner (navigator.onLine + listeners), stale data marked with timestamp.

## 9. Motion Spec

- Durations: 120ms (hover/press), 200ms (enter/exit), 350ms (drawer/modal).
- Easing: `cubic-bezier(0.16,1,0.3,1)` out; no bounce on clinical data.
- Choreography: stagger ≤ 40ms, first paint ≤ 3 elements; nothing animates twice.
- Skeleton shimmer 1.5s; suppressed entirely under reduced motion.

## 10. Platform Adaptation

- **Desktop:** hover states, persistent nav, keyboard shortcuts (`/` focuses search, `g d` nav — additive, discoverable, no trap).
- **Tablet:** overlay drawer + persistent toggle; larger gutters; split content grid.
- **Android (Material):** bottom nav with active pill, ripple-free but touch-elevation feedback, back button closes drawer (history API), status-bar theme-color sync.
- **iOS (HIG):** safe-area insets honored (notch/home indicator), no hover-dependent UI, `100dvh` keyboard-safe layout, standalone display via PWA meta.
