# PLAN.md Optimization Guidelines

Principles and patterns for creating effective project plans.

## Plan Structure

A good PLAN.md should be:

### 1. Clear and Actionable

**Vague:**
```
- Fix bugs
- Add features
```

**Clear:**
```
- Fix authentication timeout issue when session expires after 1 hour
- Add password reset flow with email verification
```

### 2. Properly Scoped

**Too Large:**
```
- Build the entire e-commerce platform
```

**Properly Scoped:**
```
- Design database schema for products and orders
- Implement product listing API endpoint
- Create shopping cart UI component
```

### 3. With Dependencies

```
- Set up project structure and dependencies
- Implement database models and migrations
- Create API endpoints for CRUD operations
- Build frontend components for data display
```

Dependencies: Each step builds on the previous.

## Task Conversion

Convert plan items to TaskCreate format:

### From PLAN.md:
```
- Implement user authentication with JWT
```

### To TaskCreate:
```python
TaskCreate(
  subject="Implement user authentication with JWT",
  description="Create authentication system including:
  - User registration endpoint
  - Login endpoint with JWT token generation
  - Token validation middleware
  - Password hashing with bcrypt
  Acceptance criteria: Users can register, login, and access protected routes",
  activeForm="Implementing user authentication"
)
```

## Optimization Checklist

When optimizing PLAN.md:

- [ ] Are tasks specific and actionable?
- [ ] Is scope appropriate (not too large/small)?
- [ ] Are dependencies clearly identified?
- [ ] Is there acceptance criteria for each task?
- [ ] Are tasks ordered logically?
- [ ] Is technical context provided?
- [ ] Are testing requirements mentioned?

## Common PLAN.md Patterns

### Feature Development
```
## Feature: [Name]

### Tasks
- Design and document the feature spec
- Implement core functionality
- Add unit tests
- Integration testing
- Documentation and examples
```

### Bug Fixing
```
## Bug: [Description]

### Tasks
- Reproduce and isolate the bug
- Identify root cause
- Implement fix
- Add regression test
- Verify fix and deploy
```

### Refactoring
```
## Refactor: [Component]

### Tasks
- Analyze current implementation
- Design new structure
- Incrementally refactor with tests
- Update documentation
- Verify no behavioral changes
```
