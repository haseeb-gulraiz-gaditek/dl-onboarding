# STD-001 Templates Reference

Full templates for Spec-Driven Development artifacts. Copy and fill in for each change.

---

## proposal.md

```markdown
# Proposal: [Change Name]

**Author:** [Name]
**Date:** [YYYY-MM-DD]
**Status:** Draft | Review | Approved | Rejected

## Problem

[Describe the problem or gap. Include specific user-facing symptoms, metrics, or error reports that motivate this change.]

## Solution

[Describe the proposed solution at a high level. What will the system do differently after this change?]

## Scope

### Affected Features
- [feature-1]: [brief description of impact]
- [feature-2]: [brief description of impact]

### Affected Specs
- `specs/features/[feature]/spec.md`: [what changes]

### Out of Scope
- [Explicitly list what this proposal does NOT cover]

## Alternatives Considered

### Alternative 1: [Name]
- **Pros:** [advantages]
- **Cons:** [disadvantages]
- **Why not:** [reason for rejection]

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk description] | Low/Med/High | Low/Med/High | [How to mitigate] |

## Rollback Plan

[How to revert this change if something goes wrong]

## Dependencies

- [External services, libraries, or other proposals this depends on]
```

---

## spec-delta.md

```markdown
# Spec Delta: [Change Name]

**Proposal:** [Link to proposal.md]
**Target Spec:** `specs/features/[feature]/spec.md`

## ADDED

### [New Capability Name]

**Description:** [What new behavior is being added]

#### Scenarios

Given [precondition]
When [action]
Then [expected outcome]

Given [precondition]
When [error condition]
Then [error handling behavior]

### [Another New Capability]

...

## MODIFIED

### [Existing Capability Name]

**Reason for change:** [Why this behavior is changing]

#### Before
Given [precondition]
When [action]
Then [old outcome]

#### After
Given [precondition]
When [action]
Then [new outcome]

## REMOVED

### [Removed Capability Name]

**Reason for removal:** [Why this behavior is being removed]

#### Previous Behavior
Given [precondition]
When [action]
Then [behavior that will no longer exist]

#### Migration
[How users/systems should adapt to this removal]
```

---

## tasks.md

```markdown
# Tasks: [Change Name]

**Proposal:** [Link to proposal.md]
**Spec Delta:** [Link to spec-delta.md]

## Pre-Implementation
- [ ] Proposal reviewed and approved
- [ ] Spec-delta reviewed and approved
- [ ] Commit spec artifacts with `[spec]` prefix

## Implementation
- [ ] [Specific implementation task 1]
- [ ] [Specific implementation task 2]
- [ ] [Specific implementation task 3]
- [ ] Commit implementation with `[impl]` prefix

## Verification
- [ ] All new scenarios have corresponding tests
- [ ] All modified scenarios have updated tests
- [ ] Error cases are tested
- [ ] Existing tests still pass
- [ ] Manual verification of key scenarios

## Post-Merge
- [ ] Move `changes/[change-name]/` to `archive/[change-name]/`
- [ ] Merge spec-delta into `specs/features/[feature]/spec.md`
- [ ] Commit archive with `[archive]` prefix
```

---

## spec.md (Feature Specification)

```markdown
# [Feature Name] Specification

**Last Updated:** [YYYY-MM-DD]
**Owner:** [Team or person]

## Overview

[One paragraph describing what this feature does]

## Requirements

### [Requirement 1 Name]

[Brief description]

#### Scenarios

Given [precondition]
When [action]
Then [expected outcome]

Given [precondition]
When [error condition]
Then [error handling behavior]

### [Requirement 2 Name]

...

## Constraints

- [Performance requirements]
- [Security requirements]
- [Compatibility requirements]

## Dependencies

- [Other features or services this depends on]
```

---

## constitution.md

```markdown
# [Project Name] Constitution

**Established:** [YYYY-MM-DD]
**Last Amended:** [YYYY-MM-DD]

## Principles

1. **[Principle Name]:** [Description of the immutable principle]
2. **[Principle Name]:** [Description]

## Boundaries

- [Hard constraints that must never be violated]
- [Security invariants]
- [Data integrity rules]

## Amendment Process

Changes to this constitution require:
- [ ] Written proposal with rationale
- [ ] Team-wide review
- [ ] Unanimous approval from [decision makers]
```
