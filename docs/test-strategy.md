# Revenue Cloud Migration Tool - Test Strategy & Scripts

## 1. Test Strategy Overview

### Testing Principles
1. **Shift-Left Testing**: Test early and often
2. **Automation First**: Automate repetitive tests
3. **Risk-Based Testing**: Focus on critical functionality
4. **Continuous Testing**: Integrate with CI/CD pipeline
5. **User-Centric**: Test from user perspective

### Testing Levels

```
┌─────────────────────────────────────────────────────────┐
│                    Testing Pyramid                       │
│                                                          │
│                    ┌───────────┐                        │
│                   /    E2E      \                       │
│                  /   UI Tests    \    (10%)            │
│                 ┌─────────────────┐                    │
│                /   Integration     \                    │
│               /      Tests          \  (20%)           │
│              ┌───────────────────────┐                 │
│             /      Unit Tests         \                 │
│            /    Component Tests        \ (70%)          │
│           └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## 2. Test Coverage Requirements

### Code Coverage Targets
- **Unit Tests**: 80% minimum coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: Main user journeys
- **Overall Coverage**: 85% target

### Functional Coverage
- **Authentication**: 100% coverage
- **Data Upload**: 100% coverage
- **Validation**: 95% coverage
- **Sync Operations**: 100% coverage
- **UI Components**: 90% coverage

## 3. Test Environment Strategy

### Environment Setup
```yaml
environments:
  development:
    database: PostgreSQL (Docker)
    cache: Redis (Docker)
    salesforce: Sandbox org
    data: Synthetic test data
    
  staging:
    database: PostgreSQL (RDS)
    cache: Redis (ElastiCache)
    salesforce: Full sandbox
    data: Anonymized production data
    
  production:
    database: PostgreSQL (RDS Multi-AZ)
    cache: Redis (ElastiCache)
    salesforce: Production org
    data: Live data
```

## 4. Unit Test Scripts

### 4.1 Backend Unit Tests

```python
# tests/unit/test_validation_service.py
import pytest
from app.services.validation_service import ValidationService
from app.models.validation_rules import RequiredFieldRule, DataTypeRule

class TestValidationService:
    
    @pytest.fixture
    def validation_service(self):
        return ValidationService()
    
    def test_required_field_validation_success(self, validation_service):
        """Test that required field validation passes with valid data"""
        rule = RequiredFieldRule(field_name="Name")
        data = {"Name": "Test Product"}
        
        result = validation_service.validate_field(rule, data)
        
        assert result.is_valid == True
        assert result.errors == []
    
    def test_required_field_validation_failure(self, validation_service):
        """Test that required field validation fails with missing data"""
        rule = RequiredFieldRule(field_name="Name")
        data = {"Description": "Test"}
        
        result = validation_service.validate_field(rule, data)
        
        assert result.is_valid == False
        assert "Name is required" in result.errors[0]
    
    def test_data_type_validation_number(self, validation_service):
        """Test number data type validation"""
        rule = DataTypeRule(field_name="Price", data_type="number")
        
        # Valid number
        result = validation_service.validate_field(rule, {"Price": "123.45"})
        assert result.is_valid == True
        
        # Invalid number
        result = validation_service.validate_field(rule, {"Price": "abc"})
        assert result.is_valid == False
        assert "Price must be a number" in result.errors[0]
    
    def test_validate_multiple_rules(self, validation_service):
        """Test validation with multiple rules"""
        rules = [
            RequiredFieldRule(field_name="Name"),
            DataTypeRule(field_name="Price", data_type="number"),
            RequiredFieldRule(field_name="ProductCode")
        ]
        data = {
            "Name": "Test Product",
            "Price": "99.99"
            # Missing ProductCode
        }
        
        results = validation_service.validate_all(rules, data)
        
        assert len(results.errors) == 1
        assert "ProductCode is required" in results.errors[0]
```

```python
# tests/unit/test_salesforce_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.salesforce_service import SalesforceService
from app.exceptions import SalesforceAPIError

class TestSalesforceService:
    
    @pytest.fixture
    def mock_sf_client(self):
        return Mock()
    
    @pytest.fixture
    def salesforce_service(self, mock_sf_client):
        service = SalesforceService()
        service.client = mock_sf_client
        return service
    
    def test_query_objects_success(self, salesforce_service, mock_sf_client):
        """Test successful object query"""
        mock_sf_client.query.return_value = {
            'totalSize': 2,
            'records': [
                {'Id': '001xx000003DHP0', 'Name': 'Account 1'},
                {'Id': '001xx000003DHP1', 'Name': 'Account 2'}
            ]
        }
        
        results = salesforce_service.query_objects('Account', ['Id', 'Name'])
        
        assert len(results) == 2
        assert results[0]['Name'] == 'Account 1'
        mock_sf_client.query.assert_called_once()
    
    def test_query_objects_with_filter(self, salesforce_service, mock_sf_client):
        """Test object query with WHERE clause"""
        mock_sf_client.query.return_value = {'totalSize': 1, 'records': []}
        
        salesforce_service.query_objects(
            'Account', 
            ['Id', 'Name'],
            where="Type = 'Customer'"
        )
        
        called_query = mock_sf_client.query.call_args[0][0]
        assert "WHERE Type = 'Customer'" in called_query
    
    def test_bulk_insert_success(self, salesforce_service, mock_sf_client):
        """Test successful bulk insert"""
        mock_bulk = Mock()
        mock_sf_client.bulk.return_value = mock_bulk
        mock_bulk.insert.return_value = [
            {'id': '001xx000003DHP0', 'success': True},
            {'id': '001xx000003DHP1', 'success': True}
        ]
        
        data = [
            {'Name': 'Account 1', 'Type': 'Customer'},
            {'Name': 'Account 2', 'Type': 'Partner'}
        ]
        
        results = salesforce_service.bulk_insert('Account', data)
        
        assert all(r['success'] for r in results)
        mock_bulk.insert.assert_called_once_with('Account', data)
    
    def test_connection_error_handling(self, salesforce_service, mock_sf_client):
        """Test connection error handling"""
        mock_sf_client.query.side_effect = Exception("Connection failed")
        
        with pytest.raises(SalesforceAPIError) as exc_info:
            salesforce_service.query_objects('Account', ['Id'])
        
        assert "Connection failed" in str(exc_info.value)
```

### 4.2 Frontend Unit Tests

```javascript
// tests/unit/components/FileUploader.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUploader from '@/components/FileUploader';
import { uploadFile } from '@/services/api';

jest.mock('@/services/api');

describe('FileUploader Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload area', () => {
    render(<FileUploader />);
    
    expect(screen.getByText(/drag.*drop.*files/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /browse/i })).toBeInTheDocument();
  });

  test('accepts valid file types', async () => {
    render(<FileUploader acceptedTypes={['.xlsx', '.csv']} />);
    
    const file = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const input = screen.getByLabelText(/file input/i);
    await userEvent.upload(input, file);
    
    expect(screen.getByText('test.xlsx')).toBeInTheDocument();
  });

  test('rejects invalid file types', async () => {
    render(<FileUploader acceptedTypes={['.xlsx', '.csv']} />);
    
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    const input = screen.getByLabelText(/file input/i);
    await userEvent.upload(input, file);
    
    expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
  });

  test('shows upload progress', async () => {
    uploadFile.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => resolve({ success: true }), 100);
      });
    });
    
    render(<FileUploader />);
    
    const file = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const input = screen.getByLabelText(/file input/i);
    await userEvent.upload(input, file);
    
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/upload complete/i)).toBeInTheDocument();
    });
  });

  test('handles upload errors', async () => {
    uploadFile.mockRejectedValue(new Error('Upload failed'));
    
    render(<FileUploader />);
    
    const file = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const input = screen.getByLabelText(/file input/i);
    await userEvent.upload(input, file);
    
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
    });
  });
});
```

```javascript
// tests/unit/components/ValidationResults.test.js
import { render, screen } from '@testing-library/react';
import ValidationResults from '@/components/ValidationResults';

describe('ValidationResults Component', () => {
  const mockResults = {
    success: false,
    totalRecords: 100,
    validRecords: 85,
    errors: [
      {
        row: 10,
        field: 'ProductCode',
        message: 'ProductCode is required',
        severity: 'error'
      },
      {
        row: 25,
        field: 'Price',
        message: 'Price must be a positive number',
        severity: 'error'
      },
      {
        row: 50,
        field: 'Description',
        message: 'Description is recommended',
        severity: 'warning'
      }
    ]
  };

  test('displays validation summary', () => {
    render(<ValidationResults results={mockResults} />);
    
    expect(screen.getByText(/85.*100.*records.*valid/i)).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  test('shows error count by severity', () => {
    render(<ValidationResults results={mockResults} />);
    
    expect(screen.getByText(/2.*errors/i)).toBeInTheDocument();
    expect(screen.getByText(/1.*warning/i)).toBeInTheDocument();
  });

  test('displays individual errors', () => {
    render(<ValidationResults results={mockResults} />);
    
    expect(screen.getByText(/row 10/i)).toBeInTheDocument();
    expect(screen.getByText(/ProductCode is required/i)).toBeInTheDocument();
  });

  test('shows success state when all valid', () => {
    const successResults = {
      success: true,
      totalRecords: 100,
      validRecords: 100,
      errors: []
    };
    
    render(<ValidationResults results={successResults} />);
    
    expect(screen.getByText(/all records valid/i)).toBeInTheDocument();
    expect(screen.getByTestId('success-icon')).toBeInTheDocument();
  });
});
```

## 5. Integration Test Scripts

```python
# tests/integration/test_upload_workflow.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import pandas as pd

from app.main import app
from app.database import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestUploadWorkflow:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        # Login and get token
        response = client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "testpass123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def sample_excel_file(self):
        # Create sample Excel file
        df = pd.DataFrame({
            'Name': ['Product 1', 'Product 2', 'Product 3'],
            'ProductCode': ['P001', 'P002', 'P003'],
            'Price': [100.00, 200.00, 300.00],
            'IsActive': [True, True, False]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            return tmp.name
    
    def test_complete_upload_workflow(self, client, auth_headers, sample_excel_file):
        """Test complete file upload workflow"""
        
        # Step 1: Upload file
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/api/data/upload",
                files={"file": ("products.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        upload_id = response.json()["upload_id"]
        
        # Step 2: Validate uploaded data
        response = client.post(
            f"/api/data/validate/{upload_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        validation_result = response.json()
        assert validation_result["valid_records"] == 3
        assert validation_result["errors"] == []
        
        # Step 3: Map fields
        field_mapping = {
            "Name": "Name",
            "ProductCode": "ProductCode", 
            "Price": "UnitPrice",
            "IsActive": "IsActive"
        }
        
        response = client.post(
            f"/api/data/map/{upload_id}",
            json={"mapping": field_mapping},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Step 4: Process upload to Salesforce
        response = client.post(
            f"/api/data/process/{upload_id}",
            json={"object": "Product2"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        process_id = response.json()["process_id"]
        
        # Step 5: Check processing status
        response = client.get(
            f"/api/operations/{process_id}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status = response.json()
        assert status["status"] in ["pending", "processing", "completed"]
    
    def test_upload_with_validation_errors(self, client, auth_headers):
        """Test upload with validation errors"""
        
        # Create file with errors
        df = pd.DataFrame({
            'Name': ['Product 1', '', 'Product 3'],  # Missing name
            'ProductCode': ['P001', 'P002', 'P001'],  # Duplicate code
            'Price': [100.00, -50.00, 300.00],  # Negative price
            'IsActive': [True, True, 'Invalid']  # Invalid boolean
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            
            with open(tmp.name, 'rb') as f:
                response = client.post(
                    "/api/data/upload",
                    files={"file": ("products.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    headers=auth_headers
                )
        
        upload_id = response.json()["upload_id"]
        
        # Validate
        response = client.post(
            f"/api/data/validate/{upload_id}",
            headers=auth_headers
        )
        
        validation_result = response.json()
        assert validation_result["valid_records"] < 3
        assert len(validation_result["errors"]) > 0
        
        # Check specific errors
        error_types = [e["type"] for e in validation_result["errors"]]
        assert "required_field" in error_types
        assert "duplicate_value" in error_types
        assert "invalid_value" in error_types
```

```python
# tests/integration/test_sync_workflow.py
import pytest
from unittest.mock import patch, Mock
import asyncio

class TestSyncWorkflow:
    
    @pytest.fixture
    def mock_salesforce(self):
        with patch('app.services.salesforce_service.Salesforce') as mock:
            yield mock
    
    async def test_bidirectional_sync(self, client, auth_headers, mock_salesforce):
        """Test bidirectional sync between Salesforce and local data"""
        
        # Mock Salesforce data
        mock_sf = Mock()
        mock_salesforce.return_value = mock_sf
        mock_sf.query.return_value = {
            'totalSize': 2,
            'records': [
                {
                    'Id': '01t000000000001',
                    'Name': 'Updated Product 1',
                    'ProductCode': 'P001',
                    'LastModifiedDate': '2023-06-22T10:00:00.000+0000'
                },
                {
                    'Id': '01t000000000002',
                    'Name': 'New Product',
                    'ProductCode': 'P004',
                    'LastModifiedDate': '2023-06-22T11:00:00.000+0000'
                }
            ]
        }
        
        # Start sync
        response = await client.post(
            "/api/data/sync",
            json={
                "object": "Product2",
                "mode": "bidirectional",
                "last_sync": "2023-06-22T09:00:00.000+0000"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        sync_id = response.json()["sync_id"]
        
        # Wait for sync to complete
        max_attempts = 10
        for _ in range(max_attempts):
            response = await client.get(
                f"/api/operations/{sync_id}/status",
                headers=auth_headers
            )
            status = response.json()
            if status["status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Check sync results
        assert status["status"] == "completed"
        assert status["summary"]["records_updated"] == 1
        assert status["summary"]["records_created"] == 1
        assert status["summary"]["conflicts_resolved"] == 0
```

## 6. End-to-End Test Scripts

```javascript
// tests/e2e/new-implementation.spec.js
import { test, expect } from '@playwright/test';

test.describe('New Implementation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('complete phase 1 implementation', async ({ page }) => {
    // Navigate to new implementation
    await page.click('text=New Implementation');
    await expect(page).toHaveURL('/implementation/new');
    
    // Phase 1 should be active
    await expect(page.locator('.phase-1')).toHaveClass(/active/);
    
    // Upload Account data
    await page.click('text=Upload Account Data');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-data/accounts.xlsx');
    
    await page.click('button:has-text("Upload")');
    
    // Wait for upload to complete
    await expect(page.locator('.upload-progress')).toHaveText('100%');
    
    // Validate data
    await page.click('button:has-text("Validate")');
    await expect(page.locator('.validation-status')).toHaveText('Passed');
    
    // Process to Salesforce
    await page.click('button:has-text("Process")');
    await expect(page.locator('.process-status')).toHaveText('Completed');
    
    // Check task completion
    await expect(page.locator('.task-account')).toHaveClass(/completed/);
    
    // Continue with other Phase 1 objects...
    const phase1Objects = ['Contact', 'LegalEntity', 'TaxEngine'];
    
    for (const obj of phase1Objects) {
      await page.click(`text=Upload ${obj} Data`);
      await fileInput.setInputFiles(`test-data/${obj.toLowerCase()}.xlsx`);
      await page.click('button:has-text("Upload")');
      await expect(page.locator('.upload-progress')).toHaveText('100%');
      await page.click('button:has-text("Process")');
      await expect(page.locator('.process-status')).toHaveText('Completed');
    }
    
    // Phase 1 should be complete
    await expect(page.locator('.phase-1-status')).toHaveText('Completed');
    
    // Phase 2 should now be active
    await expect(page.locator('.phase-2')).toHaveClass(/active/);
  });

  test('handle validation errors', async ({ page }) => {
    await page.goto('/implementation/new');
    
    // Upload file with errors
    await page.click('text=Upload Account Data');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-data/accounts-with-errors.xlsx');
    
    await page.click('button:has-text("Upload")');
    await page.click('button:has-text("Validate")');
    
    // Should show validation errors
    await expect(page.locator('.validation-status')).toHaveText('Failed');
    await expect(page.locator('.error-count')).toHaveText('5 errors found');
    
    // View error details
    await page.click('text=View Details');
    await expect(page.locator('.error-list')).toBeVisible();
    await expect(page.locator('.error-item').first()).toContainText('Row 10: Name is required');
    
    // Download error report
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button:has-text("Download Error Report")')
    ]);
    expect(download.suggestedFilename()).toBe('validation-errors.xlsx');
  });

  test('save and resume progress', async ({ page }) => {
    await page.goto('/implementation/new');
    
    // Complete partial phase
    await page.click('text=Upload Account Data');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-data/accounts.xlsx');
    await page.click('button:has-text("Process")');
    
    // Save progress
    await page.click('button:has-text("Save Progress")');
    await expect(page.locator('.save-status')).toHaveText('Progress saved');
    
    // Navigate away
    await page.goto('/dashboard');
    
    // Return to implementation
    await page.click('text=Continue Implementation');
    
    // Should restore previous progress
    await expect(page.locator('.task-account')).toHaveClass(/completed/);
    await expect(page.locator('.task-contact')).not.toHaveClass(/completed/);
  });
});
```

```javascript
// tests/e2e/data-management.spec.js
import { test, expect } from '@playwright/test';

test.describe('Data Management', () => {
  test('search and filter objects', async ({ page }) => {
    await page.goto('/data-management');
    
    // Search for product
    await page.fill('input[placeholder="Search objects..."]', 'product');
    
    // Should filter results
    await expect(page.locator('.object-card')).toHaveCount(5);
    await expect(page.locator('.object-card').first()).toContainText('Product2');
    
    // Apply category filter
    await page.click('text=Filter by Category');
    await page.click('text=Core Product Objects');
    
    // Should show only product objects
    await expect(page.locator('.object-card')).toHaveCount(8);
  });

  test('bulk sync operation', async ({ page }) => {
    await page.goto('/data-management');
    
    // Select multiple objects
    await page.click('input[data-object="Product2"]');
    await page.click('input[data-object="Pricebook2"]');
    await page.click('input[data-object="PricebookEntry"]');
    
    // Bulk sync
    await page.click('button:has-text("Sync Selected")');
    
    // Confirm dialog
    await expect(page.locator('.confirm-dialog')).toContainText('Sync 3 objects?');
    await page.click('button:has-text("Confirm")');
    
    // Monitor progress
    await expect(page.locator('.sync-modal')).toBeVisible();
    await expect(page.locator('.sync-progress')).toHaveAttribute('value', '100');
    
    // Check results
    await expect(page.locator('.sync-summary')).toContainText('3 objects synced successfully');
  });
});
```

## 7. Performance Test Scripts

```python
# tests/performance/test_load.py
import pytest
from locust import HttpUser, task, between
import pandas as pd
import io

class MigrationToolUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "username": "loadtest@example.com",
            "password": "loadtest123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/dashboard", headers=self.headers)
    
    @task(2)
    def list_objects(self):
        self.client.get("/api/data/objects", headers=self.headers)
    
    @task(1)
    def upload_small_file(self):
        # Create small Excel file (1000 records)
        df = pd.DataFrame({
            'Name': [f'Product {i}' for i in range(1000)],
            'ProductCode': [f'P{i:04d}' for i in range(1000)],
            'Price': [100.00 + i for i in range(1000)]
        })
        
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        
        files = {'file': ('products.xlsx', buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        self.client.post("/api/data/upload", files=files, headers=self.headers)

class HeavyUser(HttpUser):
    wait_time = between(5, 10)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "username": "heavyuser@example.com",
            "password": "heavyuser123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def upload_large_file(self):
        # Create large Excel file (100k records)
        df = pd.DataFrame({
            'Name': [f'Product {i}' for i in range(100000)],
            'ProductCode': [f'P{i:06d}' for i in range(100000)],
            'Price': [100.00 + (i % 1000) for i in range(100000)],
            'Description': [f'Description for product {i}' * 10 for i in range(100000)]
        })
        
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        
        files = {'file': ('large_products.xlsx', buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        with self.client.post(
            "/api/data/upload", 
            files=files, 
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 30:
                response.failure("Upload took longer than 30 seconds")
```

## 8. Security Test Scripts

```python
# tests/security/test_security.py
import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

class TestSecurity:
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM products WHERE '1'='1"
        ]
        
        for payload in malicious_inputs:
            response = client.get(
                f"/api/data/search?q={payload}",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should not execute SQL
            assert response.status_code in [200, 400]
            assert "error" not in response.json()
    
    def test_xss_prevention(self, client, auth_headers):
        """Test XSS prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'>"
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/data/upload",
                json={"name": payload, "description": payload},
                headers=auth_headers
            )
            
            # Check response doesn't contain unescaped script
            response_text = response.text
            assert "<script>" not in response_text
            assert "javascript:" not in response_text
    
    def test_authentication_required(self, client):
        """Test endpoints require authentication"""
        protected_endpoints = [
            "/api/dashboard",
            "/api/data/objects",
            "/api/data/upload",
            "/api/migrations"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            assert response.json()["detail"] == "Not authenticated"
    
    def test_jwt_token_validation(self, client):
        """Test JWT token validation"""
        # Expired token
        expired_token = jwt.encode(
            {"exp": datetime.utcnow() - timedelta(hours=1), "sub": "user@example.com"},
            "secret_key",
            algorithm="HS256"
        )
        
        response = client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        
        # Invalid signature
        invalid_token = jwt.encode(
            {"exp": datetime.utcnow() + timedelta(hours=1), "sub": "user@example.com"},
            "wrong_secret",
            algorithm="HS256"
        )
        
        response = client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == 401
    
    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting"""
        # Make multiple rapid requests
        for i in range(100):
            response = client.get("/api/data/objects", headers=auth_headers)
            
            if response.status_code == 429:
                # Rate limit hit
                assert response.json()["detail"] == "Too many requests"
                assert "Retry-After" in response.headers
                break
        else:
            pytest.fail("Rate limiting not enforced")
    
    def test_file_upload_security(self, client, auth_headers):
        """Test file upload security"""
        # Test malicious file types
        dangerous_files = [
            ("malware.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("script.js", b"alert('XSS')", "application/javascript"),
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php")
        ]
        
        for filename, content, content_type in dangerous_files:
            response = client.post(
                "/api/data/upload",
                files={"file": (filename, content, content_type)},
                headers=auth_headers
            )
            
            assert response.status_code == 400
            assert "Invalid file type" in response.json()["detail"]
```

## 9. Test Data Management

### Test Data Sets

```python
# tests/fixtures/test_data.py
import pandas as pd
from faker import Faker
import random

fake = Faker()

def generate_test_accounts(count=100):
    """Generate test account data"""
    return pd.DataFrame({
        'Name': [fake.company() for _ in range(count)],
        'Type': [random.choice(['Customer', 'Partner', 'Prospect']) for _ in range(count)],
        'Industry': [fake.bs() for _ in range(count)],
        'AnnualRevenue': [random.randint(100000, 10000000) for _ in range(count)],
        'NumberOfEmployees': [random.randint(10, 10000) for _ in range(count)],
        'BillingStreet': [fake.street_address() for _ in range(count)],
        'BillingCity': [fake.city() for _ in range(count)],
        'BillingState': [fake.state_abbr() for _ in range(count)],
        'BillingPostalCode': [fake.zipcode() for _ in range(count)],
        'BillingCountry': ['USA' for _ in range(count)]
    })

def generate_test_products(count=1000):
    """Generate test product data"""
    categories = ['Hardware', 'Software', 'Services', 'Support']
    
    return pd.DataFrame({
        'Name': [f"{fake.catch_phrase()} {random.choice(['Pro', 'Enterprise', 'Basic'])}" for _ in range(count)],
        'ProductCode': [f"P{i:06d}" for i in range(count)],
        'Description': [fake.text(max_nb_chars=200) for _ in range(count)],
        'Family': [random.choice(categories) for _ in range(count)],
        'IsActive': [random.choice([True, True, True, False]) for _ in range(count)],  # 75% active
        'QuantityUnitOfMeasure': [random.choice(['Each', 'License', 'User', 'GB']) for _ in range(count)]
    })

def generate_test_data_with_errors(df, error_rate=0.1):
    """Introduce errors into test data"""
    error_count = int(len(df) * error_rate)
    error_indices = random.sample(range(len(df)), error_count)
    
    for idx in error_indices:
        error_type = random.choice(['missing', 'invalid', 'duplicate'])
        
        if error_type == 'missing':
            # Remove required field
            col = random.choice(['Name', 'ProductCode'])
            df.loc[idx, col] = None
        
        elif error_type == 'invalid':
            # Invalid data type
            if 'Price' in df.columns:
                df.loc[idx, 'Price'] = 'invalid'
            elif 'IsActive' in df.columns:
                df.loc[idx, 'IsActive'] = 'maybe'
        
        elif error_type == 'duplicate':
            # Duplicate unique field
            if idx > 0:
                df.loc[idx, 'ProductCode'] = df.loc[idx-1, 'ProductCode']
    
    return df
```

## 10. Test Automation & CI/CD

### GitHub Actions Test Pipeline

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9]
        node-version: [14.x, 16.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Set up Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/pip
          node_modules
        key: ${{ runner.os }}-deps-${{ hashFiles('**/requirements.txt', '**/package-lock.json') }}
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Install Node dependencies
      run: npm ci
    
    - name: Run Python unit tests
      run: |
        pytest tests/unit -v --cov=app --cov-report=xml
    
    - name: Run JavaScript unit tests
      run: |
        npm test -- --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml,./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost/testdb
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build application
      run: |
        docker-compose build
    
    - name: Start services
      run: |
        docker-compose up -d
        sleep 10  # Wait for services to start
    
    - name: Run E2E tests
      run: |
        npx playwright install
        npx playwright test
    
    - name: Upload test artifacts
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: playwright-report/

  security-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: zaproxy/action-full-scan@v0.4.0
      with:
        target: 'http://localhost:8000'
    
    - name: Run dependency check
      run: |
        pip install safety
        safety check
    
    - name: Run SAST scan
      uses: AppThreat/sast-scan-action@master
      with:
        type: "python,javascript"

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run performance tests
      run: |
        pip install locust
        docker-compose up -d
        sleep 10
        locust -f tests/performance/test_load.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000
```

## 11. Test Reporting

### Test Report Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - Revenue Cloud Migration Tool</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Test Run: {{ timestamp }}</p>
        <p>Duration: {{ duration }}</p>
        <p>
            Total: {{ total_tests }} | 
            <span class="passed">Passed: {{ passed_tests }}</span> | 
            <span class="failed">Failed: {{ failed_tests }}</span> | 
            <span class="skipped">Skipped: {{ skipped_tests }}</span>
        </p>
        <p>Coverage: {{ coverage_percent }}%</p>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test Suite</th>
                <th>Test Case</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
            {% for test in tests %}
            <tr>
                <td>{{ test.suite }}</td>
                <td>{{ test.name }}</td>
                <td class="{{ test.status }}">{{ test.status }}</td>
                <td>{{ test.duration }}s</td>
                <td>{{ test.error }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Coverage Report</h2>
    <table>
        <thead>
            <tr>
                <th>Module</th>
                <th>Statements</th>
                <th>Missing</th>
                <th>Coverage</th>
            </tr>
        </thead>
        <tbody>
            {% for module in coverage %}
            <tr>
                <td>{{ module.name }}</td>
                <td>{{ module.statements }}</td>
                <td>{{ module.missing }}</td>
                <td>{{ module.percent }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
```

## 12. Test Maintenance

### Test Review Checklist

- [ ] Tests follow naming conventions
- [ ] Tests are independent and can run in any order
- [ ] Tests clean up after themselves
- [ ] Tests use appropriate fixtures
- [ ] Tests have clear assertions
- [ ] Tests cover positive and negative cases
- [ ] Tests are maintainable and readable
- [ ] Tests run in reasonable time
- [ ] Tests are properly categorized
- [ ] Test documentation is up to date