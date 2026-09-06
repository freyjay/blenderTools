# Claude Code & Cursor Project Setup Guide

## Quick Setup Steps

1. **Create directory structure:**
   ```bash
   mkdir -p .claude config tasks
   ```

2. **Essential files to create:**
   - CLAUDE.md (main memory file)
   - .claude/settings.json (project settings)
   - .claude/settings.local.json (local permissions - optional)
   - .claudeignore (exclusion rules)
   - .cursorrules (Cursor AI instructions)

3. **Config directory files:**
   - config/commands.md (development commands)
   - config/standards.md (coding standards)
   - config/stack.md (tech stack info)
   - config/environment.md (setup requirements)

4. **Task management files:**
   - tasks/todo.md (current work tracking)
   - tasks/frontend.md (frontend tasks - if applicable)
   - tasks/backend.md (backend tasks - if applicable)

## File Templates

### CLAUDE.md Template:
```markdown
# [PROJECT_NAME]

Clean, focused memory file for [PROJECT_DESCRIPTION].

## config/
### commands.md
Development commands for this project

### standards.md
Coding standards and conventions

### stack.md
Tech stack information

### environment.md
Setup requirements and configuration

## tasks/
### todo.md
Current work items and progress tracking

### [feature].md
Feature-specific tasks (create as needed)

## .claudeignore
Exclusion rules for Claude Code
```

### .claude/settings.json Template:
```json
{
  "permissions": {
    "allow": ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "LS"]
  }
}
```

### .claudeignore Template:
```
# Ignore common files that don't need Claude's attention
node_modules/
.git/
*.log
.DS_Store
dist/
build/
coverage/

# Claude settings (keep private)
.claude/settings.local.json
```

### .cursorrules Template:
```
# Cursor AI Rules for [PROJECT_NAME]

## Project Context
[PROJECT_DESCRIPTION]

## Coding Standards
- Keep code clean and simple
- Follow existing patterns in the codebase
- Use [LANGUAGE/FRAMEWORK] when applicable
- Prefer explicit over implicit
```

## Alex Finn's 7-Rule Methodology (Advanced)

For comprehensive AI-assisted development, implement:

1. **Think & Plan** - Analyze in tasks/todo.md
2. **Create Todo List** - Break work into checkable items
3. **Verify** - Check plans before starting
4. **Track Progress** - Mark todos complete as you go
5. **Explain Changes** - Provide high-level explanations
6. **Keep Simple** - Make minimal impact changes
7. **Review** - Add summaries to tasks/todo.md

## Usage Commands

### Claude Code:
- `claude` - Start session in project directory
- Files are automatically read from CLAUDE.md

### Cursor:
- `cursor .` - Open project in Cursor
- Ctrl/Cmd+K - Trigger AI assistance
- .cursorrules automatically applied

## Reference Locations

- Template project: `/Users/francisrey/Developer/project-template-minimal`
- Test setup: `/Users/francisrey/Developer/afterCCCsetup`

## Notes

- Both tools work without these files, but they provide project-specific context
- .claude/settings.local.json contains personal permissions (keep private)
- CLAUDE.md serves as shared context between Claude Code and Cursor
- Cross-reference files using @ notation (e.g., @config/commands.md)

---

**Created:** July 25, 2024
**Based on:** claude-cursor-setup-guide.txt
**Template Location:** /Users/francisrey/Developer/project-template-minimal
