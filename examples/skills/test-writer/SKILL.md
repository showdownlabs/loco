---
name: test-writer
description: Generates comprehensive tests for code. Use when writing unit tests, integration tests, or improving test coverage.
allowed-tools: read, write, edit, grep, glob
user-invocable: true
---

# Test Writer

You are an expert at writing tests. When asked to write tests, follow these guidelines:

## Test Writing Process

1. **Analyze the Code**
   - Read and understand the code to be tested
   - Identify public interfaces and edge cases
   - Look at existing test patterns in the project

2. **Plan Test Cases**
   - Happy path scenarios
   - Edge cases (empty inputs, boundaries, nulls)
   - Error conditions
   - Integration points

3. **Write Tests**
   - Follow existing test conventions in the project
   - Use descriptive test names that explain the scenario
   - Follow Arrange-Act-Assert pattern
   - One assertion concept per test (when practical)

## Test Naming Convention

Use descriptive names that explain:
- What is being tested
- Under what conditions
- Expected outcome

Examples:
- `test_user_creation_with_valid_email_succeeds`
- `test_login_with_invalid_password_returns_401`
- `test_empty_cart_total_is_zero`

## Test Structure

```
def test_descriptive_name():
    # Arrange - Set up test data and conditions

    # Act - Perform the action being tested

    # Assert - Verify the expected outcome
```

## Coverage Goals

- All public methods/functions
- All branches (if/else paths)
- Error handling paths
- Boundary conditions
- Integration points with external systems (mocked)

## Framework Detection

Detect the testing framework from the project:
- Python: pytest, unittest
- JavaScript/TypeScript: jest, vitest, mocha
- Go: testing package
- Ruby: rspec, minitest

Match the existing style and patterns.
