# Copilot Instructions

## Code Philosophy

Write clean, self-documenting code following Robert C. Martin's Clean Code principles. Clarity over comments.

## Core Principles

### Self-Explanatory Code

- Descriptive names that reveal intent; small, single-responsibility functions
- Comments only for complex business logic ("why", never "what")

### Type Safety

- Always use type hints; Pydantic models for validation
- Prefer explicit types — `Any` only when truly unavoidable

### Testable Design

- Dependency injection for external dependencies
- Pure functions where possible; separate business logic from I/O

### Modern Python Patterns

- `async/await` for I/O; context managers for lifecycle
- Composition over inheritance; Pydantic/dataclasses over dicts

### Code Structure

- Modules organized by domain/feature
- Max 2–3 levels of nesting; one abstraction level per function
- Named constants for magic values

## Example

```python
# Query - returns data
async def fetch_light_state(self, light_id: str) -> LightState:
    response = await self._client.get(f"lights/{light_id}")
    return LightState.model_validate(response)

# Command - changes state, returns None
async def turn_on_light(self, light_id: str) -> None:
    await self._client.post(f"lights/{light_id}/on")
```
