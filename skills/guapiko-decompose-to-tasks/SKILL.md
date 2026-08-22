---
name: guapiko-decompose-to-tasks
description: >-
  Teaches the agent to decompose projects into LLM-optimized task files. Focuses on context window management (50k-100k tokens), explicit testing instructions, and zero human management overhead (no deadlines).
---

# Task Decomposition for LLM Agents

## Overview
This skill instructs agents on how to translate a Game Design Document (GDD) or project scope into actionable, isolated tasks that other LLM agents can execute efficiently. It specifically optimizes for the constraints and strengths of Large Language Models (LLMs).

## Core Rules

When decomposing a project into tasks, you MUST follow these native AI-UX rules:

### 1. File Structure & Location
Every client folder within the `Projects/` directory must contain a `tasks/` subfolder.
- Each individual task must be saved as a separate Markdown file.
- **Naming Convention:** `Projects/[ClientName]/tasks/task_[number]_[descriptive_name].md` (e.g., `task_01_bignumber_math.md`).

### 2. Context Optimization (50k-100k Token Density)
LLMs perform optimally when given a dense, encapsulated chunk of work that heavily utilizes a moderately sized context window (up to ~100k tokens). Accuracy degrades beyond this point.
- **No Micro-Tasks:** Do not create tasks like "Change button color" or "Rename a variable."
- **No Mega-Tasks:** Do not create tasks like "Build the entire core loop" if it requires 500k tokens of context.
- **Optimal Scope:** Group related features into a dense, logical module. For example, "Implement the entire BigNumber library and its unit tests" or "Refactor the Manager Automation system and wire it to the UI."

### 3. Asynchronous Execution (No Deadlines)
LLM agents do not perceive time like humans do; they execute instantly upon invocation.
- **Never include human deadlines** or time estimates (e.g., "Due on Friday", "Estimated time: 2 days").
- Focus entirely on **dependencies** (e.g., "Must be done after task_01 is completed").

### 4. Explicit Context Priming
Do not force the executing agent to blindly search the workspace for context. You must serve the context to them.
- Each task MUST contain a section explicitly listing the absolute paths of the files the agent needs to read.
- Specify which APIs, libraries, or design documents are relevant to this specific task.

### 5. Pre-defined Testing Instructions
An LLM reaching the end of a 100k-token task execution has a heavily saturated context window. Do not force it to invent tests from scratch at that stage.
- The task file MUST include a strict `Testing / QA` section.
- Provide explicit testing steps, CLI commands to run, or specific edge-case scenarios to verify (e.g., "Run `godot --test BigNumberTest.gd`" or "Ensure that buying 100 units with 0 cash fails and throws no errors").
- Give the developer agent clear hints on what to look for when verifying their own work.

## Task File Template
Use the following Markdown structure when creating a task file:

```markdown
# Task: [Task Name]

## Objective
[Clear, concise description of what needs to be implemented]

## Required Context
Read the following files before starting:
- [absolute/path/to/relevant_file1.gd]
- [absolute/path/to/GDD.md]

## Implementation Details
[Detailed technical requirements, math formulas, and architectural constraints. Encapsulated scope (50k-100k tokens).]

## Dependencies
[What needs to be finished before this task, or what this task blocks]

## Testing & Verification
[Strict, step-by-step testing instructions, edge cases to check, and CLI commands. Do not leave this open-ended.]
```

---

## Completion Protocol (CRITICAL)

When you are invoked as a subagent by an orchestrator or any parent agent, you **MUST** use the `send_message` tool to send your completion report back to the parent agent when you finish your work.

**Rules:**
- Do NOT just output text into your own context — the parent agent cannot see it.
- You MUST explicitly call `send_message` with the conversation ID of the agent that invoked you.
- Include a summary of all created/modified task files and their descriptions in the message body.
- If you are blocked and cannot complete the task, send a message explaining why.

**Example:**
```
send_message(
  Recipient: "<parent_conversation_id>",
  Message: "Decomposition complete. Created 3 task files: [list and brief descriptions]"
)
```

Failure to send this message will cause the parent agent to stall indefinitely. This is a **hard requirement**.
