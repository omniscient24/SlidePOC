# POC Agents for CPQ to Revenue Cloud Migration

This directory contains specialized agents to assist with different aspects of the Revenue Cloud Migration POC. Each agent has specific expertise and responsibilities.

## Available Agents

### 1. **Salesforce Integration Agent** (`salesforce_integration_agent.md`)
- Handles all Salesforce API operations
- Manages connections to fortradp2 and fortra-dev orgs
- Executes CRUD operations on Revenue Cloud objects
- Performs bulk data operations

### 2. **UI Development Agent** (`ui_development_agent.md`)
- Develops and maintains web interfaces
- Creates D3.js visualizations
- Implements modal dialogs and forms
- Ensures UI/UX best practices

### 3. **Data Migration Agent** (`data_migration_agent.md`)
- Manages data transformation from CPQ to Revenue Cloud
- Handles Excel/CSV processing
- Coordinates bulk uploads
- Validates data integrity

### 4. **Testing & QA Agent** (`testing_qa_agent.md`)
- Performs comprehensive testing
- Creates and maintains test suites
- Validates functionality
- Ensures quality standards

### 5. **Revenue Cloud Specialist Agent** (`revenue_cloud_specialist_agent.md`)
- Provides Revenue Cloud expertise
- Guides architecture decisions
- Offers migration best practices
- Handles complex RLM scenarios

## How to Use Agents

1. **Select the appropriate agent** based on your task
2. **Provide context** about your specific need
3. **Reference the agent's capabilities** to ensure it can help
4. **Follow the agent's guidelines** for best results

## Example Usage

```
"I need help with the Salesforce Integration Agent to debug why ProductCategory records aren't being created."

"Can the UI Development Agent help me add a new modal for product selection?"

"I need the Data Migration Agent to validate my Excel template before bulk upload."
```

## Agent Collaboration

Agents can work together on complex tasks:
- UI Agent creates interface → Integration Agent handles backend
- Migration Agent prepares data → Integration Agent uploads to Salesforce
- Testing Agent validates → Specialist Agent reviews architecture

## Current Project Context

- **Active Orgs**: fortradp2 (primary), fortra-dev (development)
- **Focus**: Product hierarchy management and visualization
- **Recent Work**: Add Category feature implementation
- **Key Objects**: ProductCatalog, ProductCategory, Product2, ProductCategoryProduct