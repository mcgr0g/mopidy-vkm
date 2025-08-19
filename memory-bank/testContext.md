# Test Context

## Test Structure and Organization

The project follows a structured approach to testing with a focus on unit tests and mocking external dependencies:

### Unit Test Organization

1. **Test File Structure**
   - Tests are organized in the `tests/` directory
   - Test files follow the naming convention `test_*.py`
   - Each module has a corresponding test file (e.g., `auth.py` → `test_auth.py`)

2. **Test Class Structure**
   - Tests use Python's `unittest` framework
   - Each test class inherits from `unittest.TestCase`
   - Test methods follow the naming convention `test_*`
   - Setup and teardown methods (`setUp`, `tearDown`) are used for test initialization and cleanup

3. **Test Method Organization**
   - Each test method focuses on a single functionality or scenario
   - Test methods have descriptive names that explain what they test
   - Tests are organized from simple to complex scenarios

## Mocking Strategy

The project uses the `unittest.mock` module for mocking external dependencies:

1. **Mock Objects**
   - `MagicMock` is used for creating mock objects
   - Mock objects are configured with appropriate return values and side effects
   - `patch` decorator/context manager is used for replacing classes and functions

2. **External Dependencies**
   - VK API dependencies (`vkpymusic`) are mocked to avoid actual API calls
   - File system operations are mocked or use temporary directories
   - Network operations are mocked to avoid actual network calls

3. **Mock Configuration**
   - Mocks are configured with appropriate return values
   - Side effects are used for simulating errors and exceptions
   - Mock assertions are used to verify that methods were called with expected arguments

## Test Coverage Goals

The project aims for comprehensive test coverage:

1. **Coverage Targets**
   - Minimum 60% overall test coverage
   - Critical paths (authentication, credential handling) should have >80% coverage
   - All public APIs should be tested

2. **Coverage Measurement**
   - Coverage is measured using pytest-cov
   - Coverage reports are generated during CI runs
   - Coverage gaps are identified and addressed in subsequent iterations

## Type Checking in Tests

1. **Type Annotations**
   - All test methods include return type annotations (`-> None`)
   - Mock objects are properly typed with appropriate specs
   - Type checking is enforced in CI pipeline

2. **Type Checking Exceptions**
   - In test code, some type checking rules may be relaxed with appropriate comments
   - When mocking complex objects, `# type: ignore` comments are used with specific error codes

## Manual End-to-End Testing

For complete system validation, manual E2E testing is required:

1. **E2E Test with Real VK Account**
   - Place test account credentials in root `.env` file:
     - `TEST_USER_LOGIN`
     - `TEST_USER_PASSWORD`
   - Start the Mopidy server with the VKM extension
   - Open `/vkm` in a browser
   - Enter credentials from `.env` (manually or via test harness)
   - Complete captcha or 2FA if prompted
   - Verify `/vkm/auth/status` transitions to `success`
   - Verify VK library is accessible and playback works

2. **Testing Authentication Flows**
   - Test normal login flow
   - Test captcha challenge flow
   - Test 2FA challenge flow
   - Test error handling (invalid credentials, network errors)
   - Test token refresh flow

3. **Security Testing**
   - Verify credentials are stored securely
   - Verify sensitive data is not exposed in logs
   - Verify proper error handling for security-related operations

## Test Execution

All tests must be run using the project's environment via uv:

```bash
uv run pytest tests/ -v
```

This ensures correct tool versions and consistent dependency resolution.
