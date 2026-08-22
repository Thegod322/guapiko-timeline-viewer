# Antigravity Slash Commands Reference

This document summarizes the core Antigravity slash commands and subagents utilized throughout the AI-First development workflow for **Softgames — Operation Close Win**.

---

## 1. /learn
- **Purpose:** Persists empirical findings, architectural rules, and bug solutions back into the project's living skill file (softgames-closewin).
- **Usage in Project:** Triggered at the end of each session to prevent context drift and ensure subsequent chat sessions inherit newly discovered invariants (such as bounding box geometry formulas, Golden Seed mining protocols, and multi-persona thresholds).

---

## 2. /browser
- **Purpose:** Launches an automated headless/interactive browser subagent to visually inspect, playtest, and verify running web applications.
- **Usage in Project:** Used to inspect layout responsiveness, test drag-and-drop level uploads, verify UI rendering on GitHub Pages, and audit the Difficulty Tuner card layouts.

---

## 3. /grill-me
- **Purpose:** Initiates an interactive adversarial design interview where the AI challenges assumptions, explores edge cases, and aligns on technical trade-offs before implementation.
- **Usage in Project:** Used to stress-test the Candidate Report narrative, examine survivorship bias trade-offs in CWR, and refine the delivery package structure.

---

## 4. /btw
- **Purpose:** Quick side-inquiry channel to query project state, timeline metrics, or code facts without disrupting the main conversation thread.
