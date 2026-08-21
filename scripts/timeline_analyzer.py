#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GuapikoClaw Universal Timeline Analyzer & Chrono-Engine
------------------------------------------------------
Универсальный инструмент для AI-агентов и оператора:
- Анализирует сессии разработки и транскрипты
- Фильтрует по ключевым словам проекта, датам, количеству сессий или списку ID
- Вычисляет чистое рабочее время (Active Work) и паузы (Gaps)
- Строит 44+ часовую сетку плотности
- Генерирует интерактивный HTML-дашборд с мгновенным поиском

Примеры запуска:
  python scripts/timeline_analyzer.py                      # Базовый запуск (все сохраненные чаты)
  python scripts/timeline_analyzer.py --project softgames  # Поиск сессий по ключевому слову
  python scripts/timeline_analyzer.py --since 2026-08-19   # Фильтр по дате от 19 августа
  python scripts/timeline_analyzer.py --days 2             # За последние 2 дня
  python scripts/timeline_analyzer.py --recent 5           # Последние 5 активных сессий
  python scripts/timeline_analyzer.py --chats id1,id2      # Конкретные ID через запятую
  python scripts/timeline_analyzer.py --hourly             # Почасовая сетка активности
  python scripts/timeline_analyzer.py --gaps               # Список пауз и перерывов
  python scripts/timeline_analyzer.py --chat 2             # Детальный лог сессии #2
  python scripts/timeline_analyzer.py --add <id> "<title>" # Добавить чат в реестр
  python scripts/timeline_analyzer.py --json               # Чистый JSON для агентов
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
CURRENT_CONV_ID = "2ab178e2-f484-44bf-b57b-a0bb30c90f78"
PALETTE = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f43f5e", "#84cc16", "#a855f7"]

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
        return f"{int(seconds)} сек"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins < 60:
        return f"{mins} мин {secs} сек" if secs > 0 else f"{mins} мин"
    hours = int(mins // 60)
    rem_mins = mins % 60
    return f"{hours} ч {rem_mins} мин"

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
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)
    print(f"✓ Чат {chat_id} успешно сохранен в {config_path}")

def discover_chats_in_brain(brain_dir=BRAIN_DIR, project_kw=None, since_dt=None, until_dt=None, limit=None):
    if not os.path.exists(brain_dir):
        return []
    
    dirs = [d for d in os.listdir(brain_dir) if d != "tempmediaStorage" and os.path.isdir(os.path.join(brain_dir, d))]
    discovered = []
    
    for d in dirs:
        t_path = os.path.join(brain_dir, d, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(t_path):
            continue
        
        mtime = os.path.getmtime(t_path)
        m_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        
        if since_dt and m_dt < since_dt:
            continue
        if until_dt and m_dt > until_dt:
            continue
        
        first_prompt = ""
        user_msg_count = 0
        total_steps = 0
        all_text = ""
        
        try:
            with open(t_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        total_steps += 1
                        step = json.loads(line)
                        if step.get("type") == "USER_INPUT":
                            user_msg_count += 1
                            raw_cnt = step.get("content", "")
                            clean_c = re.sub(r"<.*?>", "", raw_cnt, flags=re.DOTALL).strip()
                            all_text += " " + clean_c
                            if not first_prompt:
                                first_prompt = clean_c
        except Exception:
            continue
        
        if total_steps == 0:
            continue
        
        if project_kw:
            kw_clean = project_kw.lower()
            if kw_clean not in all_text.lower() and kw_clean not in d.lower():
                continue
        
        discovered.append({
            "id": d,
            "mtime": mtime,
            "m_dt": m_dt,
            "first_prompt": first_prompt[:120],
            "total_steps": total_steps,
            "user_msg_count": user_msg_count
        })
    
    discovered.sort(key=lambda x: x["mtime"])
    
    if limit and len(discovered) > limit:
        discovered = discovered[-limit:]
        
    return discovered

def build_chat_configs(args):
    if args.chats:
        chat_ids = [c.strip() for c in args.chats.split(",") if c.strip()]
        configs = []
        for idx, cid in enumerate(chat_ids):
            configs.append({
                "id": cid,
                "title": f"Chat {idx+1}: {cid[:8]}",
                "order": idx + 1,
                "badge": "Explicit ID",
                "color": PALETTE[idx % len(PALETTE)]
            })
        return configs
    
    if args.project or args.since or args.until or args.days or args.recent:
        since_dt = None
        if args.since:
            since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
        elif args.days:
            since_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
        
        until_dt = None
        if args.until:
            until_dt = (datetime.strptime(args.until, "%Y-%m-%d") + timedelta(days=1)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
        
        discovered = discover_chats_in_brain(
            brain_dir=BRAIN_DIR,
            project_kw=args.project,
            since_dt=since_dt,
            until_dt=until_dt,
            limit=args.recent
        )
        
        if not discovered:
            print(f"⚠️ Чаты по заданным критериям (project='{args.project}', since='{args.since}') не найдены.")
            return []
        
        configs = []
        for idx, disc in enumerate(discovered):
            badge = "Discovered"
            if args.project: badge = f"{args.project.capitalize()}"
            title_text = disc["first_prompt"][:40] if disc["first_prompt"] else f"Session {disc['id'][:8]}"
            configs.append({
                "id": disc["id"],
                "title": f"Chat {idx+1}: {title_text}",
                "order": idx + 1,
                "badge": badge,
                "color": PALETTE[idx % len(PALETTE)]
            })
        return configs
    
    saved = load_saved_chats(CONFIG_FILE)
    return saved

def process_timeline(chat_configs, brain_dir=BRAIN_DIR):
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

                current_turn = {
                    "chat_id": cid,
                    "chat_title": cfg["title"],
                    "chat_order": cfg["order"],
                    "badge": cfg.get("badge", "Chat"),
                    "color": cfg.get("color", "#3b82f6"),
                    "turn_index": len(chat_turns) + 1,
                    "user_step_index": step.get("step_index", i),
                    "start_dt": dt,
                    "end_dt": dt,
                    "duration_sec": 1.0,
                    "duration_fmt": "1 сек",
                    "user_prompt": clean_content,
                    "user_prompt_preview": clean_content[:180] + ("..." if len(clean_content) > 180 else ""),
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
                "idle_sec": max(0.0, (c_end - c_start).total_seconds() - active_sec)
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
                if gap_sec > 1800:
                    gap_type = "major_break"
                    gap_title = "Длительный перерыв / Пауза в работе"
                elif gap_sec > 300:
                    gap_type = "short_break"
                    gap_title = "Перерыв / Тестирование в браузере"
                else:
                    gap_type = "micro_gap"
                    gap_title = "Микро-пауза / Осмысление и ввод"

                gap_item = {
                    "kind": "gap",
                    "gap_type": gap_type,
                    "gap_title": gap_title,
                    "is_cross_chat": is_cross_chat,
                    "chat_id": prev_turn["chat_id"] if not is_cross_chat else None,
                    "from_chat_id": prev_turn["chat_id"],
                    "to_chat_id": turn["chat_id"],
                    "from_chat": prev_turn["chat_title"],
                    "to_chat": turn["chat_title"],
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
            "turn_id": f"turn_{turn['chat_order']}_{turn['turn_index']}",
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
            "user_prompt_preview": turn["user_prompt_preview"],
            "tools_count": len(turn["tool_calls"]),
            "tools_sample": list(dict.fromkeys(turn["tool_calls"]))[:6],
            "files_modified": turn["files_modified"]
        })

    first_dt_local = all_turns[0]["start_dt"].astimezone(LOCAL_TZ) if all_turns else None
    last_dt_local = all_turns[-1]["end_dt"].astimezone(LOCAL_TZ) if all_turns else None

    if first_dt_local and last_dt_local:
        start_hour_floor = first_dt_local.replace(minute=0, second=0, microsecond=0)
        end_hour_ceil = (last_dt_local + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        total_hours = max(1, int((end_hour_ceil - start_hour_floor).total_seconds() // 3600))
    else:
        start_hour_floor = datetime(2026, 8, 18, 22, 0, 0, tzinfo=LOCAL_TZ)
        total_hours = 45

    hourly_bins = []
    for h_idx in range(total_hours):
        bin_start = start_hour_floor + timedelta(hours=h_idx)
        bin_end = bin_start + timedelta(hours=1)
        bin_start_utc = bin_start.astimezone(timezone.utc)
        bin_end_utc = bin_end.astimezone(timezone.utc)

        active_segs = []
        tot_active = 0.0

        for turn in all_turns:
            overlap_start = max(bin_start_utc, turn["start_dt"])
            overlap_end = min(bin_end_utc, turn["end_dt"])
            if overlap_start < overlap_end:
                dur = (overlap_end - overlap_start).total_seconds()
                tot_active += dur
                active_segs.append({
                    "turn_id": f"turn_{turn['chat_order']}_{turn['turn_index']}",
                    "chat_order": turn["chat_order"],
                    "chat_title": turn["chat_title"],
                    "color": turn["color"],
                    "duration_sec": dur,
                    "duration_fmt": format_duration(dur),
                    "prompt_preview": turn["user_prompt_preview"]
                })

        active_mins = round(tot_active / 60.0, 1)
        idle_mins = round(60.0 - active_mins, 1)

        hourly_bins.append({
            "hour_index": h_idx,
            "day_label": bin_start.strftime("%d.%m (%a)"),
            "hour_label": bin_start.strftime("%H:00"),
            "time_range": f"{bin_start.strftime('%d.%m %H:00')} — {bin_end.strftime('%H:00')}",
            "active_seconds": tot_active,
            "active_minutes": active_mins,
            "idle_minutes": idle_mins,
            "is_active": len(active_segs) > 0,
            "segments": active_segs
        })

    first_overall_dt = all_turns[0]["start_dt"] if all_turns else None
    last_overall_dt = all_turns[-1]["end_dt"] if all_turns else None
    total_wall_sec = (last_overall_dt - first_overall_dt).total_seconds() if (first_overall_dt and last_overall_dt) else 0
    total_active_sec = sum(t["duration_sec"] for t in all_turns)
    total_gaps_sec = sum(item["duration_sec"] for item in timeline_items if item["kind"] == "gap")

    stats = {
        "first_event": format_dt(first_overall_dt),
        "last_event": format_dt(last_overall_dt),
        "total_wall_time": format_duration(total_wall_sec),
        "total_active_work": format_duration(total_active_sec),
        "total_gap_time": format_duration(total_gaps_sec),
        "total_turns": len(all_turns),
        "total_chats": len(chat_summaries),
        "hours_count": total_hours,
        "active_ratio_pct": round((total_active_sec / (total_wall_sec or 1)) * 100, 1) if total_wall_sec > 0 else 0
    }

    return {
        "stats": stats,
        "chats": chat_summaries,
        "hourly_bins": hourly_bins,
        "gaps": gaps_list,
        "turns": all_turns,
        "timeline_items": timeline_items
    }

def generate_html_viewer(data, output_path="timeline_viewer.html"):
    app_data = {
        "stats": data["stats"],
        "hourly_bins": data["hourly_bins"],
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
                "wall_duration": format_duration(c["wall_clock_sec"]),
                "active_duration": format_duration(c["active_work_sec"]),
                "idle_duration": format_duration(c["idle_sec"]),
                "active_pct": round((c["active_work_sec"] / (c["wall_clock_sec"] or 1)) * 100, 1)
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

    total_hours_span = len(data["hourly_bins"])

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GuapikoClaw — Хронометраж и График разработки</title>
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
    .header-tag {{
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
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: var(--card-accent, var(--accent-blue));
    }}
    .kpi-label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}
    .kpi-value {{
      font-size: 24px;
      font-weight: 800;
      color: var(--text-primary);
      font-family: var(--font-mono);
      margin-bottom: 4px;
    }}
    .kpi-subtext {{ font-size: 12px; color: var(--text-secondary); }}
    .chart-section {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 34px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
    .section-header-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .section-title {{
      font-size: 17px;
      font-weight: 800;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .chart-legend {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-secondary); font-weight: 600; }}
    .legend-dot {{ width: 10px; height: 10px; border-radius: 3px; }}
    .hourly-graph-wrapper {{ overflow-x: auto; padding-bottom: 12px; }}
    .hourly-grid {{
      display: grid;
      grid-template-columns: repeat({total_hours_span}, minmax(42px, 1fr));
      gap: 3px;
      min-width: 1100px;
      background: rgba(0,0,0,0.3);
      padding: 12px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.05);
    }}
    .hour-column {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      padding: 6px 2px;
      border-radius: 6px;
      transition: all 0.15s ease;
      position: relative;
    }}
    .hour-column:hover {{ background: rgba(255,255,255,0.06); transform: translateY(-2px); }}
    .hour-column.day-boundary {{ border-left: 2px dashed rgba(255,255,255,0.2); padding-left: 5px; }}
    .hour-bar-track {{
      width: 100%;
      height: 110px;
      background: rgba(255,255,255,0.03);
      border-radius: 4px;
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.04);
    }}
    .hour-bar-fill {{
      width: 100%;
      background: var(--hour-accent, var(--accent-blue));
      border-radius: 3px 3px 0 0;
      transition: height 0.3s ease;
      min-height: 0;
      position: relative;
    }}
    .hour-bar-segments {{
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      display: flex; flex-direction: column-reverse;
    }}
    .hour-micro-segment {{ width: 100%; transition: opacity 0.2s; }}
    .hour-time-label {{ font-size: 10px; font-family: var(--font-mono); font-weight: 700; color: var(--text-muted); }}
    .hour-column.is-active .hour-time-label {{ color: var(--text-primary); }}
    .hour-day-label {{ font-size: 9px; font-weight: 800; text-transform: uppercase; color: #60a5fa; margin-bottom: 2px; }}
    .hour-mins-badge {{
      font-size: 9px; font-family: var(--font-mono); font-weight: 700; color: #6ee7b7; background: rgba(16,185,129,0.15); padding: 1px 4px; border-radius: 3px;
    }}
    .timeline-tooltip {{
      position: fixed; display: none; background: #1e293b; border: 1px solid #334155; padding: 12px 16px; border-radius: 8px; font-size: 12px; color: #f8fafc; pointer-events: none; z-index: 1000; box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 320px;
    }}
    .tt-header {{ font-weight: 700; color: #60a5fa; margin-bottom: 4px; font-family: var(--font-mono); }}
    .tt-row {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 3px; }}
    .tt-muted {{ color: #94a3b8; }}
    .session-cards-section {{ margin-bottom: 32px; }}
    .chats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px; }}
    .chat-card {{
      background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.2s ease; position: relative;
    }}
    .chat-card:hover, .chat-card.active {{
      border-color: var(--c-accent); background: var(--bg-card); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }}
    .chat-card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    .chat-order-badge {{
      display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 6px; background: var(--c-accent); color: #000; font-weight: 800; font-size: 12px; font-family: var(--font-mono);
    }}
    .chat-badge-tag {{
      font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.06); color: var(--text-secondary); border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .chat-card-title {{ font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; line-height: 1.4; }}
    .chat-card-stats {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px; background: rgba(0,0,0,0.25); padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);
    }}
    .c-stat-item span {{ display: block; color: var(--text-muted); font-size: 10px; text-transform: uppercase; }}
    .c-stat-item strong {{ color: var(--text-primary); font-family: var(--font-mono); font-size: 12px; }}
    .controls-bar {{
      background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px 20px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
    }}
    .filter-group {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .filter-btn {{
      padding: 6px 14px; border-radius: 8px; border: 1px solid var(--border-subtle); background: var(--bg-card); color: var(--text-secondary); font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease;
    }}
    .filter-btn:hover, .filter-btn.active {{ background: var(--accent-blue); border-color: var(--accent-blue); color: #fff; }}
    .search-input {{
      background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 7px 14px; color: var(--text-primary); font-size: 12px; font-family: var(--font-sans); width: 260px; outline: none;
    }}
    .search-input:focus {{ border-color: var(--accent-blue); }}
    .timeline-container {{ position: relative; padding-left: 36px; }}
    .timeline-container::before {{
      content: ''; position: absolute; top: 10px; bottom: 10px; left: 15px; width: 2px; background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%); opacity: 0.4;
    }}
    .timeline-node {{ position: relative; margin-bottom: 24px; scroll-margin-top: 100px; }}
    .node-dot {{
      position: absolute; left: -36px; top: 16px; width: 14px; height: 14px; border-radius: 50%; background: var(--node-color, var(--accent-blue)); border: 3px solid var(--bg-base); box-shadow: 0 0 10px var(--node-color, var(--accent-blue)); z-index: 2;
    }}
    .turn-card {{ background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 18px 20px; transition: all 0.15s ease; }}
    .turn-card:hover {{ border-color: rgba(255,255,255,0.15); background: var(--bg-card); }}
    .turn-meta {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }}
    .turn-badge-group {{ display: flex; align-items: center; gap: 8px; }}
    .turn-chat-pill {{
      font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.08); color: var(--text-primary); border-left: 3px solid var(--node-color, var(--accent-blue));
    }}
    .turn-duration-pill {{
      font-size: 11px; font-family: var(--font-mono); padding: 3px 8px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.2);
    }}
    .turn-time {{ font-size: 12px; font-family: var(--font-mono); color: var(--text-muted); }}
    .turn-prompt {{
      font-size: 14px; font-weight: 600; color: var(--text-primary); line-height: 1.5; margin-bottom: 12px; background: rgba(0, 0, 0, 0.2); padding: 12px 14px; border-radius: 8px; border-left: 3px solid var(--node-color, var(--accent-blue));
    }}
    .turn-tools {{
      display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.04);
    }}
    .tool-chip {{
      font-size: 11px; font-family: var(--font-mono); background: rgba(59, 130, 246, 0.1); color: #93c5fd; padding: 2px 7px; border-radius: 4px; border: 1px solid rgba(59, 130, 246, 0.2);
    }}
    .file-chip {{
      font-size: 11px; font-family: var(--font-mono); background: rgba(236, 72, 153, 0.1); color: #f472b6; padding: 2px 7px; border-radius: 4px; border: 1px solid rgba(236, 72, 153, 0.2);
    }}
    .gap-node {{ position: relative; margin: 16px 0 24px 0; }}
    .gap-line {{ position: absolute; left: -30px; top: 50%; transform: translateY(-50%); width: 14px; height: 2px; background: rgba(255,255,255,0.2); }}
    .gap-card {{
      display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; border-radius: 8px; font-size: 12px; border-left: 3px solid;
    }}
    .gap-card.major_break {{ background: var(--gap-major-bg); border: 1px solid var(--gap-major-border); border-left-color: #ef4444; }}
    .gap-card.short_break {{ background: var(--gap-short-bg); border: 1px solid var(--gap-short-border); border-left-color: #f59e0b; }}
    .gap-card.micro_gap {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-left-color: var(--text-muted); }}
    .gap-info {{ display: flex; align-items: center; gap: 10px; }}
    .gap-icon {{ font-size: 16px; }}
    .gap-title {{ font-weight: 600; color: var(--text-primary); }}
    .gap-meta {{ color: var(--text-muted); font-size: 11px; }}
    .gap-duration {{ font-family: var(--font-mono); font-weight: 700; font-size: 13px; color: #f87171; }}
    .gap-card.short_break .gap-duration {{ color: #fbbf24; }}
    .gap-card.micro_gap .gap-duration {{ color: var(--text-secondary); }}
    .empty-state {{
      text-align: center; padding: 48px 24px; color: var(--text-muted); background: var(--bg-surface); border-radius: 12px; border: 1px dashed var(--border-subtle);
    }}
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
      <h1>📊 График & Таймлайн разработки</h1>
      <p>Проект: <strong>GuapikoClaw / Softgames — Operation Close Win</strong> (Почасовая сетка и лог итераций)</p>
    </div>
    <div class="header-tag">
      ⏱️ {data['stats']['first_event']} ➔ {data['stats']['last_event']} • Почасовые слоты
    </div>
  </header>

  <div class="kpi-grid">
    <div class="kpi-card" style="--card-accent: #3b82f6;">
      <div class="kpi-label">Чистое рабочее время (Active)</div>
      <div class="kpi-value">{data['stats']['total_active_work']}</div>
      <div class="kpi-subtext">Промптинг, генерация кода, сборки, тесты</div>
    </div>
    <div class="kpi-card" style="--card-accent: #ef4444;">
      <div class="kpi-label">Время пауз / перерывов (Gaps)</div>
      <div class="kpi-value">{data['stats']['total_gap_time']}</div>
      <div class="kpi-subtext">Сон, отдых, ручные плейтесты между чатами</div>
    </div>
    <div class="kpi-card" style="--card-accent: #10b981;">
      <div class="kpi-label">Общий охват проекта (Wall-Clock)</div>
      <div class="kpi-value">{data['stats']['total_wall_time']}</div>
      <div class="kpi-subtext">Вся протяженность разработки</div>
    </div>
    <div class="kpi-card" style="--card-accent: #8b5cf6;">
      <div class="kpi-label">Итераций диалога (Turns)</div>
      <div class="kpi-value">{data['stats']['total_turns']}</div>
      <div class="kpi-subtext">В {data['stats']['total_chats']} сессиях</div>
    </div>
  </div>

  <div class="chart-section">
    <div class="section-header-row">
      <div class="section-title">
        <span>📈 Почасовой график активности ({total_hours_span} ч):</span>
      </div>
      <div class="chart-legend">
        {''.join([f'<div class="legend-item"><div class="legend-dot" style="background: {c["color"]};"></div> {c["title"].split(":")[0]}</div>' for c in data["chats"]])}
        <div class="legend-item"><div class="legend-dot" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);"></div> Паузы / Сон</div>
      </div>
    </div>

    <div class="hourly-graph-wrapper">
      <div class="hourly-grid" id="hourlyGrid"></div>
    </div>
  </div>

  <div class="session-cards-section">
    <div class="section-title">
      <span>📂 Сессии разработки (Нажмите на карточку для фильтрации):</span>
    </div>
    <div class="chats-grid" id="chatsGrid"></div>
  </div>

  <div class="controls-bar">
    <div class="filter-group">
      <button class="filter-btn active" onclick="setFilter('all')">Все события ({len(data['timeline_items'])})</button>
      <button class="filter-btn" onclick="setFilter('turns')">Только активная работа ({data['stats']['total_turns']})</button>
      <button class="filter-btn" onclick="setFilter('gaps')">Только паузы и гэпы ({len([i for i in data['timeline_items'] if i['kind'] == 'gap'])})</button>
      <button class="filter-btn" onclick="setFilter('major_gaps')">Длительные перерывы (>30 мин)</button>
    </div>
    <input type="text" id="searchInput" class="search-input" placeholder="🔍 Поиск по промптам, файлам..." oninput="handleSearch(this.value)">
  </div>

  <div class="timeline-container" id="timelineList"></div>
</div>

<div class="timeline-tooltip" id="tooltip"></div>

<script>
  const DATA = {json.dumps(app_data, ensure_ascii=False)};
  let currentFilter = 'all';
  let activeChatFilter = null;
  let searchQuery = '';

  const tooltip = document.getElementById('tooltip');

  function renderHourlyGrid() {{
    const grid = document.getElementById('hourlyGrid');
    let lastDay = '';

    grid.innerHTML = DATA.hourly_bins.map((bin, i) => {{
      const isDayBoundary = (bin.day_label !== lastDay);
      if (isDayBoundary) lastDay = bin.day_label;

      const fillPct = Math.min(100, Math.round((bin.active_minutes / 60.0) * 100));
      
      const segmentsHtml = bin.segments.map(seg => `
        <div class="hour-micro-segment" 
             style="background: ${{seg.color}}; height: ${{Math.max(12, Math.round((seg.duration_sec / (bin.active_seconds || 1)) * 100))}}%;">
        </div>
      `).join('');

      return `
        <div class="hour-column ${{bin.is_active ? 'is-active' : ''}} ${{isDayBoundary ? 'day-boundary' : ''}}"
             onmouseenter="showHourTooltip(event, ${{i}})"
             onmousemove="moveTooltip(event)"
             onmouseleave="hideTooltip()"
             onclick="handleHourClick(${{i}})">
          ${{isDayBoundary ? `<span class="hour-day-label">${{bin.day_label.split(' ')[0]}}</span>` : `<span class="hour-day-label" style="opacity:0;">.</span>`}}
          <div class="hour-bar-track">
            <div class="hour-bar-fill" style="height: ${{fillPct}}%;">
              <div class="hour-bar-segments">
                ${{segmentsHtml}}
              </div>
            </div>
          </div>
          <span class="hour-time-label">${{bin.hour_label}}</span>
          ${{bin.active_minutes > 0 ? `<span class="hour-mins-badge">${{bin.active_minutes}}м</span>` : ''}}
        </div>
      `;
    }}).join('');
  }}

  function showHourTooltip(e, idx) {{
    const bin = DATA.hourly_bins[idx];
    let segsInfo = '';
    if (bin.segments.length > 0) {{
      segsInfo = '<div style="margin-top:8px; border-top:1px solid #334155; padding-top:6px;">' +
        bin.segments.map(s => `
          <div style="font-size:11px; margin-bottom:4px;">
            <strong style="color:${{s.color}};">${{s.chat_title.split(':')[0]}}:</strong> ${{s.duration_fmt}}
            <div class="tt-muted" style="font-size:10px;">💬 "${{escapeHtml(s.prompt_preview.substring(0, 70))}}..."</div>
          </div>
        `).join('') + '</div>';
    }}

    tooltip.innerHTML = `
      <div class="tt-header">📅 ${{bin.time_range}}</div>
      <div class="tt-row"><span class="tt-muted">Активная работа:</span> <strong>${{bin.active_minutes}} мин</strong></div>
      <div class="tt-row"><span class="tt-muted">Пауза / Сон:</span> <strong>${{bin.idle_minutes}} мин</strong></div>
      ${{segsInfo}}
      ${{bin.segments.length > 0 ? '<div style="margin-top:6px; font-size:10px; color:#38bdf8;">👉 Нажмите для перехода к диалогу</div>' : ''}}
    `;
    tooltip.style.display = 'block';
    moveTooltip(e);
  }}

  function moveTooltip(e) {{
    const x = e.clientX + 16;
    const y = e.clientY + 16;
    tooltip.style.left = Math.min(window.innerWidth - 340, x) + 'px';
    tooltip.style.top = Math.min(window.innerHeight - 200, y) + 'px';
  }}

  function hideTooltip() {{ tooltip.style.display = 'none'; }}

  function handleHourClick(idx) {{
    const bin = DATA.hourly_bins[idx];
    if (bin.segments.length > 0) {{
      const firstTurnId = bin.segments[0].turn_id;
      const el = document.getElementById(firstTurnId);
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        el.querySelector('.turn-card').style.borderColor = '#38bdf8';
        setTimeout(() => {{ el.querySelector('.turn-card').style.borderColor = ''; }}, 2000);
      }}
    }}
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
            <span>Активно</span>
            <strong>${{c.active_duration}}</strong>
          </div>
          <div class="c-stat-item">
            <span>Паузы</span>
            <strong>${{c.idle_duration}}</strong>
          </div>
          <div class="c-stat-item">
            <span>Итераций</span>
            <strong>${{c.turns_count}}</strong>
          </div>
        </div>
      </div>
    `).join('');
  }}

  function renderTimeline() {{
    const list = document.getElementById('timelineList');
    
    const filtered = DATA.timeline.filter(item => {{
      // CRITICAL FIX: When filtering by chat, only show turns of this chat and internal gaps strictly belonging to this chat!
      if (activeChatFilter) {{
        if (item.kind === 'turn') {{
          if (item.chat_id !== activeChatFilter) return false;
        }} else if (item.kind === 'gap') {{
          // Strictly reject cross-chat gaps and gaps belonging to other chats
          if (item.is_cross_chat) return false;
          if (item.chat_id !== activeChatFilter && item.from_chat_id !== activeChatFilter) return false;
        }}
      }}

      if (currentFilter === 'turns' && item.kind !== 'turn') return false;
      if (currentFilter === 'gaps' && item.kind !== 'gap') return false;
      if (currentFilter === 'major_gaps') {{
        if (item.kind !== 'gap' || item.gap_type !== 'major_break') return false;
      }}

      if (searchQuery) {{
        const q = searchQuery.toLowerCase();
        if (item.kind === 'turn') {{
          const matchPrompt = item.user_prompt && item.user_prompt.toLowerCase().includes(q);
          const matchTools = item.tools_sample && item.tools_sample.some(t => t.toLowerCase().includes(q));
          const matchFiles = item.files_modified && item.files_modified.some(f => f.toLowerCase().includes(q));
          if (!matchPrompt && !matchTools && !matchFiles) return false;
        }} else if (item.kind === 'gap') {{
          const matchTitle = item.gap_title && item.gap_title.toLowerCase().includes(q);
          if (!matchTitle) return false;
        }}
      }}

      return true;
    }});

    if (filtered.length === 0) {{
      list.innerHTML = `<div class="empty-state">По выбранным фильтрам событий не найдено.</div>`;
      return;
    }}

    list.innerHTML = filtered.map(item => {{
      if (item.kind === 'turn') {{
        const toolsHtml = item.tools_sample && item.tools_sample.length > 0
          ? item.tools_sample.map(t => `<span class="tool-chip">⚙️ ${{t}}</span>`).join('')
          : '';
        const filesHtml = item.files_modified && item.files_modified.length > 0
          ? item.files_modified.map(f => `<span class="file-chip">📄 ${{f}}</span>`).join('')
          : '';

        return `
          <div class="timeline-node" id="${{item.turn_id}}">
            <div class="node-dot" style="--node-color: ${{item.color}};"></div>
            <div class="turn-card" style="--node-color: ${{item.color}};">
              <div class="turn-meta">
                <div class="turn-badge-group">
                  <span class="turn-chat-pill" style="--node-color: ${{item.color}};">${{item.chat_title}} • Итерация #${{item.turn_index}}</span>
                  <span class="turn-duration-pill">⚡ ${{item.duration_fmt}} активной работы</span>
                </div>
                <span class="turn-time">📅 ${{item.start_fmt}} (отрезок: ${{item.time_span_fmt}})</span>
              </div>
              <div class="turn-prompt">
                💬 "${{escapeHtml(item.user_prompt)}}"
              </div>
              ${{toolsHtml || filesHtml ? `
                <div class="turn-tools">
                  ${{toolsHtml}}
                  ${{filesHtml}}
                </div>
              ` : ''}}
            </div>
          </div>
        `;
      }} else if (item.kind === 'gap') {{
        const icon = item.gap_type === 'major_break' ? '⏸️' : (item.gap_type === 'short_break' ? '☕' : '⏱️');
        return `
          <div class="gap-node">
            <div class="gap-line"></div>
            <div class="gap-card ${{item.gap_type}}">
              <div class="gap-info">
                <span class="gap-icon">${{icon}}</span>
                <div>
                  <div class="gap-title">${{item.gap_title}} ${{item.is_cross_chat ? `(Переход: ${{item.from_chat.split(':')[0]}} ➔ ${{item.to_chat.split(':')[0]}})` : ''}}</div>
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

  function escapeHtml(text) {{
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }}

  function setFilter(f) {{
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderTimeline();
  }}

  function toggleChatFilter(id) {{
    if (activeChatFilter === id) {{ activeChatFilter = null; }}
    else {{ activeChatFilter = id; }}
    renderChatsGrid();
    renderTimeline();
  }}

  function handleSearch(val) {{
    searchQuery = val;
    renderTimeline();
  }}

  renderHourlyGrid();
  renderChatsGrid();
  renderTimeline();
</script>

</body>
</html>
"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Интерактивный HTML-дашборд обновлен: {output_path}")

    # Also save to current brain directory so browser tab refresh works immediately!
    brain_path = f"{BRAIN_DIR}/{CURRENT_CONV_ID}/timeline_viewer.html"
    if os.path.exists(os.path.dirname(brain_path)):
        try:
            with open(brain_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✓ Также синхронизировано в Brain: {brain_path}")
        except Exception:
            pass

def print_summary(data):
    s = data["stats"]
    print("=" * 82)
    print(" 🚀 GUAPIKOCLAW — ХРОНОМЕТРАЖ И ТАЙМЛАЙН РАЗРАБОТКИ")
    print("=" * 82)
    print(f" ⏱️ Общий охват проекта (Wall-Clock) : {s['total_wall_time']} ({s['first_event']} ➔ {s['last_event']})")
    print(f" ⚡ Чистое рабочее время (Active)    : {s['total_active_work']} ({s['active_ratio_pct']}% плотности)")
    print(f" ⏸️ Время пауз и перерывов (Gaps)    : {s['total_gap_time']}")
    print(f" 💬 Всего итераций диалога (Turns)   : {s['total_turns']} в {s['total_chats']} сессиях")
    print("-" * 82)
    print(" 📂 СЕССИИ РАЗРАБОТКИ:")
    for c in data["chats"]:
        print(f"   [{c['order']}] {c['title']}")
        print(f"       Отрезок: {c['start_fmt']} ➔ {c['end_fmt']} (Общее: {format_duration(c['wall_clock_sec'])})")
        print(f"       Активно: {format_duration(c['active_work_sec'])} | Паузы: {format_duration(c['idle_sec'])} | Итераций: {c['turns_count']}")
    print("=" * 82)

def print_hourly(data):
    print("=" * 82)
    print(f" 📈 ПОЧАСОВАЯ СЕТКА АКТИВНОСТИ ({data['stats']['hours_count']} ЧАСОВ)")
    print("=" * 82)
    print(f" {'Время (CEST)':<20} | {'Статус':<10} | {'Активно':<10} | {'Пауза':<10} | {'Сессия и действия'}")
    print("-" * 82)
    for b in data["hourly_bins"]:
        status = "⚡ РАБОТА" if b["is_active"] else "⏸️ Пауза"
        segs_desc = ""
        if b["segments"]:
            chats = list(dict.fromkeys([s["chat_title"].split(':')[0] for s in b["segments"]]))
            segs_desc = f"{', '.join(chats)}: {b['segments'][0]['prompt_preview'][:35]}..."
        print(f" {b['time_range']:<20} | {status:<10} | {b['active_minutes']:>4} мин   | {b['idle_minutes']:>4} мин   | {segs_desc}")
    print("=" * 82)

def print_gaps(data):
    print("=" * 82)
    print(" ⏸️ ВСЕ ПАУЗЫ И ПЕРЕРЫВЫ МЕЖДУ ИТЕРАЦИЯМИ")
    print("=" * 82)
    for g in data["gaps"]:
        icon = "🛌" if g["gap_type"] == "major_break" else ("☕" if g["gap_type"] == "short_break" else "⏱️")
        print(f" {icon} [{g['duration_fmt']:<12}] {g['start_fmt']} ➔ {g['end_fmt']}")
        print(f"    Тип: {g['gap_title']}")
        if g['is_cross_chat']:
            print(f"    Переход: {g['from_chat']} ➔ {g['to_chat']}")
        print("-" * 82)

def print_chat_detail(data, order_num):
    target = next((c for c in data["chats"] if c["order"] == order_num), None)
    if not target:
        print(f"Чат с номером {order_num} не найден. Доступны: 1..{len(data['chats'])}")
        return
    print("=" * 82)
    print(f" 📂 ДЕТАЛЬНЫЙ ЛОГ: {target['title']}")
    print(f" ID: {target['id']} | Шагов в логе: {target['total_steps']}")
    print("=" * 82)
    chat_turns = [t for t in data["turns"] if t["chat_order"] == order_num]
    for t in chat_turns:
        print(f" 💬 Итерация #{t['turn_index']} [{format_time_only(t['start_dt'])} — {format_time_only(t['end_dt'])}] (⚡ {t['duration_fmt']}):")
        print(f"    Промпт: \"{t['user_prompt'][:120]}...\"")
        if t["tool_calls"]:
            tools_unique = list(dict.fromkeys(t["tool_calls"]))[:4]
            print(f"    Инструменты: {', '.join(tools_unique)}")
        if t["files_modified"]:
            print(f"    Файлы: {', '.join(t['files_modified'])}")
        print("-" * 82)

def main():
    parser = argparse.ArgumentParser(description="GuapikoClaw Universal Timeline Analyzer & Chrono-Engine")
    parser.add_argument("--project", "--filter", type=str, help="Фильтр по ключевому слову проекта (softgames, bi-lagun, etsy, и т.д.)")
    parser.add_argument("--since", "--from", dest="since", type=str, help="Фильтр: дата начала (ГГГГ-ММ-ДД)")
    parser.add_argument("--until", "--to", dest="until", type=str, help="Фильтр: дата окончания (ГГГГ-ММ-ДД)")
    parser.add_argument("--days", type=int, help="Фильтр: за последние N дней")
    parser.add_argument("--recent", type=int, help="Авто-поиск последних N активных сессий")
    parser.add_argument("--chats", "--ids", type=str, help="Список ID сессий через запятую")
    parser.add_argument("--add", nargs="+", help="Добавить чат в реестр: --add <chat_id> <title> [badge] [color]")
    parser.add_argument("--list-saved", action="store_true", help="Показать сохраненные чаты в реестре")
    parser.add_argument("--hourly", action="store_true", help="Показать почасовую сетку активности")
    parser.add_argument("--gaps", action="store_true", help="Показать список пауз и перерывов")
    parser.add_argument("--chat", type=int, help="Показать подробный лог по номеру чата")
    parser.add_argument("--json", action="store_true", help="Вывести чистый JSON для программного чтения")
    parser.add_argument("--no-html", action="store_true", help="Не перегенерировать HTML-файл")
    parser.add_argument("--output-html", type=str, default="timeline_viewer.html", help="Путь для генерации HTML")

    args = parser.parse_args()

    if args.add:
        cid = args.add[0]
        title = args.add[1] if len(args.add) > 1 else f"Session {cid[:8]}"
        badge = args.add[2] if len(args.add) > 2 else "Tracked"
        color = args.add[3] if len(args.add) > 3 else None
        save_chat_to_config(cid, title, badge, color)
        return

    if args.list_saved:
        saved = load_saved_chats()
        print(f"Сохраненные чаты в {CONFIG_FILE} ({len(saved)} шт):")
        for c in saved:
            print(f"  [{c['order']}] {c['id']} — {c['title']} ({c.get('badge', '')})")
        return

    configs = build_chat_configs(args)
    if not configs:
        return

    data = process_timeline(configs, BRAIN_DIR)

    if not data["turns"]:
        print("⚠️ Нет событий по указанным чатам.")
        return

    if not args.no_html and not args.json:
        generate_html_viewer(data, args.output_html)

    if args.json:
        serializable = {
            "stats": data["stats"],
            "chats": [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "order": c["order"],
                    "badge": c["badge"],
                    "turns_count": c["turns_count"],
                    "total_steps": c["total_steps"],
                    "start_fmt": c["start_fmt"],
                    "end_fmt": c["end_fmt"],
                    "wall_duration": format_duration(c["wall_clock_sec"]),
                    "active_duration": format_duration(c["active_work_sec"]),
                    "idle_duration": format_duration(c["idle_sec"])
                }
                for c in data["chats"]
            ],
            "hourly_bins": data["hourly_bins"],
            "gaps": [
                {
                    "gap_type": g["gap_type"],
                    "gap_title": g["gap_title"],
                    "start_fmt": g["start_fmt"],
                    "end_fmt": g["end_fmt"],
                    "duration_fmt": g["duration_fmt"],
                    "is_cross_chat": g["is_cross_chat"]
                }
                for g in data["gaps"]
            ]
        }
        print(json.dumps(serializable, ensure_ascii=False, indent=2))
        return

    if args.hourly:
        print_hourly(data)
    elif args.gaps:
        print_gaps(data)
    elif args.chat:
        print_chat_detail(data, args.chat)
    else:
        print_summary(data)
        print("\n💡 Опции фильтрации и вывода:")
        print("   python scripts/timeline_analyzer.py --project <kw>   # Поиск по ключевому слову")
        print("   python scripts/timeline_analyzer.py --since 2026-08-19 # Фильтр по дате")
        print("   python scripts/timeline_analyzer.py --recent 5         # Последние N сессий")
        print("   python scripts/timeline_analyzer.py --hourly           # Почасовая сетка")
        print("   python scripts/timeline_analyzer.py --gaps             # Паузы и гэпы")
        print("   python scripts/timeline_analyzer.py --chat 2           # Детали чата")

if __name__ == "__main__":
    main()
