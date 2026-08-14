# Go TUI Framework Research & Selection

## Executive Summary

To reimplement the scanDOC Terminal UI (TUI) as a production-grade native Go application, we evaluated mature Go TUI frameworks across key criteria: rendering performance, composability, async execution model, component ecosystem, styling flexibility, and long-term maintainability.

**Selected Ecosystem**: **Charm (Bubble Tea + Lip Gloss + Bubbles)**

---

## Ecosystem Evaluation Matrix

| Criterion | Bubble Tea + Lip Gloss + Bubbles | tview + tcell | termui |
|---|---|---|---|
| **Architecture Pattern** | Elm Architecture (Model-View-Update) | Imperative Widget Tree | Canvas / Grid Dashboard |
| **State Management** | Unidirectional immutable message flow | Mutable widget callbacks & event listeners | Manual redrawing |
| **Async & Background Jobs** | Native `tea.Cmd` goroutine channels | Manual `tview.Application.QueueUpdateDraw` | Manual timer redraws |
| **Styling & Theming** | Lip Gloss (CSS-like flex, borders, colors) | Primitive formatting & color tags | Basic colors |
| **Component Library** | Bubbles (`table`, `list`, `filepicker`, `progress`, `spinner`) | Form widgets, Modal, Table | Widgets, Charts |
| **Terminal Resizing** | Native `tea.WindowSizeMsg` handling | Automatic widget resize | Manual grid calculation |
| **Community & Adoption** | GitHub CLI (`gh`), Charm tools, wide adoption | Mature classic framework | Niche dashboard tool |

---

## Architectural Rationale

### 1. Elm Architecture (Model-View-Update)
Bubble Tea enforces an explicit, unidirectional state flow:
- `Init() tea.Cmd`: Initializes initial commands.
- `Update(msg tea.Msg) (tea.Model, tea.Cmd)`: Receives user inputs, keypresses, background job messages, and screen change events. Returns updated state and optional async commands.
- `View() string`: Pure rendering function returning formatted terminal output.

This design completely eliminates race conditions and mutex locks across UI updates.

### 2. Native Goroutine Async Integration
Long-running document processing tasks, model downloads, and benchmark runs execute as standard Go goroutines wrapped in `tea.Cmd`. Upon completion or progress update, goroutines emit typed messages (`tea.Msg`) directly into Bubble Tea's main event loop.

### 3. Lip Gloss Declarative Layouts
Lip Gloss provides CSS-like styling primitives (`lipgloss.NewStyle()`) for borders, padding, margins, foreground/background HSL/RGB colors, text alignment, and dynamic width/height constraints.

### 4. Bubbles Pre-built Primitives
Provides tested, accessible UI primitives for file picking, data tables, search inputs, progress bars, and spinners.
