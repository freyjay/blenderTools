# Development Commands

## 🎯 Blueprint Workflow Commands

### Discovery Phase
```bash
# Always start here for new projects or major features
# 1. Enter plan mode with Claude
"lets go back to plan mode and deeply understand what we are building"

# 2. Create project blueprint  
"create a blueprint for our project"

# 3. Solidify vision
"solidify our project vision"

# 4. Review blueprint file
cat tasks/blueprint.md
```

### Blueprint Validation
```bash
# Check if blueprint is complete
grep "TO BE DETERMINED" tasks/blueprint.md  # Should return empty

# Verify all discovery questions answered
grep "\[ \]" tasks/blueprint.md            # Should show only incomplete tasks

# Review project status
cat tasks/todo.md
```

## Project Setup
```bash
# Initialize project
npm init -y

# Install dependencies
npm install

# Start development server
npm run dev
```

## Blueprint Development Workflow
```bash
# Phase 1: Discovery (REQUIRED FIRST)
npm run blueprint-check     # Check if blueprint exists and is complete

# Phase 2: Development (Only after blueprint approved)
npm run dev                 # Start development server
npm run test               # Run tests (when available)
npm run build              # Build for production (when configured)
```

## Template Commands
```bash
# Copy this template to new project
cp -r /Users/francisrey/Developer/testWEB /path/to/new-project

# Initialize new project from template
cd new-project && ./setup-project.sh "ProjectName" "Project Description"
```
