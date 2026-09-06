# Minimal Project Template

## 🚀 Quick Start

To create a new project with this template:

```bash
# Navigate to your projects directory
cd /path/to/your/projects

# Copy the template
cp -r /Users/francisrey/Developer/project-template-minimal ./my-new-project

# Navigate to your new project
cd my-new-project

# Replace placeholders in files
find . -type f -name "*.md" -exec sed -i "" "s/\[PROJECT_NAME\]/my-new-project/g" {} \;
find . -type f -name "*.md" -exec sed -i "" "s/\[PROJECT_DESCRIPTION\]/My project description/g" {} \;
```
