---
name: todo-manager
description: Manage a personal to-do list stored in a local file. Use when user says "add todo", "my tasks", "list tasks", "list todos", "done with X", "mark X complete", "remove X", "delete X", "clear done", or anything about tasks or a to-do list.
allowed-tools: Read, Write, Edit
---

Manage the user's todo list at `~/personal-bot/data/todos.md`.

## File Format

```
# Todo List

- [ ] Incomplete task
- [x] Completed task
```

If the file or the `data/` directory does not exist, create them before writing.

## Operations

| User says | Action |
|---|---|
| "add X" / "add todo X" | Append `- [ ] X` to the file |
| "list" / "my tasks" / "todos" | Read file, show incomplete first then completed |
| "done with X" / "complete X" / "finished X" | Change `- [ ] X` to `- [x] X` (partial text match) |
| "remove X" / "delete X" | Remove that line entirely |
| "clear done" / "clear completed" | Remove all `- [x]` lines |

## Response Format

Use Telegram Markdown formatting:

**After add / complete / remove** — one confirmation line:
```
Added: Finish assignment ✓
Marked complete: Study for quiz ✓
Removed: Old task ✓
```

**For list:**
```
*Your Todos (N incomplete, M done)*

⬜ Task 1
⬜ Task 2
✅ Completed task
```

**Empty list:**
"Your todo list is empty. Add a task with 'add [task name]'."

## Notes
- When matching tasks for complete/remove, use partial text (case-insensitive)
- If multiple tasks match, complete/remove the first match and mention it
- The file persists between sessions — it is the single source of truth
