# Claude Code Agent: Commit and Push POC Changes

## Agent Purpose
This agent will handle the complete workflow of documenting changes, updating task lists, and pushing code to GitHub for the CPQ Revenue Cloud Migration POC project.

## Prerequisites
- Working directory: `/Users/marcdebrey/cpq-revenue-cloud-migration/POC`
- Git repository initialized
- GitHub remote configured
- Active GitHub authentication

## Agent Instructions

### Step 1: Update Task Documentation

1. Review all completed tasks in the current session
2. Update the main task tracking file:
   ```bash
   # Create or update COMPLETED_TASKS.md with all completed work
   ```

### Step 2: Update Project Documentation

1. **Update PRD (Product Requirements Document)**:
   - Review `/docs/Revenue_Cloud_POC_PRD.md` if it exists
   - Document all implemented features
   - Update status of requirements

2. **Update Technical Documentation**:
   - Update `/docs/TECHNICAL_IMPLEMENTATION.md` with:
     - New features implemented
     - Architecture changes
     - API modifications
     - Database schema changes

3. **Update Change Log**:
   - Create/update `CHANGELOG.md` with:
     - Date and version
     - Features added
     - Bugs fixed
     - Known issues

4. **Update README if needed**:
   - Add any new setup instructions
   - Update feature list
   - Add new dependencies

### Step 3: Review and Stage Changes

1. **Check git status**:
   ```bash
   git status
   ```

2. **Review all changes**:
   ```bash
   git diff
   ```

3. **Stage all relevant files**:
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
   
   # DO NOT stage:
   # - server logs (*.log)
   # - temporary files
   # - .pyc files
   # - __pycache__
   # - data/sync-logs/
   # - data/upload-logs/
   ```

### Step 4: Create Detailed Commit

1. **Create comprehensive commit message**:
   ```bash
   git commit -m "feat: Implement Add Product functionality with hierarchy display

   - Add Product modal with form validation and auto-generation
   - Implement product creation in Salesforce with ProductCode generation
   - Add ProductCategoryProduct junction record creation
   - Fix event listener attachment for Add Product button
   - Fix ChangeTracker to preserve categoryId for products
   - Implement product ID query after bulk upload
   - Add comprehensive testing suite for product functionality
   
   Features:
   - Product form with Name, Description, ProductCode, SKU, Family fields
   - Auto-generation of ProductCode and SKU with customizable patterns
   - Real-time validation and field formatting
   - Integration with existing hierarchy refresh mechanism
   
   Bug Fixes:
   - Fix circular reference error in ChangeTracker
   - Fix delete functionality for subcategory nodes
   - Fix hierarchy refresh after node deletion
   - Fix catalog assignment for categories
   
   Testing:
   - Add Puppeteer browser automation tests
   - Add Salesforce query verification scripts
   - Add ProductCategoryProduct sync tests
   
   Known Issues:
   - Products may not display in hierarchy until ProductCategoryProduct sheet has correct column structure
   - Manual sync of ProductCategoryProduct may be required
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

### Step 5: Push to GitHub

1. **Verify remote**:
   ```bash
   git remote -v
   ```

2. **Push to remote**:
   ```bash
   git push origin main
   # or if on a feature branch:
   git push origin feature/add-product-functionality
   ```

3. **Verify push success**:
   ```bash
   git log --oneline -5
   git status
   ```

### Step 6: Create Summary Report

Create `PUSH_SUMMARY_[DATE].md` with:
- Commit hash
- Files changed count
- Features implemented
- Tests added
- Documentation updated
- Next steps

## Specific Files to Update

### 1. COMPLETED_TASKS.md
```markdown
# Completed Tasks - CPQ Revenue Cloud Migration POC

## Session Date: [CURRENT_DATE]

### Completed Features
- [x] Add Product functionality with modal interface
- [x] Product form validation and auto-generation
- [x] ProductCategoryProduct junction creation
- [x] Hierarchy refresh after product addition
- [x] Delete functionality for all node types
- [x] Circular reference fix in ChangeTracker

### Bug Fixes
- [x] Event listener attachment for dynamic buttons
- [x] ChangeTracker field preservation
- [x] Hierarchy refresh reliability
- [x] Category catalog assignment

### Testing
- [x] Puppeteer browser automation
- [x] Salesforce integration verification
- [x] Manual testing procedures documented
```

### 2. Key Documentation Updates

- `README.md` - Add new features and dependencies
- `docs/ARCHITECTURE.md` - Document component interactions
- `docs/API_REFERENCE.md` - Document new endpoints
- `TESTING_GUIDE.md` - Add new test procedures

## Important Notes

1. **Do NOT commit**:
   - Excel workbook files (*.xlsx)
   - Log files (*.log)
   - Temporary test files
   - API credentials or secrets
   - `__pycache__` directories

2. **Always include**:
   - Meaningful commit messages
   - Co-author attribution
   - Issue references if applicable

3. **Before pushing**:
   - Ensure all tests pass
   - Verify no sensitive data included
   - Check file permissions are correct

## Error Handling

If push fails due to:
- **Authentication**: Use `gh auth login` or check SSH keys
- **Conflicts**: Pull latest changes first with `git pull origin main`
- **Large files**: Use `.gitignore` to exclude them

## Completion Checklist

- [ ] All tasks documented in COMPLETED_TASKS.md
- [ ] PRD updated with implementation status
- [ ] Technical documentation current
- [ ] CHANGELOG.md updated
- [ ] All code changes staged
- [ ] Comprehensive commit message
- [ ] Successfully pushed to GitHub
- [ ] Summary report created