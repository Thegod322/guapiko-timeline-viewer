#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GuapikoClaw Universal Timeline Analyzer & Chrono-Engine
------------------------------------------------------
Production Timeline & Chrono-Tracker for AI-First Game Development:
- Parses local conversation transcripts (transcript.jsonl)
- Computes active AI execution time vs idle/playtest gaps
- Extracts AI skills (/softgames-closewin, /guapiko-decompose-to-tasks, /learn, etc.)
- Embeds interactive skill documentation modal popups
- Supports bilingual English & Russian user prompt toggle
- Interactive Trading-Chart style Candlestick Timeframe Selector (1H, 2H, 4H, 1D, Fit)
- Standalone zero-dependency HTML dashboard with responsive density roadmap
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime, timezone, timedelta

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

LOCAL_TZ = timezone(timedelta(hours=2))
BRAIN_DIR = "C:/Users/natal/.gemini/antigravity/brain"
CONFIG_FILE = "data/timeline_chats.json"
TRANSLATIONS_FILE = "data/prompt_translations.json"
CURRENT_CONV_ID = "2ab178e2-f484-44bf-b57b-a0bb30c90f78"
PALETTE = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f43f5e", "#84cc16", "#a855f7"]

KNOWN_SKILLS = {
    "softgames-closewin": {"name": "softgames-closewin", "type": "skill", "icon": "🎯", "label": "/softgames-closewin", "url": "skills/softgames-closewin.md"},
    "guapiko-decompose-to-tasks": {"name": "guapiko-decompose-to-tasks", "type": "skill", "icon": "🧩", "label": "/guapiko-decompose-to-tasks", "url": "skills/guapiko-decompose-to-tasks.md"},
    "guapiko-timeline-tracker": {"name": "guapiko-timeline-tracker", "type": "skill", "icon": "⏱️", "label": "/guapiko-timeline-tracker", "url": "skills/guapiko-timeline-tracker.md"},
    "workflow-skill-creator": {"name": "workflow-skill-creator", "type": "skill", "icon": "🛠️", "label": "/workflow-skill-creator", "url": "skills/slash-commands.md"},
    "learn": {"name": "learn", "type": "command", "icon": "⚡", "label": "/learn", "url": "skills/slash-commands.md#1-learn"},
    "grill-me": {"name": "grill-me", "type": "command", "icon": "🎙️", "label": "/grill-me", "url": "skills/slash-commands.md#3-grill-me"},
    "browser": {"name": "browser", "type": "command", "icon": "🌐", "label": "/browser", "url": "skills/slash-commands.md#2-browser"},
    "btw": {"name": "btw", "type": "command", "icon": "💡", "label": "/btw", "url": "skills/slash-commands.md#4-btw"},
    "goal": {"name": "goal", "type": "command", "icon": "🎯", "label": "/goal", "url": "skills/slash-commands.md"},
    "schedule": {"name": "schedule", "type": "command", "icon": "⏰", "label": "/schedule", "url": "skills/slash-commands.md"},
    "teamwork-preview": {"name": "teamwork-preview", "type": "command", "icon": "👥", "label": "/teamwork-preview", "url": "skills/slash-commands.md"},
}

def extract_skills_from_step(raw_content, step_data):
    found = {}
    if not raw_content:
        return []
    
    # 1. Metadata skill tags: <SKILL>.../skills/(name)...</SKILL>
    m_skills = re.findall(r'<SKILL>.*?skills[\\\\/]([a-zA-Z0-9_\-]+)', raw_content, re.DOTALL | re.IGNORECASE)
    for s in m_skills:
        s_clean = s.lower()
        if s_clean in KNOWN_SKILLS:
            found[s_clean] = KNOWN_SKILLS[s_clean]

    # 2. Slash command mentions in metadata: /([a-zA-Z0-9_\-]+)\s+is a \[Slash Command\]
    m_slash = re.findall(r'/([a-zA-Z0-9_\-]+)\s+is a \[Slash Command\]', raw_content, re.IGNORECASE)
    for s in m_slash:
        s_clean = s.lower()
        if s_clean in KNOWN_SKILLS:
            found[s_clean] = KNOWN_SKILLS[s_clean]

    # 3. User request slash mentions: e.g. /softgames-closewin, /learn, etc.
    req_match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', raw_content, re.DOTALL)
    req_text = req_match.group(1) if req_match else raw_content
    for k, v in KNOWN_SKILLS.items():
        if re.search(r'/' + re.escape(k) + r'(?![a-zA-Z0-9_\-])', req_text, re.IGNORECASE):
            found[k] = v

    return list(found.values())

def load_skills_docs():
    skills_map = {
        "softgames-closewin": "Projects/Guapiko/guapiko-timeline-viewer/skills/softgames-closewin.md",
        "guapiko-decompose-to-tasks": "Projects/Guapiko/guapiko-timeline-viewer/skills/guapiko-decompose-to-tasks.md",
        "guapiko-timeline-tracker": "Projects/Guapiko/guapiko-timeline-viewer/skills/guapiko-timeline-tracker.md",
        "workflow-skill-creator": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "learn": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "grill-me": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "browser": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "btw": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "goal": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
        "schedule": "Projects/Guapiko/guapiko-timeline-viewer/skills/slash-commands.md",
    }
    docs = {}
    for k, p in skills_map.items():
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    docs[k] = f.read()
            except Exception:
                docs[k] = f"# {k}\n\nDocumentation file loaded."
        else:
            docs[k] = f"# {k}\n\nSkill specification for {k}."
    return docs

def load_prompt_translations(path=TRANSLATIONS_FILE):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def parse_iso(ts_str):
    if not ts_str:
        return None
    ts_str = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None

def format_dt(dt):
    if not dt:
        return ""
    local_dt = dt.astimezone(LOCAL_TZ)
    return local_dt.strftime("%d.%m.%Y %H:%M:%S")

def format_time_only(dt):
    if not dt:
        return ""
    local_dt = dt.astimezone(LOCAL_TZ)
    return local_dt.strftime("%H:%M:%S")

def format_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins < 60:
        return f"{mins}m {secs}s" if secs > 0 else f"{mins}m"
    hours = int(mins // 60)
    rem_mins = mins % 60
    return f"{hours}h {rem_mins}m"

def load_saved_chats(config_path=CONFIG_FILE):
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_chat_to_config(chat_id, title, badge="Custom", color=None, config_path=CONFIG_FILE):
    chats = load_saved_chats(config_path)
    for c in chats:
        if c["id"] == chat_id:
            c["title"] = title
            c["badge"] = badge
            if color: c["color"] = color
            break
    else:
        new_order = len(chats) + 1
        new_color = color or PALETTE[(new_order - 1) % len(PALETTE)]
        chats.append({
            "id": chat_id,
            "title": f"Chat {new_order}: {title}",
            "order": new_order,
            "badge": badge,
            "color": new_color
        })
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)
    print(f"✓ Chat {chat_id[:8]} saved to {config_path}")

def process_timeline(chat_configs, brain_dir=BRAIN_DIR):
    translations = load_prompt_translations()
    all_turns = []
    chat_summaries = []

    for cfg in chat_configs:
        cid = cfg["id"]
        p = f"{brain_dir}/{cid}/.system_generated/logs/transcript.jsonl"
        if not os.path.exists(p):
            continue

        steps = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        steps.append(json.loads(line))
                    except Exception:
                        pass

        if not steps:
            continue

        current_turn = None
        chat_turns = []

        for i, step in enumerate(steps):
            stype = step.get("type")
            source = step.get("source")
            created_at = step.get("created_at")
            dt = parse_iso(created_at)
            if not dt:
                continue

            if stype == "USER_INPUT" or source == "USER_EXPLICIT":
                if current_turn:
                    current_turn["end_dt"] = current_turn["steps"][-1]["dt"]
                    dur = max(1.0, (current_turn["end_dt"] - current_turn["start_dt"]).total_seconds())
                    current_turn["duration_sec"] = dur
                    current_turn["duration_fmt"] = format_duration(dur)
                    chat_turns.append(current_turn)

                raw_content = step.get("content", "")
                clean_content = re.sub(r"<USER_REQUEST>(.*?)</USER_REQUEST>", r"\1", raw_content, flags=re.DOTALL)
                clean_content = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", clean_content, flags=re.DOTALL)
                clean_content = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", clean_content, flags=re.DOTALL).strip()

                skills_used = extract_skills_from_step(raw_content, step)
                turn_idx = len(chat_turns) + 1
                turn_id = f"turn_{cfg['order']}_{turn_idx}"
                
                trans = translations.get(turn_id, {})
                user_prompt_en = trans.get("en", clean_content)
                user_prompt_ru = trans.get("ru", clean_content)

                current_turn = {
                    "turn_id": turn_id,
                    "chat_id": cid,
                    "chat_title": cfg["title"],
                    "chat_order": cfg["order"],
                    "badge": cfg.get("badge", "Chat"),
                    "color": cfg.get("color", "#3b82f6"),
                    "turn_index": turn_idx,
                    "user_step_index": step.get("step_index", i),
                    "start_dt": dt,
                    "end_dt": dt,
                    "duration_sec": 1.0,
                    "duration_fmt": "1s",
                    "user_prompt": user_prompt_en,
                    "user_prompt_en": user_prompt_en,
                    "user_prompt_ru": user_prompt_ru,
                    "user_prompt_preview": user_prompt_en[:180] + ("..." if len(user_prompt_en) > 180 else ""),
                    "skills_used": skills_used,
                    "steps": [{"dt": dt, "type": "USER_INPUT", "index": step.get("step_index", i)}],
                    "tool_calls": [],
                    "files_modified": []
                }
            else:
                if current_turn:
                    current_turn["steps"].append({"dt": dt, "type": stype, "index": step.get("step_index", i)})
                    t_calls = step.get("tool_calls", [])
                    for tc in t_calls:
                        if isinstance(tc, dict):
                            tname = tc.get("toolSummary", tc.get("toolAction", tc.get("name", "Action")))
                            current_turn["tool_calls"].append(tname)
                            args = tc.get("arguments", tc.get("Arguments", {}))
                            if isinstance(args, dict):
                                tf = args.get("TargetFile") or args.get("target_file")
                                if tf and tf not in current_turn["files_modified"]:
                                    current_turn["files_modified"].append(os.path.basename(tf))

        if current_turn:
            current_turn["end_dt"] = current_turn["steps"][-1]["dt"]
            dur = max(1.0, (current_turn["end_dt"] - current_turn["start_dt"]).total_seconds())
            current_turn["duration_sec"] = dur
            current_turn["duration_fmt"] = format_duration(dur)
            chat_turns.append(current_turn)

        if chat_turns:
            c_start = chat_turns[0]["start_dt"]
            c_end = chat_turns[-1]["end_dt"]
            active_sec = sum(t["duration_sec"] for t in chat_turns)

            chat_summaries.append({
                "id": cid,
                "title": cfg["title"],
                "order": cfg["order"],
                "badge": cfg.get("badge", "Chat"),
                "color": cfg.get("color", "#3b82f6"),
                "turns_count": len(chat_turns),
                "total_steps": len(steps),
                "start_dt": c_start,
                "end_dt": c_end,
                "start_fmt": format_dt(c_start),
                "end_fmt": format_dt(c_end),
                "wall_clock_sec": (c_end - c_start).total_seconds(),
                "active_work_sec": active_sec,
                "idle_sec": max(0.0, (c_end - c_start).total_seconds() - active_sec),
                "active_duration": format_duration(active_sec),
                "idle_duration": format_duration(max(0.0, (c_end - c_start).total_seconds() - active_sec)),
                "wall_duration": format_duration((c_end - c_start).total_seconds()),
                "active_pct": round((active_sec / ((c_end - c_start).total_seconds() or 1)) * 100, 1)
            })
            all_turns.extend(chat_turns)

    all_turns.sort(key=lambda t: t["start_dt"])

    timeline_items = []
    gaps_list = []

    for idx, turn in enumerate(all_turns):
        if idx > 0:
            prev_turn = all_turns[idx - 1]
            gap_start = prev_turn["end_dt"]
            gap_end = turn["start_dt"]
            gap_sec = (gap_end - gap_start).total_seconds()

            if gap_sec >= 10:
                is_cross_chat = (prev_turn["chat_id"] != turn["chat_id"])
                
                if gap_sec >= 4 * 3600:
                    gap_type = "major_break"
                    gap_category = "sleep"
                    gap_title = "Sleep & Rest Period"
                    is_prompting = False
                elif gap_sec >= 5400:
                    gap_type = "short_break"
                    gap_category = "break"
                    gap_title = "Work Pause / Extended Break"
                    is_prompting = False
                elif gap_sec >= 1800:
                    gap_type = "prompting_deep"
                    gap_category = "prompting"
                    gap_title = "Deep Prompting, Tech Spec & Architecture Analysis"
                    is_prompting = True
                elif gap_sec >= 60:
                    gap_type = "prompting"
                    gap_category = "prompting"
                    gap_title = "Prompt Engineering & In-Browser Playtesting" if not is_cross_chat else "Context Transition & Prompting"
                    is_prompting = True
                else:
                    gap_type = "micro_gap"
                    gap_category = "prompting"
                    gap_title = "Instant Iteration / Fast Prompt"
                    is_prompting = True

                gap_item = {
                    "kind": "gap",
                    "gap_id": f"gap_{idx}",
                    "chat_id": turn["chat_id"],
                    "from_chat_id": prev_turn["chat_id"],
                    "from_chat": prev_turn["chat_title"],
                    "to_chat": turn["chat_title"],
                    "is_cross_chat": is_cross_chat,
                    "gap_type": gap_type,
                    "gap_category": gap_category,
                    "is_prompting": is_prompting,
                    "gap_title": gap_title,
                    "start_dt": gap_start,
                    "end_dt": gap_end,
                    "start_fmt": format_dt(gap_start),
                    "end_fmt": format_dt(gap_end),
                    "duration_sec": gap_sec,
                    "duration_fmt": format_duration(gap_sec)
                }
                timeline_items.append(gap_item)
                gaps_list.append(gap_item)

        timeline_items.append({
            "kind": "turn",
            "turn_id": turn["turn_id"],
            "chat_id": turn["chat_id"],
            "chat_title": turn["chat_title"],
            "chat_order": turn["chat_order"],
            "badge": turn["badge"],
            "color": turn["color"],
            "turn_index": turn["turn_index"],
            "start_dt": turn["start_dt"],
            "end_dt": turn["end_dt"],
            "start_fmt": format_dt(turn["start_dt"]),
            "end_fmt": format_dt(turn["end_dt"]),
            "time_span_fmt": f"{format_time_only(turn['start_dt'])} — {format_time_only(turn['end_dt'])}",
            "duration_sec": turn["duration_sec"],
            "duration_fmt": turn["duration_fmt"],
            "user_prompt": turn["user_prompt"],
            "user_prompt_en": turn.get("user_prompt_en", turn["user_prompt"]),
            "user_prompt_ru": turn.get("user_prompt_ru", turn["user_prompt"]),
            "user_prompt_preview": turn["user_prompt_preview"],
            "skills_count": len(turn.get("skills_used", [])),
            "skills_sample": turn.get("skills_used", []),
            "tools_count": len(turn["tool_calls"]),
            "tools_sample": list(dict.fromkeys(turn["tool_calls"]))[:6],
            "files_modified": turn["files_modified"]
        })

    first_dt_local = all_turns[0]["start_dt"].astimezone(LOCAL_TZ) if all_turns else None
    last_dt_local = all_turns[-1]["end_dt"].astimezone(LOCAL_TZ) if all_turns else None

    if first_dt_local and last_dt_local:
        start_hour_floor = first_dt_local.replace(minute=0, second=0, microsecond=0)
        end_hour_ceil = (last_dt_local + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    else:
        start_hour_floor = datetime(2026, 8, 18, 22, 0, 0, tzinfo=LOCAL_TZ)
        end_hour_ceil = datetime(2026, 8, 22, 5, 0, 0, tzinfo=LOCAL_TZ)

    tot_wall_sec = (all_turns[-1]["end_dt"] - all_turns[0]["start_dt"]).total_seconds() if all_turns else 0.0
    tot_ai_sec = sum(t["duration_sec"] for t in all_turns)
    tot_prompting_sec = sum(g["duration_sec"] for g in gaps_list if g.get("is_prompting"))
    tot_breaks_sec = sum(g["duration_sec"] for g in gaps_list if not g.get("is_prompting"))
    tot_cowork_sec = tot_ai_sec + tot_prompting_sec

    stats = {
        "total_chats": len(chat_summaries),
        "total_turns": len(all_turns),
        "total_gaps": len(gaps_list),
        "first_event": format_dt(all_turns[0]["start_dt"]) if all_turns else "",
        "last_event": format_dt(all_turns[-1]["end_dt"]) if all_turns else "",
        "wall_clock_sec": tot_wall_sec,
        "wall_clock_fmt": format_duration(tot_wall_sec),
        "active_work_sec": tot_ai_sec,
        "active_work_fmt": format_duration(tot_ai_sec),
        "prompting_sec": tot_prompting_sec,
        "prompting_fmt": format_duration(tot_prompting_sec),
        "cowork_sec": tot_cowork_sec,
        "cowork_fmt": format_duration(tot_cowork_sec),
        "breaks_sec": tot_breaks_sec,
        "breaks_fmt": format_duration(tot_breaks_sec),
        "idle_sec": tot_breaks_sec,
        "idle_fmt": format_duration(tot_breaks_sec),
        "ai_density_pct": round((tot_ai_sec / (tot_wall_sec or 1)) * 100, 1),
        "cowork_density_pct": round((tot_cowork_sec / (tot_wall_sec or 1)) * 100, 1),
        "density_pct": round((tot_cowork_sec / (tot_wall_sec or 1)) * 100, 1)
    }

    raw_turns_for_candles = [
        {
            "turn_id": t["turn_id"],
            "chat_order": t["chat_order"],
            "chat_title": t["chat_title"],
            "color": t["color"],
            "start_ts": int(t["start_dt"].timestamp() * 1000),
            "end_ts": int(t["end_dt"].timestamp() * 1000),
            "duration_sec": t["duration_sec"],
            "duration_fmt": t["duration_fmt"],
            "prompt_preview": t["user_prompt_preview"]
        }
        for t in all_turns
    ]

    return {
        "stats": stats,
        "chats": chat_summaries,
        "turns": all_turns,
        "raw_turns_for_candles": raw_turns_for_candles,
        "project_start_ts": int(start_hour_floor.astimezone(timezone.utc).timestamp() * 1000),
        "project_end_ts": int(end_hour_ceil.astimezone(timezone.utc).timestamp() * 1000),
        "gaps": gaps_list,
        "timeline_items": timeline_items
    }

def generate_html_dashboard(data, output_path="timeline_viewer.html"):
    skills_docs = load_skills_docs()
    
    app_data = {
        "stats": data["stats"],
        "skills_docs": skills_docs,
        "project_start_ts": data["project_start_ts"],
        "project_end_ts": data["project_end_ts"],
        "raw_turns": data["raw_turns_for_candles"],
        "chats": [
            {
                "id": c["id"],
                "title": c["title"],
                "order": c["order"],
                "badge": c["badge"],
                "color": c["color"],
                "turns_count": c["turns_count"],
                "total_steps": c["total_steps"],
                "start_fmt": c["start_fmt"],
                "end_fmt": c["end_fmt"],
                "wall_duration": c["wall_duration"],
                "active_duration": c["active_duration"],
                "idle_duration": c["idle_duration"],
                "active_pct": c["active_pct"]
            }
            for c in data["chats"]
        ],
        "timeline": [
            {
                k: v for k, v in item.items() if not isinstance(v, datetime)
            }
            for item in data["timeline_items"]
        ]
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Softgames — Operation Close Win: AI Development Timeline & Chrono-Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-base: #090c12;
      --bg-surface: #101522;
      --bg-card: #151c2e;
      --bg-card-hover: #1b243b;
      --border-subtle: #212c42;
      --border-active: #3b82f6;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-blue: #3b82f6;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-purple: #8b5cf6;
      --accent-pink: #ec4899;
      --accent-cyan: #06b6d4;
      --gap-major-bg: rgba(239, 68, 68, 0.08);
      --gap-major-border: rgba(239, 68, 68, 0.25);
      --gap-short-bg: rgba(245, 158, 11, 0.08);
      --gap-short-border: rgba(245, 158, 11, 0.25);
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg-base);
      color: var(--text-primary);
      font-family: var(--font-sans);
      line-height: 1.5;
      padding: 32px 24px;
      min-height: 100vh;
    }}
    .container {{ max-width: 1360px; margin: 0 auto; }}
    header {{
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .header-title h1 {{
      font-size: 28px;
      font-weight: 800;
      background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }}
    .header-title p {{ color: var(--text-secondary); font-size: 14px; }}
    .header-links {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .nav-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 9999px;
      font-size: 12px;
      font-family: var(--font-mono);
      color: #93c5fd;
      text-decoration: none;
      transition: all 0.2s ease;
    }}
    .nav-btn:hover {{
      background: rgba(59, 130, 246, 0.25);
      border-color: #60a5fa;
      color: #fff;
      transform: translateY(-1px);
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 30px;
    }}
    .kpi-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(255, 255, 255, 0.15);
    }}
    .kpi-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}
    .kpi-value {{
      font-size: 26px;
      font-weight: 800;
      font-family: var(--font-mono);
      margin-bottom: 4px;
    }}
    .kpi-value.active-time {{ color: #10b981; }}
    .kpi-value.cowork-time {{ color: #38bdf8; }}
    .kpi-value.prompt-time {{ color: #c084fc; }}
    .kpi-value.wall-time {{ color: #60a5fa; }}
    .kpi-value.idle-time {{ color: #f59e0b; }}
    .kpi-value.turns-count {{ color: #e2e8f0; }}
    .kpi-subtext {{
      font-size: 11px;
      color: var(--text-muted);
    }}

    /* TRADING CHART / CANDLESTICK GRID */
    .hourly-graph-section {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 30px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }}
    .trading-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .trading-title-group {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .trading-badge {{
      font-size: 11px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
    }}
    .trading-res-info {{
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 600;
    }}
    .timeframe-selector {{
      display: flex;
      align-items: center;
      gap: 4px;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 3px;
    }}
    .tf-label {{
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      margin-left: 6px;
      margin-right: 4px;
      text-transform: uppercase;
    }}
    .tf-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-secondary);
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .tf-btn:hover {{
      color: var(--text-primary);
      background: rgba(255, 255, 255, 0.06);
    }}
    .tf-btn.active {{
      background: var(--accent-blue);
      color: #fff;
      border-color: var(--accent-blue);
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }}

    .days-banner-track {{
      display: flex;
      width: 100%;
      height: 24px;
      align-items: center;
      margin-bottom: 6px;
      position: relative;
    }}
    .day-banner-item {{
      font-size: 10.5px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: #94a3b8;
      border-left: 1px solid rgba(255, 255, 255, 0.2);
      padding-left: 6px;
      height: 100%;
      display: flex;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 2px 2px 0 0;
    }}

    .hourly-graph-wrapper {{
      width: 100%;
      overflow-x: auto;
      padding-bottom: 4px;
    }}
    .hourly-grid {{
      display: flex;
      gap: 3px;
      width: 100%;
      height: 140px;
      align-items: flex-end;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      position: relative;
    }}
    .hour-column {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 160px;
      position: relative;
      cursor: pointer;
      min-width: 0;
      padding: 0 1px;
    }}
    .hour-column.day-boundary {{
      border-left: 1px dashed rgba(255, 255, 255, 0.2);
      padding-left: 2px;
    }}
    .hour-top-slot {{
      height: 20px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 4px;
    }}
    .hour-bar-track {{
      width: 100%;
      height: 105px;
      background: rgba(255, 255, 255, 0.025);
      border: 1px solid rgba(255, 255, 255, 0.04);
      border-radius: 4px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
      position: relative;
      transition: all 0.15s ease;
    }}
    .hour-column:hover .hour-bar-track {{
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(56, 189, 248, 0.5);
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
      transform: scaleY(1.02);
    }}
    .hour-bar-fill {{
      width: 100%;
      transition: height 0.25s ease;
      position: relative;
    }}
    .hour-bar-segments {{
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
    }}
    .hour-micro-segment {{
      width: 100%;
    }}
    .hour-bottom-slot {{
      height: 22px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 4px;
    }}
    .hour-time-label {{
      font-size: 8.5px;
      font-family: var(--font-mono);
      color: var(--text-muted);
      white-space: nowrap;
      text-align: center;
      line-height: 1;
    }}
    .hour-time-label.is-highlight {{
      color: #94a3b8;
      font-weight: 700;
    }}
    .hour-tick {{
      width: 2px;
      height: 5px;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 1px;
    }}
    .hour-mins-badge {{
      font-size: 8.5px;
      font-family: var(--font-mono);
      color: #10b981;
      font-weight: 700;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.25);
      padding: 1px 3px;
      border-radius: 3px;
      white-space: nowrap;
      line-height: 1;
    }}

    .session-cards-section {{
      margin-bottom: 24px;
    }}
    .chats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }}
    .chat-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 14px 16px;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
      overflow: hidden;
    }}
    .chat-card:hover {{
      border-color: var(--c-accent, var(--border-active));
      transform: translateY(-2px);
      background: var(--bg-card);
    }}
    .chat-card.active {{
      border-color: var(--c-accent, var(--border-active));
      background: rgba(59, 130, 246, 0.08);
      box-shadow: 0 0 16px rgba(59, 130, 246, 0.15);
    }}
    .chat-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .chat-order-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: var(--c-accent, #3b82f6);
      color: #fff;
      font-size: 11px;
      font-weight: 800;
      font-family: var(--font-mono);
    }}
    .chat-badge-tag {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.04);
      padding: 2px 8px;
      border-radius: 9999px;
    }}
    .chat-card-title {{
      font-size: 13px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 10px;
      line-height: 1.4;
    }}
    .chat-card-stats {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-secondary);
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding-top: 8px;
    }}
    .c-stat-item strong {{
      color: var(--text-primary);
      font-family: var(--font-mono);
    }}

    .controls-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 24px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 12px 18px;
    }}
    .filter-group {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .filter-btn {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .filter-btn:hover {{
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-primary);
    }}
    .filter-btn.active {{
      background: var(--accent-blue);
      border-color: var(--accent-blue);
      color: #fff;
    }}
    .search-input {{
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      padding: 7px 14px;
      border-radius: 6px;
      font-size: 12px;
      width: 280px;
      outline: none;
    }}
    .search-input:focus {{
      border-color: var(--accent-blue);
    }}

    .timeline-container {{
      position: relative;
      padding-left: 36px;
    }}
    .timeline-container::before {{
      content: '';
      position: absolute;
      left: 12px;
      top: 0;
      bottom: 0;
      width: 2px;
      background: rgba(255, 255, 255, 0.08);
    }}
    .timeline-node {{
      position: relative;
      margin-bottom: 24px;
    }}
    .node-dot {{
      position: absolute;
      left: -30px;
      top: 18px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: var(--bg-base);
      border: 3px solid var(--node-color, var(--accent-blue));
      z-index: 2;
    }}
    .turn-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 18px 20px;
      transition: all 0.2s ease;
    }}
    .turn-card:hover {{
      border-color: var(--node-color, var(--border-active));
      background: var(--bg-card);
    }}
    .turn-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .turn-badge-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .turn-chat-pill {{
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-primary);
      border-left: 3px solid var(--node-color, var(--accent-blue));
    }}
    .turn-duration-pill {{
      font-size: 11px;
      font-family: var(--font-mono);
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(16, 185, 129, 0.12);
      color: #6ee7b7;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }}
    .turn-time {{
      font-size: 12px;
      font-family: var(--font-mono);
      color: var(--text-muted);
    }}
    
    .prompt-box {{
      background: rgba(0, 0, 0, 0.25);
      border-radius: 8px;
      border-left: 3px solid var(--node-color, var(--accent-blue));
      padding: 12px 14px;
      margin-bottom: 12px;
    }}
    .prompt-header-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      padding-bottom: 6px;
    }}
    .prompt-tag {{
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}
    .prompt-lang-toggle {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #94a3b8;
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 4px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s ease;
    }}
    .prompt-lang-toggle:hover {{
      background: rgba(255, 255, 255, 0.12);
      color: #f8fafc;
      border-color: rgba(255, 255, 255, 0.25);
    }}
    .prompt-lang-toggle.active {{
      background: rgba(59, 130, 246, 0.2);
      color: #93c5fd;
      border-color: #3b82f6;
    }}
    .turn-prompt {{
      font-size: 13.5px;
      font-weight: 500;
      color: var(--text-primary);
      line-height: 1.55;
      white-space: pre-wrap;
    }}
    .turn-prompt.is-russian {{
      color: #e2e8f0;
      font-style: italic;
    }}

    .turn-tools {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.04);
    }}
    .skill-chip {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      font-family: var(--font-mono);
      font-weight: 700;
      background: rgba(168, 85, 247, 0.15);
      color: #c084fc;
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid rgba(168, 85, 247, 0.35);
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }}
    .skill-chip:hover {{
      background: rgba(168, 85, 247, 0.25);
      border-color: rgba(168, 85, 247, 0.6);
      color: #e9d5ff;
      transform: translateY(-1px);
      box-shadow: 0 0 8px rgba(168, 85, 247, 0.3);
    }}
    .tool-chip {{
      font-size: 11px;
      font-family: var(--font-mono);
      background: rgba(59, 130, 246, 0.1);
      color: #93c5fd;
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid rgba(59, 130, 246, 0.2);
    }}
    .file-chip {{
      font-size: 11px;
      font-family: var(--font-mono);
      background: rgba(236, 72, 153, 0.1);
      color: #f472b6;
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid rgba(236, 72, 153, 0.2);
    }}

    .gap-node {{
      position: relative;
      margin: 16px 0 24px 0;
    }}
    .gap-line {{
      position: absolute;
      left: -30px;
      top: 50%;
      transform: translateY(-50%);
      width: 14px;
      height: 2px;
      background: rgba(255, 255, 255, 0.2);
    }}
    .gap-card {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 18px;
      border-radius: 8px;
      font-size: 12px;
      border-left: 3px solid;
    }}
    .gap-card.major_break {{
      background: var(--gap-major-bg);
      border: 1px solid var(--gap-major-border);
      border-left-color: #ef4444;
    }}
    .gap-card.short_break {{
      background: var(--gap-short-bg);
      border: 1px solid var(--gap-short-border);
      border-left-color: #f59e0b;
    }}
    .gap-card.prompting_deep {{
      background: rgba(168, 85, 247, 0.08);
      border: 1px solid rgba(168, 85, 247, 0.25);
      border-left-color: #c084fc;
    }}
    .gap-card.prompting {{
      background: rgba(16, 185, 129, 0.06);
      border: 1px solid rgba(16, 185, 129, 0.2);
      border-left-color: #10b981;
    }}
    .gap-card.micro_gap {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-left-color: var(--text-muted);
    }}
    .gap-info {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .gap-icon {{
      font-size: 16px;
    }}
    .gap-title {{
      font-weight: 600;
      color: var(--text-primary);
    }}
    .gap-meta {{
      color: var(--text-muted);
      font-size: 11px;
    }}
    .gap-duration {{
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 13px;
      color: #f87171;
    }}
    .gap-card.short_break .gap-duration {{
      color: #fbbf24;
    }}
    .gap-card.prompting_deep .gap-duration {{
      color: #c084fc;
    }}
    .gap-card.prompting .gap-duration {{
      color: #34d399;
    }}
    .gap-card.micro_gap .gap-duration {{
      color: var(--text-secondary);
    }}
    .empty-state {{
      text-align: center;
      padding: 48px 24px;
      color: var(--text-muted);
      background: var(--bg-surface);
      border-radius: 12px;
      border: 1px dashed var(--border-subtle);
    }}

    /* SKILL MODAL POPUP */
    .skill-modal-backdrop {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .skill-modal-dialog {{
      background: var(--bg-surface);
      border: 1px solid rgba(168, 85, 247, 0.4);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 24px rgba(168, 85, 247, 0.2);
      border-radius: 14px;
      width: 100%;
      max-width: 860px;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: modalFadeIn 0.2s ease-out;
    }}
    @keyframes modalFadeIn {{
      from {{ opacity: 0; transform: scale(0.96); }}
      to {{ opacity: 1; transform: scale(1); }}
    }}
    .skill-modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 22px;
      background: rgba(168, 85, 247, 0.08);
      border-bottom: 1px solid var(--border-subtle);
    }}
    .skill-modal-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 16px;
      font-weight: 800;
      color: #f8fafc;
      font-family: var(--font-mono);
    }}
    .skill-modal-close {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #94a3b8;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }}
    .skill-modal-close:hover {{
      background: #ef4444;
      border-color: #ef4444;
      color: #fff;
    }}
    .skill-modal-body {{
      padding: 22px 26px;
      overflow-y: auto;
      font-size: 13.5px;
      line-height: 1.65;
      color: #cbd5e1;
      font-family: var(--font-sans);
    }}
    .skill-modal-body h1, .skill-modal-body h2, .skill-modal-body h3 {{
      color: #f8fafc;
      margin-top: 18px;
      margin-bottom: 10px;
    }}
    .skill-modal-body pre {{
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 12px 14px;
      overflow-x: auto;
      margin: 12px 0;
      font-family: var(--font-mono);
      font-size: 12px;
      color: #38bdf8;
    }}
    .skill-modal-body code {{
      font-family: var(--font-mono);
      background: rgba(0, 0, 0, 0.35);
      color: #f472b6;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
    }}
    .skill-modal-body ul, .skill-modal-body ol {{
      margin-left: 20px;
      margin-bottom: 12px;
    }}
    .skill-modal-body li {{
      margin-bottom: 4px;
    }}
    .skill-modal-body table {{
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0;
      font-size: 12.5px;
    }}
    .skill-modal-body th, .skill-modal-body td {{
      padding: 8px 12px;
      border: 1px solid var(--border-subtle);
      text-align: left;
    }}
    .skill-modal-body th {{
      background: rgba(255, 255, 255, 0.04);
      color: #93c5fd;
      font-weight: 700;
    }}

    .timeline-tooltip {{
      position: fixed;
      background: var(--bg-card);
      border: 1px solid var(--border-active);
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 12px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      pointer-events: none;
      z-index: 100;
      display: none;
      max-width: 340px;
    }}
    .tt-header {{ font-weight: 700; color: #fff; margin-bottom: 4px; }}
    .tt-row {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 2px; }}
    .tt-muted {{ color: var(--text-muted); }}

    @media (max-width: 768px) {{
      body {{ padding: 16px; }}
      .chats-grid {{ grid-template-columns: 1fr; }}
      .timeline-container {{ padding-left: 24px; }}
      .node-dot {{ left: -24px; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <header>
    <div class="header-title">
      <h1>📊 AI Development Timeline & Chrono-Engine</h1>
      <p>Project: <strong>Softgames — Operation Close Win</strong> (Hourly Density Grid & Bilingual Prompt Roadmap)</p>
    </div>
    <div class="header-links">
      <a href="https://thegod322.github.io/softgames-closewin/" target="_blank" class="nav-btn">🎮 Playable Prototype & Tuner</a>
      <a href="https://github.com/Thegod322/guapiko-timeline-viewer/tree/main/transcripts" target="_blank" class="nav-btn">📜 Raw Transcripts</a>
      <a href="https://github.com/Thegod322/softgames-closewin" target="_blank" class="nav-btn">📦 Source Code</a>
    </div>
  </header>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Total Project Span (Wall-Clock)</div>
      <div class="kpi-value wall-time">{data['stats']['wall_clock_fmt']}</div>
      <div class="kpi-subtext">{data['stats']['first_event']} ➔ {data['stats']['last_event']}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Combined Active Co-Work</div>
      <div class="kpi-value cowork-time">{data['stats']['cowork_fmt']}</div>
      <div class="kpi-subtext">{data['stats']['cowork_density_pct']}% density (AI Execution + Operator Prompting)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Active AI Execution</div>
      <div class="kpi-value active-time">{data['stats']['active_work_fmt']}</div>
      <div class="kpi-subtext">{data['stats']['ai_density_pct']}% net AI model generation & tool work</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Operator Prompting & Analysis (&lt;1.5h)</div>
      <div class="kpi-value prompt-time">{data['stats']['prompting_fmt']}</div>
      <div class="kpi-subtext">Active prompt drafting, specs & in-browser testing</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Offline Breaks &amp; Sleep (≥1.5h)</div>
      <div class="kpi-value idle-time">{data['stats']['breaks_fmt']}</div>
      <div class="kpi-subtext">Rest periods, sleep &amp; offline intervals</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Dialogue Iterations</div>
      <div class="kpi-value turns-count">{data['stats']['total_turns']}</div>
      <div class="kpi-subtext">Across {data['stats']['total_chats']} development sessions</div>
    </div>
  </div>

  <!-- TRADING CHART DENSITY ROADMAP SECTION -->
  <div class="hourly-graph-section">
    <div class="trading-header">
      <div class="trading-title-group">
        <span class="trading-badge">📈 DENSITY ROADMAP</span>
        <span class="trading-res-info" id="tradingResInfo">Trading Chart: <strong>2H Resolution (Auto-Fit)</strong></span>
      </div>
      <div class="timeframe-selector">
        <span class="tf-label">Timeframe:</span>
        <button class="tf-btn" id="tf-btn-1" onclick="setTimeframe(1)">1H</button>
        <button class="tf-btn active" id="tf-btn-2" onclick="setTimeframe(2)">2H</button>
        <button class="tf-btn" id="tf-btn-4" onclick="setTimeframe(4)">4H</button>
        <button class="tf-btn" id="tf-btn-24" onclick="setTimeframe(24)">1D</button>
        <button class="tf-btn" id="tf-btn-fit" onclick="setTimeframe('fit')">⚡ 100% Fit</button>
      </div>
    </div>

    <div class="days-banner-track" id="daysBanner"></div>

    <div class="hourly-graph-wrapper">
      <div class="hourly-grid" id="hourlyGrid"></div>
    </div>
  </div>

  <div class="session-cards-section">
    <div class="section-title">
      <span>📂 Development Sessions (Click card to filter):</span>
    </div>
    <div class="chats-grid" id="chatsGrid"></div>
  </div>

  <div class="controls-bar">
    <div class="filter-group">
      <button class="filter-btn active" onclick="setFilter('all')">All Events ({len(data['timeline_items'])})</button>
      <button class="filter-btn" onclick="setFilter('turns')">AI Active Work ({data['stats']['total_turns']})</button>
      <button class="filter-btn" onclick="setFilter('prompting')">Prompting &amp; Analysis (&lt;1.5h) ({len([i for i in data['timeline_items'] if i['kind'] == 'gap' and i.get('is_prompting')])})</button>
      <button class="filter-btn" onclick="setFilter('breaks')">Breaks &amp; Sleep (≥1.5h) ({len([i for i in data['timeline_items'] if i['kind'] == 'gap' and not i.get('is_prompting')])})</button>
    </div>
    <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search prompts (EN/RU), skills, tools, files..." oninput="handleSearch(this.value)">
  </div>

  <div class="timeline-container" id="timelineList"></div>
</div>

<!-- SKILL MODAL DIALOG -->
<div class="skill-modal-backdrop" id="skillModalBackdrop" onclick="handleModalBackdropClick(event)">
  <div class="skill-modal-dialog">
    <div class="skill-modal-header">
      <div class="skill-modal-title" id="skillModalTitle">
        <span class="skill-modal-icon" id="skillModalIcon">🎯</span>
        <span id="skillModalName">Skill Specification</span>
      </div>
      <button class="skill-modal-close" onclick="closeSkillModal()" title="Close (Esc)">✕</button>
    </div>
    <div class="skill-modal-body" id="skillModalBody"></div>
  </div>
</div>

<div class="timeline-tooltip" id="tooltip"></div>

<script>
  const DATA = {json.dumps(app_data, ensure_ascii=False)};
  let currentFilter = 'all';
  let activeChatFilter = null;
  let searchQuery = '';
  let currentTimeframe = 2; // Default 2 hours candle
  let currentBins = [];
  const promptLangs = {{}}; // turn_id -> 'en' | 'ru'

  const tooltip = document.getElementById('tooltip');

  function setTimeframe(tf) {{
    currentTimeframe = tf;
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`tf-btn-${{tf}}`);
    if (btn) btn.classList.add('active');

    renderTradingGrid();
  }}

  function renderTradingGrid() {{
    const grid = document.getElementById('hourlyGrid');
    const daysBanner = document.getElementById('daysBanner');
    const resInfo = document.getElementById('tradingResInfo');

    let resHours = (currentTimeframe === 'fit') ? 2 : Number(currentTimeframe);
    let isFitMode = (currentTimeframe === 'fit' || resHours >= 2);

    const tStart = DATA.project_start_ts;
    const tEnd = DATA.project_end_ts;
    const binMs = resHours * 3600 * 1000;
    const totalBinsCount = Math.ceil((tEnd - tStart) / binMs);

    resInfo.innerHTML = `Trading Chart: <strong>${{currentTimeframe === 'fit' ? '100% Fit Screen' : (resHours === 24 ? '1D Daily Candles' : `${{resHours}}H Candles`)}}</strong> • ${{totalBinsCount}} Bars`;

    currentBins = [];
    let daySpans = [];
    let curDay = '';
    let curDayBinCount = 0;

    for (let i = 0; i < totalBinsCount; i++) {{
      const bStart = tStart + i * binMs;
      const bEnd = bStart + binMs;
      const dStart = new Date(bStart);
      const dEnd = new Date(bEnd);

      const dayStr = dStart.toLocaleDateString('en-GB', {{ day: '2-digit', month: 'short' }});
      if (dayStr !== curDay) {{
        if (curDay) {{
          daySpans.push({{ label: curDay, bins: curDayBinCount }});
        }}
        curDay = dayStr;
        curDayBinCount = 1;
      }} else {{
        curDayBinCount++;
      }}

      // Find overlapping turns
      let activeWorkSec = 0;
      let segments = [];

      DATA.raw_turns.forEach(turn => {{
        const overlapStart = Math.max(bStart, turn.start_ts);
        const overlapEnd = Math.min(bEnd, turn.end_ts);
        if (overlapStart < overlapEnd) {{
          const dur = (overlapEnd - overlapStart) / 1000;
          activeWorkSec += dur;
          segments.push({{
            turn_id: turn.turn_id,
            chat_order: turn.chat_order,
            chat_title: turn.chat_title,
            color: turn.color,
            duration_sec: dur,
            duration_fmt: formatDuration(dur),
            prompt_preview: turn.prompt_preview
          }});
        }}
      }});

      const totalBinSec = resHours * 3600;
      const idleSec = Math.max(0, totalBinSec - activeWorkSec);

      let timeLabel = '';
      if (resHours === 24) {{
        timeLabel = dayStr;
      }} else if (resHours >= 4) {{
        timeLabel = dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
      }} else {{
        // Show time label on even hours or if enough space
        timeLabel = dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
      }}

      currentBins.push({{
        index: i,
        start_ts: bStart,
        end_ts: bEnd,
        day_label: dayStr,
        time_label: timeLabel,
        range_str: `${{dayStr}} ${{dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }})}} — ${{dEnd.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }})}}`,
        active_sec: activeWorkSec,
        active_mins: Math.round((activeWorkSec / 60) * 10) / 10,
        idle_mins: Math.round((idleSec / 60) * 10) / 10,
        density_pct: Math.round((activeWorkSec / totalBinSec) * 1000) / 10,
        segments: segments,
        is_active: activeWorkSec > 0
      }});
    }}

    if (curDayBinCount > 0) {{
      daySpans.push({{ label: curDay, bins: curDayBinCount }});
    }}

    // Render Days Banner
    daysBanner.innerHTML = daySpans.map(ds => `
      <div class="day-banner-item" style="flex: ${{ds.bins}};">
        📅 ${{ds.label}} (${{ds.bins * resHours}}h)
      </div>
    `).join('');

    // Render Candles Grid
    let lastDay = '';
    grid.innerHTML = currentBins.map((bin, i) => {{
      const isDayBoundary = (bin.day_label !== lastDay);
      if (isDayBoundary) lastDay = bin.day_label;

      const dStart = new Date(bin.start_ts);
      const hourNum = dStart.getHours();
      let timeLabelHtml = '';
      
      if (resHours === 24) {{
        timeLabelHtml = `<span class=\"hour-time-label is-highlight\">${{bin.day_label}}</span>`;
      }} else if (resHours >= 4) {{
        timeLabelHtml = `<span class=\"hour-time-label\">${{dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }})}}</span>`;
      }} else if (resHours === 2) {{
        if (hourNum % 4 === 0 || isDayBoundary) {{
          timeLabelHtml = `<span class=\"hour-time-label ${{isDayBoundary ? 'is-highlight' : ''}}\">${{dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }})}}</span>`;
        }} else {{
          timeLabelHtml = `<span class=\"hour-tick\"></span>`;
        }}
      }} else {{
        if (hourNum % 6 === 0 || isDayBoundary) {{
          timeLabelHtml = `<span class=\"hour-time-label ${{isDayBoundary ? 'is-highlight' : ''}}\">${{dStart.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }})}}</span>`;
        }} else {{
          timeLabelHtml = `<span class=\"hour-tick\"></span>`;
        }}
      }}

      const fillPct = bin.active_sec > 0 
        ? Math.max(14, Math.min(100, Math.round((bin.active_sec / (resHours * 3600)) * 100))) 
        : 0;

      const segsHtml = bin.segments.map(seg => `
        <div class=\"hour-micro-segment\" 
             style=\"background: ${{seg.color}}; height: ${{Math.max(15, Math.round((seg.duration_sec / (bin.active_sec || 1)) * 100))}}%;\">
        </div>
      `).join('');

      const badgeHtml = bin.active_mins > 0 
        ? `<span class=\"hour-mins-badge\">${{bin.active_mins >= 60 ? (Math.round(bin.active_mins / 6) / 10 + 'h') : (bin.active_mins + 'm')}}</span>`
        : '';

      return `
        <div class=\"hour-column ${{bin.is_active ? 'is-active' : ''}} ${{isDayBoundary ? 'day-boundary' : ''}}\"
             onmouseenter=\"showTradingTooltip(event, ${{i}})\"
             onmousemove=\"moveTooltip(event)\"
             onmouseleave=\"hideTooltip()\"
             onclick=\"handleTradingCandleClick(${{i}})\">
          <div class=\"hour-top-slot\">
            ${{badgeHtml}}
          </div>
          <div class=\"hour-bar-track\">
            <div class=\"hour-bar-fill\" style=\"height: ${{fillPct}}%;\">
              <div class=\"hour-bar-segments\">
                ${{segsHtml}}
              </div>
            </div>
          </div>
          <div class=\"hour-bottom-slot\">
            ${{timeLabelHtml}}
          </div>
        </div>
      `;
    }}).join('');
  }}

  function showTradingTooltip(e, idx) {{
    const bin = currentBins[idx];
    if (!bin) return;

    let segsInfo = '';
    if (bin.segments.length > 0) {{
      segsInfo = '<div style="margin-top:8px; border-top:1px solid #334155; padding-top:6px;">' +
        bin.segments.map(s => `
          <div style="font-size:11px; margin-bottom:4px;">
            <strong style="color:${{s.color}};">${{s.chat_title.split(':')[0]}}:</strong> ${{s.duration_fmt}}
            <div class="tt-muted" style="font-size:10px;">💬 "${{escapeHtml(s.prompt_preview.substring(0, 75))}}..."</div>
          </div>
        `).join('') + '</div>';
    }}

    tooltip.innerHTML = `
      <div class="tt-header">📅 ${{bin.range_str}}</div>
      <div class="tt-row"><span class="tt-muted">Active Work:</span> <strong style="color:#10b981;">${{bin.active_mins}} mins (${{bin.density_pct}}%)</strong></div>
      <div class="tt-row"><span class="tt-muted">Pause / Sleep:</span> <strong>${{bin.idle_mins}} mins</strong></div>
      <div class="tt-row"><span class="tt-muted">Dialogue Turns:</span> <strong>${{bin.segments.length}} iterations</strong></div>
      ${{segsInfo}}
      ${{bin.segments.length > 0 ? '<div style="margin-top:6px; font-size:10.5px; color:#38bdf8; font-weight:700;">👉 Click candle to jump to dialogue turn</div>' : ''}}
    `;
    tooltip.style.display = 'block';
    moveTooltip(e);
  }}

  function moveTooltip(e) {{
    const x = e.clientX + 16;
    const y = e.clientY + 16;
    tooltip.style.left = Math.min(window.innerWidth - 360, x) + 'px';
    tooltip.style.top = Math.min(window.innerHeight - 220, y) + 'px';
  }}

  function hideTooltip() {{ tooltip.style.display = 'none'; }}

  function handleTradingCandleClick(idx) {{
    const bin = currentBins[idx];
    if (bin && bin.segments.length > 0) {{
      const firstTurnId = bin.segments[0].turn_id;
      const el = document.getElementById(firstTurnId);
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        el.querySelector('.turn-card').style.borderColor = '#38bdf8';
        setTimeout(() => {{ el.querySelector('.turn-card').style.borderColor = ''; }}, 2500);
      }}
    }}
  }}

  function formatDuration(sec) {{
    if (sec < 60) return Math.round(sec) + 's';
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    if (m < 60) return s > 0 ? `${{m}}m ${{s}}s` : `${{m}}m`;
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return `${{h}}h ${{rm}}m`;
  }}

  function renderChatsGrid() {{
    const grid = document.getElementById('chatsGrid');
    grid.innerHTML = DATA.chats.map(c => `
      <div class="chat-card ${{activeChatFilter === c.id ? 'active' : ''}}" 
           style="--c-accent: ${{c.color}};" 
           onclick="toggleChatFilter('${{c.id}}')">
        <div class="chat-card-header">
          <span class="chat-order-badge">${{c.order}}</span>
          <span class="chat-badge-tag">${{c.badge}}</span>
        </div>
        <div class="chat-card-title">${{c.title}}</div>
        <div class="chat-card-stats">
          <div class="c-stat-item">
            <span>Active</span>
            <strong>${{c.active_duration}}</strong>
          </div>
          <div class="c-stat-item">
            <span>Gaps</span>
            <strong>${{c.idle_duration}}</strong>
          </div>
          <div class="c-stat-item">
            <span>Turns</span>
            <strong>${{c.turns_count}}</strong>
          </div>
        </div>
      </div>
    `).join('');
  }}

  function renderTimeline() {{
    const list = document.getElementById('timelineList');
    
    const filtered = DATA.timeline.filter(item => {{
      if (activeChatFilter) {{
        if (item.kind === 'turn') {{
          if (item.chat_id !== activeChatFilter) return false;
        }} else if (item.kind === 'gap') {{
          if (item.is_cross_chat) return false;
          if (item.chat_id !== activeChatFilter && item.from_chat_id !== activeChatFilter) return false;
        }}
      }}

      if (currentFilter === 'turns' && item.kind !== 'turn') return false;
      if (currentFilter === 'prompting' && (item.kind !== 'gap' || !item.is_prompting)) return false;
      if (currentFilter === 'breaks' && (item.kind !== 'gap' || item.is_prompting)) return false;

      if (searchQuery) {{
        const q = searchQuery.toLowerCase();
        if (item.kind === 'turn') {{
          const matchEn = item.user_prompt_en && item.user_prompt_en.toLowerCase().includes(q);
          const matchRu = item.user_prompt_ru && item.user_prompt_ru.toLowerCase().includes(q);
          const matchTools = item.tools_sample && item.tools_sample.some(t => t.toLowerCase().includes(q));
          const matchFiles = item.files_modified && item.files_modified.some(f => f.toLowerCase().includes(q));
          const matchSkills = item.skills_sample && item.skills_sample.some(s => (s.label || s.name || '').toLowerCase().includes(q));
          if (!matchEn && !matchRu && !matchTools && !matchFiles && !matchSkills) return false;
        }} else if (item.kind === 'gap') {{
          const matchTitle = item.gap_title && item.gap_title.toLowerCase().includes(q);
          if (!matchTitle) return false;
        }}
      }}

      return true;
    }});

    if (filtered.length === 0) {{
      list.innerHTML = `<div class="empty-state">No timeline events match the selected filters.</div>`;
      return;
    }}

    list.innerHTML = filtered.map(item => {{
      if (item.kind === 'turn') {{
        const skillsHtml = item.skills_sample && item.skills_sample.length > 0
          ? item.skills_sample.map(s => `<span class="skill-chip" onclick="openSkillModal('${{s.name}}')" title="Click to inspect skill specification">${{escapeHtml(s.icon || '🎯')}} ${{escapeHtml(s.label || s.name)}}</span>`).join('')
          : '';
        const toolsHtml = item.tools_sample && item.tools_sample.length > 0
          ? item.tools_sample.map(t => `<span class="tool-chip">⚙️ ${{t}}</span>`).join('')
          : '';
        const filesHtml = item.files_modified && item.files_modified.length > 0
          ? item.files_modified.map(f => `<span class="file-chip">📄 ${{f}}</span>`).join('')
          : '';

        const isRu = (promptLangs[item.turn_id] === 'ru');
        const displayedPrompt = isRu ? (item.user_prompt_ru || item.user_prompt) : (item.user_prompt_en || item.user_prompt);

        return `
          <div class="timeline-node" id="${{item.turn_id}}">
            <div class="node-dot" style="--node-color: ${{item.color}};"></div>
            <div class="turn-card" style="--node-color: ${{item.color}};">
              <div class="turn-meta">
                <div class="turn-badge-group">
                  <span class="turn-chat-pill" style="--node-color: ${{item.color}};">${{item.chat_title}} • Turn #${{item.turn_index}}</span>
                  <span class="turn-duration-pill">⚡ ${{item.duration_fmt}} active work</span>
                </div>
                <span class="turn-time">📅 ${{item.start_fmt}} (time span: ${{item.time_span_fmt}})</span>
              </div>
              
              <div class="prompt-box">
                <div class="prompt-header-row">
                  <span class="prompt-tag">💬 User Prompt</span>
                  <button class="prompt-lang-toggle ${{isRu ? 'active' : ''}}" id="btn-toggle-${{item.turn_id}}" onclick="togglePromptLang('${{item.turn_id}}', event)">
                    ${{isRu ? '<span class="toggle-icon">🇺🇸</span> <span class="toggle-label">EN Translation</span>' : '<span class="toggle-icon">🌐</span> <span class="toggle-label">RU Original</span>'}}
                  </button>
                </div>
                <div class="turn-prompt ${{isRu ? 'is-russian' : ''}}" id="prompt-${{item.turn_id}}">${{escapeHtml(displayedPrompt)}}</div>
              </div>

              ${{skillsHtml || toolsHtml || filesHtml ? `
                <div class="turn-tools">
                  ${{skillsHtml}}
                  ${{toolsHtml}}
                  ${{filesHtml}}
                </div>
              ` : ''}}
            </div>
          </div>
        `;
      }} else if (item.kind === 'gap') {{
        let icon = '⏱️';
        if (item.gap_type === 'major_break') icon = '🌙';
        else if (item.gap_type === 'short_break') icon = '☕';
        else if (item.gap_type === 'prompting_deep') icon = '🧠';
        else if (item.gap_type === 'prompting') icon = '✍️';
        else if (item.gap_type === 'micro_gap') icon = '⚡';

        return `
          <div class="gap-node">
            <div class="gap-line"></div>
            <div class="gap-card ${{item.gap_type}}">
              <div class="gap-info">
                <span class="gap-icon">${{icon}}</span>
                <div>
                  <div class="gap-title">${{item.gap_title}} ${{item.is_cross_chat ? `(Transition: ${{item.from_chat.split(':')[0]}} ➔ ${{item.to_chat.split(':')[0]}})` : ''}}</div>
                  <div class="gap-meta">${{item.start_fmt}} ➔ ${{item.end_fmt}}</div>
                </div>
              </div>
              <div class="gap-duration">${{item.duration_fmt}}</div>
            </div>
          </div>
        `;
      }}
    }}).join('');
  }}

  function togglePromptLang(turnId, e) {{
    if (e) e.stopPropagation();
    const item = DATA.timeline.find(t => t.turn_id === turnId);
    if (!item) return;

    const cur = promptLangs[turnId] || 'en';
    const next = cur === 'en' ? 'ru' : 'en';
    promptLangs[turnId] = next;

    const textEl = document.getElementById(`prompt-${{turnId}}`);
    const btnEl = document.getElementById(`btn-toggle-${{turnId}}`);
    if (textEl) {{
      textEl.textContent = next === 'ru' ? (item.user_prompt_ru || item.user_prompt) : (item.user_prompt_en || item.user_prompt);
      textEl.classList.toggle('is-russian', next === 'ru');
    }}
    if (btnEl) {{
      btnEl.innerHTML = next === 'ru'
        ? '<span class="toggle-icon">🇺🇸</span> <span class="toggle-label">EN Translation</span>'
        : '<span class="toggle-icon">🌐</span> <span class="toggle-label">RU Original</span>';
      btnEl.classList.toggle('active', next === 'ru');
    }}
  }}

  function openSkillModal(skillName) {{
    const doc = (DATA.skills_docs && DATA.skills_docs[skillName]) || (`# ${{skillName}}\\n\\nSkill specification for ${{skillName}}.`);
    const icon = (skillName === 'softgames-closewin' ? '🎯' : (skillName === 'guapiko-decompose-to-tasks' ? '🧩' : (skillName === 'guapiko-timeline-tracker' ? '⏱️' : '⚡')));
    
    document.getElementById('skillModalIcon').textContent = icon;
    document.getElementById('skillModalName').textContent = `/${{skillName}} (Skill Documentation)`;
    document.getElementById('skillModalBody').innerHTML = renderSimpleMarkdown(doc);
    document.getElementById('skillModalBackdrop').style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }}

  function closeSkillModal() {{
    document.getElementById('skillModalBackdrop').style.display = 'none';
    document.body.style.overflow = '';
  }}

  function handleModalBackdropClick(e) {{
    if (e.target.id === 'skillModalBackdrop') {{
      closeSkillModal();
    }}
  }}

  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') {{
      closeSkillModal();
    }}
  }});

  function renderSimpleMarkdown(md) {{
    if (!md) return '';
    const lines = md.split('\\n');
    let html = '';
    let inCode = false;
    let codeContent = '';
    
    for (let i = 0; i < lines.length; i++) {{
      let line = lines[i];
      if (line.startsWith('```')) {{
        if (!inCode) {{
          inCode = true;
          codeContent = '';
        }} else {{
          inCode = false;
          html += '<pre><code>' + escapeHtml(codeContent.trim()) + '</code></pre>';
        }}
        continue;
      }}
      
      if (inCode) {{
        codeContent += line + '\\n';
        continue;
      }}
      
      let escaped = escapeHtml(line);
      
      // Bold formatting
      escaped = escaped.split('**').map((part, idx) => idx % 2 === 1 ? '<strong style=\"color:#f1f5f9;\">' + part + '</strong>' : part).join('');
      // Code formatting
      escaped = escaped.split('`').map((part, idx) => idx % 2 === 1 ? '<code style=\"font-family:monospace; background:rgba(0,0,0,0.4); color:#f472b6; padding:2px 6px; border-radius:4px; font-size:12px;\">' + part + '</code>' : part).join('');
      
      if (line.startsWith('### ')) {{
        html += '<h3 style=\"font-size:15px; font-weight:700; color:#93c5fd; margin:16px 0 6px 0; border-bottom:1px solid #1e293b; padding-bottom:4px;\">' + escaped.substring(4) + '</h3>';
      }} else if (line.startsWith('## ')) {{
        html += '<h2 style=\"font-size:17px; font-weight:800; color:#38bdf8; margin:20px 0 8px 0; border-bottom:1px solid #334155; padding-bottom:6px;\">' + escaped.substring(3) + '</h2>';
      }} else if (line.startsWith('# ')) {{
        html += '<h1 style=\"font-size:20px; font-weight:800; color:#f8fafc; margin:22px 0 10px 0;\">' + escaped.substring(2) + '</h1>';
      }} else if (line.trim().startsWith('- ')) {{
        html += '<li style=\"margin-left:20px; margin-bottom:4px;\">' + escaped.replace(/^\\s*-\\s+/, '') + '</li>';
      }} else if (line.trim() === '') {{
        html += '<div style=\"height:10px;\"></div>';
      }} else {{
        html += '<p style=\"margin-bottom:8px;\">' + escaped + '</p>';
      }}
    }}
    return html;
  }}

  function escapeHtml(text) {{
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }}

  function setFilter(f) {{
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderTimeline();
  }}

  function toggleChatFilter(chatId) {{
    if (activeChatFilter === chatId) {{
      activeChatFilter = null;
    }} else {{
      activeChatFilter = chatId;
    }}
    renderChatsGrid();
    renderTimeline();

    if (activeChatFilter) {{
      const firstTurn = DATA.timeline.find(t => t.kind === 'turn' && t.chat_id === activeChatFilter);
      if (firstTurn) {{
        const el = document.getElementById(firstTurn.turn_id);
        if (el) {{
          el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          el.querySelector('.turn-card').style.borderColor = '#38bdf8';
          setTimeout(() => {{ el.querySelector('.turn-card').style.borderColor = ''; }}, 2000);
        }}
      }}
    }}
  }}

  function handleSearch(val) {{
    searchQuery = val.trim();
    renderTimeline();
  }}

  renderTradingGrid();
  renderChatsGrid();
  renderTimeline();
</script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Interactive HTML Dashboard updated: {output_path}")

    brain_viewer_path = f"{BRAIN_DIR}/{CURRENT_CONV_ID}/timeline_viewer.html"
    if os.path.exists(os.path.dirname(brain_viewer_path)):
        try:
            with open(brain_viewer_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✓ Also synchronized to Brain: {brain_viewer_path}")
        except Exception:
            pass

def print_summary(data):
    stats = data["stats"]
    print("=" * 82)
    print(" 🚀 GUAPIKOCLAW — DEVELOPMENT TIMELINE & CHRONO-TRACKER")
    print("=" * 82)
    print(f" ⏱️ Total Project Span (Wall-Clock) : {stats['wall_clock_fmt']} ({stats['first_event']} ➔ {stats['last_event']})")
    print(f" 🔥 Combined Active Co-Work         : {stats['cowork_fmt']} ({stats['cowork_density_pct']}% total density)")
    print(f" ⚡ Net Active AI Execution        : {stats['active_work_fmt']} ({stats['ai_density_pct']}% AI density)")
    print(f" ✍️ Operator Prompting & Analysis  : {stats['prompting_fmt']} (Active intervals < 1.5h)")
    print(f" 🌙 Offline Breaks & Sleep (≥ 1.5h)  : {stats['breaks_fmt']}")
    print(f" 💬 Dialogue Iterations (Turns)     : {stats['total_turns']} across {stats['total_chats']} sessions")
    print("-" * 82)
    print(" 📂 DEVELOPMENT SESSIONS:")
    for c in data["chats"]:
        print(f"   [{c['order']}] {c['title']}")
        print(f"       Span: {c['start_fmt']} ➔ {c['end_fmt']} (Total: {c['wall_duration']})")
        print(f"       Active AI: {c['active_duration']} | Gaps: {c['idle_duration']} | Turns: {c['turns_count']}")
    print("=" * 82)

def print_chat_detail(data, order_num):
    target = next((c for c in data["chats"] if c["order"] == order_num), None)
    if not target:
        print(f"Chat number {order_num} not found. Available: 1..{len(data['chats'])}")
        return
    print("=" * 82)
    print(f" 📂 DETAILED LOG: {target['title']}")
    print(f" ID: {target['id']} | Total steps in log: {target['total_steps']}")
    print("=" * 82)
    chat_turns = [t for t in data["turns"] if t["chat_order"] == order_num]
    for t in chat_turns:
        print(f" 💬 Turn #{t['turn_index']} [{format_time_only(t['start_dt'])} — {format_time_only(t['end_dt'])}] (⚡ {t['duration_fmt']}):")
        print(f"    Prompt (EN): \"{t['user_prompt'][:120]}...\"")
        if t.get("skills_used"):
            skills_unique = [f"{s.get('icon', '🎯')} {s.get('label', s.get('name'))}" for s in t["skills_used"]]
            print(f"    Skills: {', '.join(skills_unique)}")
        if t["tool_calls"]:
            tools_unique = list(dict.fromkeys(t["tool_calls"]))[:4]
            print(f"    Tools: {', '.join(tools_unique)}")
        if t["files_modified"]:
            print(f"    Files: {', '.join(t['files_modified'])}")
        print("-" * 82)

def main():
    parser = argparse.ArgumentParser(description="GuapikoClaw Universal Timeline Analyzer & Chrono-Engine")
    parser.add_argument("--chats", "--ids", type=str, help="List of session IDs separated by comma")
    parser.add_argument("--chat", type=int, help="Show detailed log for a specific chat order")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--no-html", action="store_true", help="Do not regenerate HTML file")
    parser.add_argument("--output-html", type=str, default="timeline_viewer.html", help="Path for HTML output")

    args = parser.parse_args()

    configs = load_saved_chats(CONFIG_FILE)
    data = process_timeline(configs)

    if args.json:
        def serialize_helper(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        print(json.dumps(data, indent=2, ensure_ascii=False, default=serialize_helper))
        return

    if not args.no_html:
        generate_html_dashboard(data, args.output_html)

    if args.chat:
        print_chat_detail(data, args.chat)
    else:
        print_summary(data)

if __name__ == "__main__":
    main()
