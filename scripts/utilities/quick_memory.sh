#!/bin/bash
# Quick memory save script
# Usage: ./quick_memory.sh "Your text to remember"

if [ $# -eq 0 ]; then
    echo "Usage: ./quick_memory.sh \"Text to remember\" [entity_name] [entity_type]"
    echo "Examples:"
    echo "  ./quick_memory.sh \"Remember to test upload function\""
    echo "  ./quick_memory.sh \"API endpoint is /api/v2\" \"API Info\" \"Technical Note\""
    exit 1
fi

python3 memory_helper.py "$@"