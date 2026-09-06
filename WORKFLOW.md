# Claude-Human Blueprint Workflow Documentation

## 🎯 Overview
This workflow ensures every project starts with clear vision and purpose before any development begins. It establishes a collaborative process between human and Claude to create meaningful applications.

## 🔄 The Complete Workflow Process

### Phase 1: Project Initiation
**When to use:** Starting any new project or major feature

1. **Technical Setup** (if needed)
   - Initialize project structure
   - Set up development environment
   - Configure basic tooling

2. **Mandatory Blueprint Discovery**
   - Human triggers: "lets go back to plan mode and deeply understand what we are building"
   - Claude enters plan mode automatically
   - NO development work proceeds without blueprint completion

### Phase 2: Discovery Process (CRITICAL)
**Claude must always:**

1. **Enter Plan Mode**
   - Use plan mode to prevent premature development
   - Focus entirely on understanding project goals

2. **Ask the 5 Key Questions**
   - What type of web application are we building?
   - What are the core features you envision?
   - Who are the users and what problems does this solve?
   - Technical preferences (frontend, database, auth, APIs)?
   - Scope and timeline (learning project, MVP, full app)?

3. **Document Everything**
   - Create/update `tasks/blueprint.md`
   - Fill in all template sections
   - Record decisions and reasoning

4. **Validate Understanding**
   - Present comprehensive plan using ExitPlanMode tool
   - Get explicit user approval before proceeding
   - Ensure alignment on vision and scope

### Phase 3: Development Execution
**Only after blueprint approval:**

1. **Create Development Todos**
   - Break blueprint into actionable tasks
   - Use TodoWrite tool to track progress
   - Prioritize MVP features first

2. **Implement Systematically**
   - Follow blueprint decisions
   - Build incrementally
   - Test frequently

3. **Stay On Track**
   - Refer back to blueprint for decisions
   - Update blueprint if scope changes
   - Re-enter plan mode for major direction changes

## 🚦 Decision Gates

### Gate 1: Technical Foundation
- [ ] Project structure exists
- [ ] Development environment ready
- [ ] Basic tooling configured

### Gate 2: Blueprint Complete
- [ ] All 5 key questions answered
- [ ] `tasks/blueprint.md` fully completed
- [ ] User has approved the plan
- [ ] Technical architecture defined

### Gate 3: Development Ready
- [ ] Development todos created
- [ ] MVP features identified
- [ ] Implementation approach confirmed

## 🎯 Success Indicators

### Good Blueprint Session
- Claude asks clarifying questions
- All "TO BE DETERMINED" placeholders filled
- Technical decisions made with reasoning
- User feels confident about direction
- Clear next steps identified

### Poor Blueprint Session (Avoid)
- Claude jumps straight to coding
- Vague or incomplete requirements
- Technical decisions made without discussion
- User unsure about project direction
- Missing key architectural decisions

## 🔧 Template Integration

### File Structure
```
testWEB/
├── CLAUDE.md              # Contains blueprint workflow
├── tasks/
│   ├── todo.md           # Current work tracking
│   └── blueprint.md      # Project vision (REQUIRED)
├── config/
│   └── commands.md       # Workflow commands
└── WORKFLOW.md           # This documentation
```

### Key Commands
- `"lets go back to plan mode and deeply understand what we are building"`
- `"create a blueprint for our project"`
- `"solidify our project vision"`

## 🔄 Template Reusability

### For New Projects
1. Copy testWEB template to new location
2. Run setup script to customize placeholders
3. Immediately enter blueprint discovery phase
4. Complete tasks/blueprint.md before any development

### For Existing Projects
1. Add blueprint workflow to CLAUDE.md
2. Create tasks/blueprint.md if missing
3. Run discovery process to document current vision
4. Use for future feature planning

## 📋 Checklist for Claude

**Before any development work:**
- [ ] Is there a complete tasks/blueprint.md file?
- [ ] Have all 5 key questions been answered?
- [ ] Has the user approved the plan?
- [ ] Are technical decisions documented?

**If any answer is "No" → Enter plan mode immediately**

## 🎯 Benefits of This Workflow

1. **Prevents Scope Creep** - Clear vision from start
2. **Reduces Rework** - Right decisions upfront  
3. **Improves Collaboration** - Shared understanding
4. **Speeds Development** - Clear requirements
5. **Creates Better Products** - User-focused approach

---

**Remember: This workflow prioritizes thoughtful planning over rushed development, ensuring every project has purpose and direction.**