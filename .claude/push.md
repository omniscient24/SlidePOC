# /push - Commit and Push POC Changes to GitHub

This command handles the complete workflow of documenting changes, updating task lists, and pushing code to GitHub for the CPQ Revenue Cloud Migration POC project.

## Step 1: Review Current Status

First, let me check the current git status and recent changes:

```bash
cd /Users/marcdebrey/cpq-revenue-cloud-migration/POC
git status
git diff --stat
```

## Step 2: Update Task Documentation

Create or update COMPLETED_TASKS.md with all completed work from this session.

## Step 3: Update Project Documentation

1. Update or create necessary documentation files:
   - CHANGELOG.md - Document all changes
   - docs/TECHNICAL_IMPLEMENTATION.md - Technical details
   - README.md - Update if features added

## Step 4: Stage Changes

Stage all relevant files while excluding logs and temporary files:

```bash
# Stage code changes
git add app/
git add static/
git add templates/

# Stage documentation
git add *.md
git add docs/

# Stage test files
git add test*.py

# Check what will be committed
git status
```

## Step 5: Create Commit

Create a detailed commit message with:
- Clear description of changes
- List of features/fixes
- Co-author attribution

## Step 6: Push to GitHub

```bash
# Push to remote repository
git push origin main
```

## Step 7: Verify and Report

Create a summary of what was pushed and any follow-up needed.

---

Let me start this process by checking the current repository status.