# ⏱️ Guapiko Timeline Tracker & Chrono-Engine
> **Interactive AI Development Timeline, Transcript Auditor & Density Visualizer**  
> 🌐 **Live Web Viewer:** [https://thegod322.github.io/guapiko-timeline-viewer/](https://thegod322.github.io/guapiko-timeline-viewer/)

---

## 🌟 Overview

The **Guapiko Timeline Tracker** is a developer tool designed to parse local AI agent conversation transcripts (`transcript.jsonl`), calculate exact active development time vs idle gaps/playtesting, and generate an interactive, searchable 44+ hour visual timeline.

```
[transcript.jsonl] ──> [scripts/timeline_analyzer.py] ──> [index.html (Interactive Dashboard)]
                                                      └──> [Console Summary & Metrics]
```

---

## 🚀 Features

- **⚡ Active Time vs. Gaps Calculation:** Distinguishes between pure code generation / tool execution time and human deliberation, sleep, breaks, and manual playtesting.
- **📊 44+ Hour Activity & Density Grid:** Hourly heatmap visualising development intensity with direct scroll-to-turn navigation.
- **🔍 Live Search & Filter:** Filter events by prompt keywords, executed tools, modified files, and session badges.
- **📜 Integrated Transcript Archive:** Browse turn-by-turn prompts, tool executions, and file diffs.
- **Zero-Dependency Static HTML:** Fully self-contained dashboard requiring no external backend or build step.

---

## 📁 Repository Structure

```
guapiko-timeline-viewer/
├── index.html                    # Interactive Timeline Dashboard
├── scripts/
│   └── timeline_analyzer.py      # Core Chrono-Engine CLI parser
├── data/
│   └── timeline_chats.json       # Session registry configuration
├── transcripts/                  # Raw conversation transcripts archive (.jsonl)
│   ├── session_01_3941989a.jsonl
│   ├── session_02_103ab5c9.jsonl
│   ├── session_03_ab542134.jsonl
│   ├── session_04_ec4b518d.jsonl
│   ├── session_05_34b6f13f.jsonl
│   └── session_06_3116d3cf.jsonl
└── README.md
```

---

## 💻 CLI Usage

```bash
# 1. Run full analysis and update index.html
python scripts/timeline_analyzer.py

# 2. Display hourly activity grid in terminal
python scripts/timeline_analyzer.py --hourly

# 3. View break/gap registry
python scripts/timeline_analyzer.py --gaps

# 4. Inspect specific session details
python scripts/timeline_analyzer.py --chat 2

# 5. Output raw JSON for agent consumption
python scripts/timeline_analyzer.py --json
```

---

## 🌐 Live Deployment
The interactive viewer is deployed automatically to GitHub Pages:  
👉 **[https://thegod322.github.io/guapiko-timeline-viewer/](https://thegod322.github.io/guapiko-timeline-viewer/)**
