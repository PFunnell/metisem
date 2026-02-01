# Code Review Checklist

Standards for reviewing and approving pull requests.

## Self-Review (Before Requesting)

Complete before marking PR as ready:

### Code Quality
- [ ] No commented-out code
- [ ] No debug statements (console.log, print, etc.)
- [ ] No hardcoded values that should be config
- [ ] Variable names are clear and consistent
- [ ] Functions are focused and reasonably sized

### Testing
- [ ] Tests pass locally
- [ ] New code has appropriate test coverage
- [ ] Edge cases are handled
- [ ] Error paths are tested

### Documentation
- [ ] Complex logic has explanatory comments
- [ ] Public APIs have documentation
- [ ] README updated if behavior changed
- [ ] Data dictionary updated if models changed

### Security
- [ ] No credentials in code
- [ ] Input validation present where needed
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities (if web)

## Reviewer Checklist

When reviewing others' PRs:

### Understanding
- [ ] I understand what this PR is trying to accomplish
- [ ] The PR description explains the "why"
- [ ] Changes align with the linked plan (if any)

### Correctness
- [ ] Logic appears correct
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs

### Design
- [ ] Approach is reasonable for the problem
- [ ] Code fits with existing patterns
- [ ] No unnecessary complexity
- [ ] Changes are focused (not mixing concerns)

### Maintainability
- [ ] Code is readable
- [ ] Would I understand this in 6 months?
- [ ] Tests make behavior clear
- [ ] No magic numbers without explanation

## Common Issues to Watch For

### Performance
- N+1 queries in database code
- Unnecessary re-renders in UI code
- Missing indexes for frequent queries
- Large objects in memory unnecessarily

### Security
- User input used without sanitization
- Authentication/authorization gaps
- Sensitive data in logs
- Insecure defaults

### Reliability
- Missing error handling
- Race conditions
- Resource leaks (connections, files)
- Missing null checks

## Approval Criteria

Approve when:
- All checklist items pass
- No blocking concerns
- Minor issues can be addressed in follow-up

Request changes when:
- Security vulnerability present
- Logic error that would cause bugs
- Missing critical test coverage
- Significant design concern

Comment without blocking when:
- Style preferences (not blocking)
- Suggestions for future improvement
- Questions that don't block merge

## Review Etiquette

- Be constructive, not critical
- Explain the "why" behind suggestions
- Offer alternatives, not just problems
- Acknowledge good patterns you see
- Use questions to understand, not to challenge
