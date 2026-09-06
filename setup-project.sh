#!/bin/bash

# Project Template Setup Script
# Usage: ./setup-project.sh [PROJECT_NAME] [PROJECT_DESCRIPTION]

if [ $# -lt 2 ]; then
    echo "Usage: ./setup-project.sh [PROJECT_NAME] [PROJECT_DESCRIPTION]"
    echo "Example: ./setup-project.sh my-app \"A modern web application\""
    exit 1
fi
