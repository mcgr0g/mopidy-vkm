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
     - `VK_TEST_LOGIN`
     - `VK_TEST_PASSWORD`
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
````

This ensures correct tool versions and consistent dependency resolution.

## Playwright Browser Configuration

Check you a in dev container: for devcontainer `pwd` will be equal `/workspace`. For work in host - use default configuration. For work in devcontaier - use additional instructions:

- To ensure Playwright finds browsers correctly, see the environment variable `echo $PLAYWRIGHT_BROWSERS_PATH`.
- Verify location with: `ls -la $PLAYWRIGHT_BROWSERS_PATH/chromium-1179/chrome-linux/chrome`

---

# Environment Validation

## Basic Health Checks

### 1. Extension Loading Validation

```bash
# Check if VKM extension is properly discovered
/home/mopidy/.venv/bin/mopidy list | grep -A 5 -B 5 vkm

# Verify extension configuration
/home/mopidy/.venv/bin/mopidy config | grep -A 10 "[vkm]"

# Check for extension loading errors
/home/mopidy/.venv/bin/mopidy --config /workspace/mopidy.conf 2>&1 | grep -i error
```

### 2. HTTP Server Validation

```bash
# Check if port 6680 is bound
netstat -tlnp | grep 6680

# Test basic HTTP response
curl --max-time 5 -I http://localhost:6680/

# Test Mopidy RPC endpoint
curl --max-time 5 http://localhost:6680/mopidy/rpc -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "core.get_uri_schemes"}'
```

### 3. VKM Routes Validation

```bash
# Test VKM status endpoint
curl --max-time 5 http://localhost:6680/vkm/auth/status

# Test VKM main endpoint
curl --max-time 5 http://localhost:6680/vkm

# Check for VKM route registration
curl --max-time 5 http://localhost:6680/mopidy/rpc -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "core.get_uri_schemes"}' | grep vkm
```

---

# Service Startup & Validation

## Expected Startup Sequence

1. __Configuration Loading__: Mopidy loads configuration files
2. __Extension Discovery__: Mopidy discovers available extensions
3. __Backend Initialization__: Each extension's backend is initialized
4. __HTTP Server Setup__: HTTP server starts and binds to configured port
5. __Route Registration__: Web endpoints are registered

## Validation Commands

```bash
# 1. Check Mopidy process
ps aux | grep mopidy | grep -v grep

# 2. Verify HTTP server is listening
netstat -tlnp | grep 6680

# 3. Test HTTP functionality
curl --max-time 5 -v http://localhost:6680/mopidy/rpc -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "core.get_uri_schemes"}'

# 4. Check VKM extension status
curl --max-time 5 http://localhost:6680/vkm/auth/status

# 5. Verify VKM routes are registered
curl --max-time 5 http://localhost:6680/vkm
```

## Common Issues and Solutions

### Issue: HTTP Requests Timeout

__Symptoms__: curl: (28) Operation timed out __Causes__:

- Pykka actors deadlocked
- HTTP server not responding __Solutions__:
- Restart Mopidy service
- Check for actor deadlock logs
- Use minimal configuration to isolate

### Issue: VKM Extension Not Loading

__Symptoms__: Extension not in `mopidy list` output __Causes__:

- Missing dependencies
- Configuration errors
- Import errors __Solutions__:
- Check mopidy logs for errors
- Verify vkpymusic installation
- Validate configuration syntax

---

# Troubleshooting Guide

## Current Known Issues (Session 2025-11-14)

### 1. HTTP Server Deadlock

__Symptom__: Port 6680 bound but all HTTP requests timeout __Logs__: `CRITICAL pykka Current state of HttpFrontend-8 (_actor_loop): queue.get()` __Status__: Reproducible across multiple restarts __Workaround__: None currently __Next Steps__:

- Investigate Pykka actor initialization
- Check for circular dependencies in VKM extension
- Test with minimal configuration

### 2. VKM Backend Not Loading

__Symptom__: "Stopping 0 instance(s) of VKMBackend" __Logs__: Extension enabled but backend count is 0 __Status__: Extension discovered but backend fails to initialize __Workaround__: None currently __Next Steps__:

- Debug VKMBackend class instantiation
- Check for missing dependencies in backend.py
- Verify backend registration in extension setup

### 3. Configuration Issues

__Status__: Mostly resolved __Fixed__:

- ✅ Removed unknown 'quality' config key
- ✅ VKM extension now appears as enabled
- ✅ Extension discovery works properly

## Diagnostic Commands

```bash
# Quick health check
ps aux | grep mopidy | grep -v grep && \
netstat -tlnp | grep 6680 && \
curl --max-time 5 http://localhost:6680/mopidy/rpc -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "core.get_uri_schemes"}'

# Check VKM extension status
/home/mopidy/.venv/bin/mopidy config | grep -A 10 "[vkm]" && \
/home/mopidy/.venv/bin/mopidy list | grep vkm

# Debug actor deadlock (send to running mopidy process)
kill -USR1 $(pgrep mopidy)

# Test with minimal configuration
cat > /tmp/minimal.conf << 'EOF'
[core]
cache_dir = /tmp/mopidy-cache
config_dir = /tmp/mopidy-config

[http]
enabled = true
hostname = 0.0.0.0
port = 6680

[file]
enabled = true

[vkm]
enabled = true
EOF

/home/mopidy/.venv/bin/mopidy --config /tmp/minimal.conf
```
