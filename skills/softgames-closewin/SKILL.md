---
name: softgames-closewin
description: >-
  Architectural guide, game mechanics reference, and simulation rules for the Softgames "Operation Close Win" project. 
  Covers the 2-module PixiJS + TypeScript + GSAP data-driven architecture: Playable Tripeaks Prototype, Procedural Vector Graphics, and Monte Carlo Difficulty Tuner.
---

# Softgames — Operation Close Win (Technical Game Designer Project)

## 1. Project Overview & Mission

This skill provides complete domain knowledge, technical architecture, mathematical models, and development protocols for **Operation Close Win** — a Technical Game Designer take-home project for **Softgames**.

### The Core Challenge
- **Game:** Solitaire Tripeaks.
- **Problem:** Automated levels are unbalanced and "swingy" — players either lose too early or win with 15+ cards remaining in the draw pile.
- **Objective ("Close Win"):** Calibrate levels so that **70% of wins occur in a "Close Win" emotional state**, defined as having **fewer than 3 cards remaining in the draw pile (0, 1, or 2 cards left)**:
  $$\text{Close Win Rate (CWR)} = \frac{N_{\text{wins with Remainder } \in \{0, 1, 2\}}}{N_{\text{total wins}}} \times 100\% = 70\% \pm 2\%$$
- **Design Philosophy:** Minimalist visual presentation focused strictly on **pure gameplay feel, difficulty pacing, and balance** without distracting meta-game/arcade clutter (no coins, no jokers, no booster buttons, no stars).
- **Data Source:** 4 raw level JSON files (`level_25`, `level_31`, `level_43`, `level_54`).
- **Tasks Registry:** `Projects/SoftGames/tasks/` (`task_01` to `task_07`).

---

## 2. System Architecture & Tech Stack

The project is built as a **100% Data-Driven Web Application** with two main tabs:

```
softgames-closewin/
├── data/
│   └── levels/               # Raw and calibrated level JSON files
│       ├── level_25.json
│       ├── level_31.json
│       ├── level_43.json
│       └── level_54.json
├── src/
│   ├── core/                 # Shared Data Models, Rules & Simulation Engine
│   │   ├── types.ts          # Level, Card, Modifier, Simulation types
│   │   ├── CardGraph.ts      # Card overlap, depth, and reachability graph
│   │   ├── TripeaksEngine.ts # Core game state machine (headless-capable)
│   │   └── MonteCarloBot.ts  # Heuristic simulation agent & Deck Size Tuner
│   ├── game/                 # Tab 1: Playable Game Prototype (PixiJS + GSAP)
│   │   ├── GameView.ts       # Minimalist PixiJS Stage, Card Sprites, Board Renderer
│   │   ├── CardTextureFactory.ts # Procedural Vector/SVG Card & Badge Generator
│   │   ├── BoardLayout.ts    # Coordinate mapper (x, y, depth, canvas scaling)
│   │   └── AnimationFX.ts    # Clean GSAP transitions, flips, modifier states
│   ├── testing/              # Tab 2: Visual Testing & Calibration Suite
│   │   ├── TestingDashboard.ts # UI with Mode 1 (Simulation Test) & Mode 2 (Calibration)
│   │   ├── AutoCalibrator.ts   # Mode B: Automated target search (70% Close Win)
│   │   ├── ChartsView.ts       # Win rate curves, Close Win histograms, Bomb stats
│   │   └── JsonExporter.ts     # Export calibrated level JSONs
│   ├── workers/              # Multi-threaded Web Workers
│   │   └── sim.worker.ts     # Background simulation thread
│   ├── ui/                   # Responsive Shell & UI Controls
│   │   └── Layout.css        # Adaptive layout for desktop & mobile
│   └── main.ts               # Application entry point & tab switcher
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Core Technologies:
- **PixiJS (v8):** High-performance 2D WebGL/Canvas rendering for card boards, depths, and clean modifier states.
- **TypeScript:** Strict type safety for level schemas, game states, and simulation metrics.
- **GSAP (GreenSock):** Smooth, clean transitions for card draws, waste pile stacks, and state updates.
- **Vite:** Instant HMR, lightweight bundle, zero-friction local development.
- **Zero-Asset Procedural Vector Rendering (`CardTextureFactory`):** Generates all 52 cards, suits (♠♥♦♣), backs, and dynamic modifier badges (bomb timers, locks with chains, keys, zaps) via code/SVG. No external raster image dependencies.
- **Responsive / Adaptive UI:** Auto-scales to fit desktop monitors, laptops, and mobile screens seamlessly.

---

## 3. Game Rules & Data Structure Specification

### A. Tripeaks Core Mechanics
1. **Board Play:** A card is playable only if it is **face-up and not covered by any card with a higher `depth`**.
2. **Matching Rule:** A card on the board can be cleared if its value is **$\pm 1$ from the active Waste card** (Ace wraps to King: $A \leftrightarrow K \leftrightarrow Q \dots 2 \leftrightarrow A$).
3. **Draw Pile (`cards_in_stack`):** Clicking the draw pile deals the next card onto the waste pile (costs 1 card from resource pool). Remaining count is displayed directly on the deck badge.
4. **Win Condition:** Clearing all board cards (`"win_criteria": [{ "type": "clear_all" }]`).
5. **Loss Condition:** Running out of cards in `cards_in_stack` with no valid board moves left, OR a `bomb` timer reaching 0.

### B. Card Modifiers Reference
- 🔒 **`lock`:** Card with regular rank/suit under a lock barrier. Cannot be matched ($\pm 1$) until a Key is collected. When unlocked, remains on the board as a standard playable value card. Shakes on invalid click.
- 🔑 **`key`:** Pure item entity (no rank/suit). When clicked/collected, floats up and dissolves directly (does NOT enter waste pile; active hand card stays unchanged). Instantly unlocks ALL currently existing lock cards on the board.
- 💣 **`bomb`:** Contains a move countdown timer (e.g., `"timer": 5`). Decrements on BOTH board plays (`playCard()`) and deck draws (`drawCard()`). If timer hits 0 before being cleared $\rightarrow$ **Instant Defeat (`bomb_exploded`)**.
- ⚡ **`zap`:** When collected, immediately clears all cards sharing the same horizontal row ($|y - y_{\text{zap}}| \le 30\text{px}$).

### C. Depth & Overlap Coordinate Rules
- `depth`: Integer layer ($0$ is bottom, higher depth sits on top visually).
- Level coordinate spacing has spacing deltas of $\Delta x = 96\text{px}, 160\text{px}$ and $\Delta y = 96\text{px}, 144\text{px}$.
- Spatial bounding boxes in level space must be `CARD_WIDTH = 100`, `CARD_HEIGHT = 150` with factor $0.98$:
  $$|\Delta x| < \frac{W_A + W_B}{2} \cdot 0.98 \quad \land \quad |\Delta y| < \frac{H_A + H_B}{2} \cdot 0.98$$
  *(Note: A height $<150\text{px}$ fails the $\Delta y = 144\text{px}$ threshold by $<3\text{px}$, causing covered cards to falsely appear face-up).*
- Card $B$ becomes playable (and turns `faceUp: true`) when all cards covering it are removed.

### D. Rendering & Animation Scale Invariants
- `BoardLayout.scale` is the single source of truth for on-screen sizing.
- All `AnimationFX` routines must receive `scale` as an argument and never hardcode `scale: 1.0` or `1.05`.

---

## 4. Execution Workflow & Tasks Registry

The project is decomposed into 8 autonomous tasks located in `Projects/SoftGames/tasks/`:
1. `task_01_core_types_and_card_graph.md`: TypeScript models, level JSON parser & spatial overlap graph.
2. `task_02_headless_tripeaks_engine.md`: Pure TypeScript headless FSM engine with matching rules, bombs, locks, keys, zap, and undo.
3. `task_03_card_texture_factory_and_layout.md`: Procedural vector/SVG texture generator and responsive board layout (Pure gameplay focus).
4. `task_04_playable_game_prototype.md`: Tab 1 PixiJS v8 interactive game view, card animations, and level switcher.
5. `task_05_monte_carlo_bot_and_worker.md`: Heuristic IS-Monte Carlo bot with bomb/key priorities and Web Worker simulation thread.
6. `task_06_difficulty_tuner_and_dashboard.md`: Tab 2 Auto-Calibrator (Bisection search for 70% Close Win) and SVG charts.
7. `task_07_documentation_and_delivery.md`: Final calibration summary, AI-first workflow report, and production README.
8. `task_08_persona_calibration_and_unified_analysis.md`: Multi-Persona stress testing (Casual, Medium, Expert), dynamic on-demand golden seed mining, and embedded card-level calibration matrix.

---

## 5. Tab 1: 🎮 Game (Playable Level Feel Prototype)

**Goal:** Minimalist, clean visual prototype allowing game designers to play through any level to verify the tactile flow, layout, and pacing of the level.

### Pure Gameplay UI Elements:
- **1. Board Area:** Accurate $x, y$ coordinates and $Z$-index layer rendering based on `depth`. Uncovered cards show face numbers; covered show royal blue pattern back. Dedicated procedural textures for lock plates with chains (`card_lock_full`), ticking bomb badges, keys (`card_key_full`), and zaps (`card_zap_full`).
- **2. Deck / Draw Pile (Bottom Left):** Layered card stack with a prominent white number badge in the corner showing remaining count in `cards_in_stack`.
- **3. Active Waste Card (Bottom Center):** Face-up card showing current target value.
- **4. Minimalist Dev Toolbar (Outside Canvas):** Level selector (`level_25`, `level_31`, `level_43`, `level_54`), Restart button with randomized PRNG seed, `Keep seed` toggle, and Undo button.
- **Explicitly Excluded:** No coin balances, no 3-star meters, no paid booster buttons, no joker purchase buttons.

---

## 6. Tab 2: 📊 Testing (Simulation & Difficulty Calibration)

**Goal:** Visual interface driving the high-speed headless simulation engine with **two distinct operating modes**:

### Mode A: Parameter Simulation Test
- Select level and set custom parameters (`cards_in_stack` length, simulation iteration count $N$).
- Expandable accordion for bot weights ($w_{\text{uncover}}, w_{\text{depth}}, w_{\text{chain}}$), bomb defusal urgency, and target tolerance.
- "↺ Revert All Settings to Default" button for instant baseline reset.
- Live progress feedback banner and animated loading states.
- View immediate analytics:
  - Overall Win Rate %
  - Close Win Rate % (proportion of wins with 0, 1, 2 cards left)
  - Remaining cards distribution histogram
  - Loss causes breakdown (Out of cards vs Bomb exploded)

### Mode B: Calibration (Auto-Tuner)
- Automated search & parameter adaptation algorithm.
- Iteratively tests candidate deck sizes to find the exact `cards_in_stack` that satisfies:
  $$\text{Close Win Rate} = \frac{\text{Wins with } (\text{Draw Pile Remainder} \in \{0, 1, 2\})}{\text{Total Wins}} \approx 70\%$$
- 1-Click JSON export of calibrated level data for game production.

---

## 7. Production Calibration Benchmark & Ground Truth

### Mode A: Strict Brief Target (70% Close Win Rate)
Calibrated using bisection search targeting $CWR = 70\% \pm 2\%$ ($N=5,000$ per candidate):

| Level ID | Mechanics & Modifiers | Brief Deck | Calibrated CWR | Pass Rate | Abs Close Wins (per 1k) | Near Misses (per 1k) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `level_25` | Standard Layout (21 cards) | **15 cards** | **72.9%** | 2.6% | 19 players | 88 players |
| `level_31` | ⚡ Zap + 🔒 2 Locks + 🔑 1 Key | **15 cards** | **68.0%** | 4.5% | 31 players | 125 players |
| `level_43` | Complex Multi-Layer (28 cards) | **16 cards** | **70.5%** | 3.1% | 22 players | 93 players |
| `level_54` | 💣 Bomb Countdown ($T = 5$) | **13 cards** | **71.1%** | 3.3% | 24 players | 103 players |

### Mode B: Multi-Objective Absolute Peak (Balanced Retention & Near Miss Experience)
Optimizes the total dramatic conversion cohort ($\text{Abs Close Wins} + 0.4 \cdot \text{Near Misses}$):

| Level ID | Mechanics & Modifiers | Peak Deck | Pass Rate | CWR | Abs Close Wins (per 1k) | Near Misses (per 1k) | Total High Excitement |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `level_25` | Standard Layout (21 cards) | **28 cards** | **44.3%** | 30.2% | **134 players** | **279 players** | **412 / 1,000 (41.2%)** |
| `level_31` | ⚡ Zap + 🔒 2 Locks + 🔑 1 Key | **26 cards** | **41.7%** | 31.4% | **131 players** | **275 players** | **406 / 1,000 (40.6%)** |
| `level_43` | Complex Multi-Layer (28 cards) | **24 cards** | **25.4%** | 43.7% | **111 players** | **259 players** | **370 / 1,000 (37.0%)** |
| `level_54` | 💣 Bomb Countdown ($T = 5$) | **20 cards** | **17.2%** | 39.3% | **68 players** | **141 players** | **209 / 1,000 (20.9%)** |

### Mode C: Dynamic On-Demand Golden Seed Mining (Zero-Bloat Architecture)
Instead of bundling multi-megabyte static pre-mined seed files into the client bundle, the engine dynamically mines 150 verified 100% winnable Close-Win seeds *specifically tailored to each calibrated target hand size* ($K_{70\%}$, $K_{\text{peak}}$, $K_{\text{orig}}$) in real time via background Web Workers.

- **Deterministic Yield:** Scans seeds rapidly (~8,000 seeds/s) and isolates seeds that pass $\ge 2$ verification runs.
- **Client Bundle Footprint:** Keeps the production bundle under **465 kB** (zero static data overhead).

### Heuristic Agent Priority & Utility Formula
1. **Urgent Bomb Defusal** ($T_{\text{bomb}} \le 2$): Play bomb card or covering cards immediately.
2. **Key Unlocking**: Play key if locked cards exist on the board.
3. **High-Yield Zap**: Play zap if $\ge 2$ cards exist on the same row.
4. **Utility Match Function**:
   $$U(m) = 3.0 \cdot N_{\text{uncovered}}(m) + 2.0 \cdot \text{depth}(m) + 1.5 \cdot L_{\text{chain}}(m)$$

### Hybrid Build Architecture
- Exclude Node-based test runners from browser compilation in `tsconfig.json`:
  ```json
  {
    "include": ["src"],
    "exclude": ["src/**/test_*.ts", "src/**/calibrate_*.ts", "src/**/diagnostics_*.ts", "src/**/mine_*.ts"]
  }
  ```

---

## 8. Deliverables & Evaluation Checklist

- [x] **Functional Web Application:** Both Game and Testing tabs working seamlessly in browser.
- [x] **Data Calibration:** Exact optimal `cards_in_stack` values found for `level_25`, `level_31`, `level_43`, `level_54`.
- [x] **Production Build:** Clean `npm run build` compilation with zero TypeScript or Vite errors.
- [x] **Clean Handover:** Clear README setup instructions, baseline vs calibrated comparison table, and AI-First report.

---

## 9. Golden Seed Mining & Hand-Size Parameterization Protocol

### Definition of a Curated Golden Seed
1. **100% Winnable Close Win**:
   - Status: `won`.
   - Remaining cards in draw pile / hand: $\le 2$ (0, 1, or 2 cards).
   - Validation: Must pass $\ge 2$ independent validation runs with the heuristic bot to guarantee deterministic stability and rule out non-deterministic flukes.
2. **Near Miss Separation**:
   - Losses with $\le 2$ cards remaining on the board are classified as **Near Misses** (monetization/conversion triggers) and must NOT be mixed into the standard Golden Win pool.

### Hand Size (Deck Size) Synchronization Invariant
- Every simulation, auto-tuning step, and mining routine MUST accept `deckSize` as a first-class parameter.
- The Playable Prototype and Tuner must remain synchronized: changing hand size in one view immediately reflects in the other.

### Unified Restart Protocol
- In casual puzzle testbenches, the `Keep seed` toggle must govern ALL restart entry points:
  - Game Toolbar `Restart` button.
  - Victory Overlay `Play Again` button.
  - Defeat Overlay `Try Again` button.
- Replaying a seed must preserve BOTH `currentSeed` AND `customDeckSize`.

---

## 10. Multi-Persona Skill Sensitivity Benchmark & Archetypes

When evaluating level fairness, difficulty curves, and skill ceilings, simulations must be executed across 3 distinct player archetypes:

1. **🟢 Expert / Pro**:
   - Full lookahead, optimal deep chain matching ($w_{\text{uncover}} = 4.0, w_{\text{depth}} = 3.0, w_{\text{chain}} = 2.5$).
   - Proactive bomb defusal ($T \le 3$).
   - Epsilon-greedy sub-optimal move chance: **0%**.
2. **🟡 Medium / Core**:
   - Standard human heuristics, 1-step chain lookahead ($w_{\text{uncover}} = 2.0, w_{\text{depth}} = 1.5, w_{\text{chain}} = 1.0$).
   - Regular bomb defusal ($T \le 2$).
   - Epsilon-greedy sub-optimal move chance: **3%**.
3. **🔴 Casual / Novice**:
   - Greedy top-layer matching ($w_{\text{uncover}} = 0.5, w_{\text{depth}} = 0.5, w_{\text{chain}} = 0.0$).
   - Delayed bomb defusal ($T \le 1$).
   - Epsilon-greedy sub-optimal move chance: **15%**.

### Skill Expression Index ($\Delta PR$)
$$\Delta PR = PR_{\text{expert}} - PR_{\text{casual}}$$
- $\Delta PR \ge 35\%$: High Skill Dynamic / Wide dynamic range (rewards mastery).
- $15\% \le \Delta PR < 35\%$: Balanced Casual-to-Pro Progression.
- $\Delta PR < 15\%$: Accessible / Low skill variance.

---

## 11. Dual-Donut Statistical Differentiation Invariant

To eliminate confusion between global conversion rates and victory emotional tension:

1. **🌍 All Games Cohort Donut ($N = 2,000$)**:
   - **Sample Base**: 100% of all player attempts.
   - **Center Display**: **Pass Rate %** (e.g. `2.9%`).
   - **Slices**: Close Wins (≤2 in hand) %, Standard Wins (3+ in hand) %, Near Misses (≤2 on board) %, Deck Out Losses %, Bomb Detonations %.
2. **🏆 Win Quality Donut ($N_{\text{wins}}$)**:
   - **Sample Base**: 100% of ONLY winning games subset.
   - **Center Display**: **CWR %** (e.g. `70.2%`).
   - **Slices**: Close Wins (≤2 in hand: 70.2%) vs Standard Wins (3+ in hand: 29.8%).

---

## 12. Single-Target Full-Width UI & Symmetrical Manual Suite

In level balancing and executive simulation suites, present analytics in a clean, uncluttered, full-width viewport hierarchy:
- **Integrated Target 1 Header (Zero Detached Bars)**: Eliminate detached top workbench panels. All level management and primary actions are consolidated directly inside the Target 1 card header:
  `🎯 Target: 70% CWR` | `[Actual CWR Metric Badge]` | `[Level Selector Dropdown]` | `[📂 Upload JSON]` | `[💾 Download JSON]` | `[🚀 Run Analysis]` | `[🎮 Apply & Play]`
- **Symmetrical Manual Testing Suite**: Directly underneath the Target card, render a matching full-width Manual Testing card with an inline Hand Size stepper input (`-` / `+`) and a matching action suite:
  `🧪 Manual Simulation` | `[💾 Download JSON]` | `[▶ Run Simulation]` | `[🎮 Apply & Play]`
- **Top 4-KPI Executive Ribbon**:
  1. **Hand Size** ($K$ cards in stack).
  2. **Overall Pass Rate** (with sub-badge for Golden Seed Pass Rate).
  3. **Close Win Rate (CWR)** (percentage of wins with $\le 2$ cards left).
  4. **High-Excitement Cohort** (Close Wins + Near Misses per 1,000 players).
- **3-Panel Analytical Grid**:
  - **Panel 1 (Dual Donut Funnels)**: All-Games Conversion Funnel ($N=2,000$) alongside Win Quality CWR Donut.
  - **Panel 2 (Detailed Loss Causes & Flow)**: Deck Exhaustion vs Bomb Explosion loss bars, Average Moves, and Max Streaks.
  - **Panel 3 (Multi-Persona Benchmark Cards)**: 3 dedicated cards for 🟢 Expert (Pro), 🟡 Medium (Core), and 🔴 Casual (Novice), each featuring dual horizontal progress bars (`🌟 Solvable` vs `🎲 Raw PRNG`), skill expression gap tag ($\Delta PR$), and direct micro-stat pills (`CWR`, `Streak`, `Bomb Loss`).

---

## 13. 1:1 Statistical & Simulation Parity Invariant

To ensure complete fairness, trustworthiness, and mathematical accuracy:
- **Zero Divergence Rule**: `runManualSimulation()` and `runFullLevelAnalysisAsync()` MUST use the EXACT same underlying evaluation pipeline:
  - **Sample Size ($N = 2,000$)**: Exactly 2,000 Monte Carlo random PRNG games with identical PRNG seed sequences.
  - **Golden Seed Pool (150 Seeds)**: Exactly 150 verified 100% winnable Golden Seeds mined for the target hand size.
  - **Persona Simulation Depth ($6 \times 600$ runs)**: Exactly 600 Golden Seed runs and 600 Random Deal runs for each bot persona (Casual, Medium, Expert).
- **Multi-Stage Real-Time Progress Bar Feedback**:
  - Stage 1 `[0% -> 30%]`: Simulating random PRNG deals ($N = 2,000$).
  - Stage 2 `[30% -> 65%]`: Mining 150 verified Golden Seeds.
  - Stage 3 `[65% -> 100%]`: Simulating Casual, Medium, and Expert bots across both pools.

---

## 14. Custom Level Import, Batch Upload & Session Persistence

The system provides robust management for user-uploaded custom JSON levels:
- **Browser Session Persistence (`CustomLevelStorage`)**:
  - Automatically persists uploaded level JSON files into browser `localStorage` (`softgames_custom_levels_v1`).
  - Restores all uploaded levels upon page refresh or browser restart, populating them into both the Game View and Difficulty Tuner dropdown selectors.
- **Batch & Multi-File Support**:
  - `<input type="file" multiple accept=".json">` allows selecting 5, 10, or 20+ level JSON files simultaneously.
  - Automatic structure validation (`cards` array and `settings.cards_in_stack`).
- **Drag-and-Drop Capability**:
  - Dropping `.json` files onto the browser window automatically registers, validates, and adds them to the level catalog.
- **Bi-Directional Dropdown Synchronization**:
  - Level options are synchronized across `#level-select` (Game View) and `#tuner-level-select` (Tuner View) with clear identifiers (`📁 LevelName (Uploaded)`).

---

## 15. Seed Management, Restart Invariants & Instant Golden Fallback

- **Dynamic Restart Protocol**:
  - Clicking `↺ Restart` generates a guaranteed fresh PRNG seed different from the current seed (unless `Keep seed` is explicitly checked).
- **Golden Seed Mode Toggle**:
  - Toggling `🌟 Golden Seed` automatically unchecks `Keep seed` and selects a fresh verified seed from the 150-seed golden pool.
- **On-The-Fly Golden Seed Fallback (`SeedMiner.mineSingleGoldenSeed`)**:
  - If a user uploads a new custom level and immediately activates `🌟 Golden Seed` before running a full benchmark analysis, the engine instantly executes an on-the-fly search to locate and verify a 100% winnable Close-Win seed in milliseconds.

---

## 16. Level Schema Integrity & Explicit ID Normalization

- **Static JSON ID Normalization**:
  - Stock level JSON files often lack an explicit top-level `"id"` property in the raw JSON payload.
  - When importing static level files into TypeScript, always pass them through an explicit factory helper (e.g. `initLevel(id, raw)`):
    ```ts
    function initLevel(id: string, raw: any): LevelJSON {
      const lvl = { ...raw, id: raw.id || id };
      return lvl as LevelJSON;
    }
    ```
  - This prevents `level.id` from evaluating to `undefined`, which would otherwise cause dropdown synchronization and JSON export routines to silently fall back to `level_25`.
- **Dynamic File Export Naming**:
  - All JSON exporters (`JsonExporter.exportCalibratedLevel`) must explicitly guarantee valid `originalJson.id` resolution to produce deterministic filenames (`${levelId}_calibrated.json`).



