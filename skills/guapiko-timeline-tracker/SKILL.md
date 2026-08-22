---
name: guapiko-timeline-tracker
description: >-
  Хронометраж, аудит транскриптов и трекинг времени разработки для агентов GuapikoClaw.
  Позволяет рассчитывать чистое рабочее время (Active Work), фильтровать сессии по проектам/датам,
  выявлять гэпы (паузы/сон), строить почасовые сетки плотности и обновлять интерактивный HTML-дашборд.
---

# ⏱️ Guapiko Timeline Tracker & Chrono-Engine

## 1. Overview & Концепция

Навык **`guapiko-timeline-tracker`** предоставляет AI-агентам и оператору студии унифицированный инструмент для парсинга локальных транскриптов диалогов (`transcript.jsonl`), точного расчета чистого времени разработки, категоризации пауз (гэпов) и визуализации сквозных таймлайнов проектов.

```
[transcript.jsonl] ──> [scripts/timeline_analyzer.py] ──> [Консольная сводка / JSON / Почасовая сетка]
                                                      └──> [Интерактивный timeline_viewer.html]
```

### Ключевые возможности:
1. **Событийная модель (Event-Driven Extraction):** Извлечение каждой итерации диалога (`USER_INPUT` $\rightarrow$ `MODEL` $\rightarrow$ `TOOL_CALLS`).
2. **Расчет чистого времени (Active Time vs Gaps):** Отделение реального времени выполнения кода и генерации от пауз, сна и ожидания оператора.
3. **Унифицированная фильтрация:** Поиск по ключевым словам проектов (`--project`), датам (`--since`, `--until`, `--days`), списку ID (`--chats`) или последним сессиям (`--recent`).
4. **44+ Часовая визуализация:** Почасовая сетка плотности и интерактивный дашборд с мгновенным скроллом к итерациям.

---

## 2. Быстрый старт и CLI-справочник

Скрипт анализатора расположен по пути: [`scripts/timeline_analyzer.py`](file:///c:/Misc/GuapikoProjects/Vaults/GuapikoClaw/GuapikoClaw/scripts/timeline_analyzer.py).

### Базовые команды:

```bash
# 1. Полная сводка по сохраненным сессиям + обновление HTML-дашборда
python scripts/timeline_analyzer.py

# 2. Почасовая сетка активности (44+ часа с минутами работы и паузами)
python scripts/timeline_analyzer.py --hourly

# 3. Полный реестр пауз и перерывов (микро-паузы, плейтесты, сон)
python scripts/timeline_analyzer.py --gaps

# 4. Детальный лог конкретной сессии по ее порядковому номеру
python scripts/timeline_analyzer.py --chat 2

# 5. Машинный JSON для автоматической обработки агентами
python scripts/timeline_analyzer.py --json
```

---

## 3. Протоколы поиска и фильтрации (Для AI-Агентов)

Агент может выполнять гибкие поисковые запросы по истории транскриптов студии:

### 🔍 А. Поиск по проекту или ключевому слову
Ищет все сессии в `~/.gemini/antigravity/brain/`, где в промптах упоминается проект:
```bash
python scripts/timeline_analyzer.py --project softgames
python scripts/timeline_analyzer.py --project bi-lagun
python scripts/timeline_analyzer.py --project etsy
```

### 📅 Б. Фильтрация по датам и диапазонам
```bash
# Все сессии начиная с конкретной даты:
python scripts/timeline_analyzer.py --since 2026-08-19

# Сессии в заданном диапазоне дат:
python scripts/timeline_analyzer.py --since 2026-08-18 --until 2026-08-20

# Сессии за последние N дней:
python scripts/timeline_analyzer.py --days 2
```

### ⚡ В. Авто-обнаружение последних активных сессий
Автоматически сканирует директорию `brain` и берет топ-$N$ последних чатов:
```bash
python scripts/timeline_analyzer.py --recent 5
```

### 🎯 Г. Анализ конкретного списка Conversation ID
```bash
python scripts/timeline_analyzer.py --chats 3941989a-09f0-457c-910e-7ef9ed6992bf,103ab5c9-fe44-4388-bcbf-43f76966133b
```

---

## 4. Гибридный протокол управления реестром чатов

Чаты могут управляться двумя способами:

### Способ 1: Регистрация в реестр `data/timeline_chats.json`
Чтобы чат стал постоянной частью проекта и отображался по умолчанию:
```bash
# Добавить сессию в реестр:
python scripts/timeline_analyzer.py --add <conversation_id> "Название сессии" "Бейдж" "#Цвет"

# Посмотреть сохраненный реестр:
python scripts/timeline_analyzer.py --list-saved
```

Пример структуры `data/timeline_chats.json`:
```json
[
  {
    "id": "3941989a-09f0-457c-910e-7ef9ed6992bf",
    "title": "Chat 1: Исследование, Архитектура и Декомпозиция",
    "order": 1,
    "badge": "Architecture & Tasks",
    "color": "#3b82f6"
  }
]
```

### Способ 2: Динамический анализ на лету
Агент запускает команду с фильтрами (`--project`, `--since`, `--recent`), получает сводку и обновляет [`timeline_viewer.html`](file:///c:/Misc/GuapikoProjects/Vaults/GuapikoClaw/GuapikoClaw/timeline_viewer.html) без перезаписи конфигурационного файла.

---

## 5. Интерактивный дашборд (`timeline_viewer.html`)

При каждом запуске скрипта автоматически генерируется или обновляется файл:
📁 [`timeline_viewer.html`](file:///c:/Misc/GuapikoProjects/Vaults/GuapikoClaw/GuapikoClaw/timeline_viewer.html)

### Правила работы UI:
1. **Инвариант первого события (First Event Invariant):** При клике на карточку любого чата список событий фильтруется строго от **Итерации #1** этого чата. Предшествующий межсессионный гэп скрывается, чтобы фокус был сразу на работе.
2. **44+ Часовой Gantt & Density Chart:** Почасовые столбцы ($0\dots 60\text{ мин}$) с цветовыми маркерами сессий. Клик по столбцу плавно скроллит страницу к началу диалога в этот час.
3. **Быстрые фильтры:** Переключение между режимами:
   - `Все события`
   - `Только активная работа`
   - `Только паузы и гэпы`
   - `Длительные перерывы (>30 мин)`
4. **Живой поиск:** Мгновенная фильтрация по тексту пользовательских промптов, именам запущенных инструментов и измененным файлам.

---

## 6. Рекомендации и правила для агентов (Agent Guidelines)

> [!TIP]
> При необходимости восстановить контекст того, что делалось в проекте за последние дни, выполните:
> `python scripts/timeline_analyzer.py --since <YYYY-MM-DD> --project <keyword>`
> Это вернет полную хронологическую цепочку шагов без необходимости читать гигабайты сырых JSONL-файлов вручную.

> [!IMPORTANT]
> Если в Windows-консоли требуется чистый JSON без цветного текста и символов псевдографики, всегда передавайте флаг `--json`.
