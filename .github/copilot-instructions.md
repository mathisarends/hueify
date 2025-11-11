# Copilot Instructions

## Code Philosophy

Write clean, self-documenting code that follows Robert C. Martin's Clean Code principles. Prioritize code clarity over comments.

## Core Principles

### Self-Explanatory Code
- Use descriptive variable and function names that reveal intent
- Keep functions small and focused (single responsibility)
- Avoid comments by making code self-explanatory
- Only add comments for complex business logic or "why" explanations, never "what"

### Type Safety
- Always use type hints for function parameters and return values
- Use Pydantic models for data validation
- Prefer explicit types over `Any` where possible
- Use `dict[str, Any]` only when truly necessary

### Command-Query Separation (CQS)
- **Commands** (operations that change state) should return `None`
- **Queries** (operations that retrieve data) should return values
- Never mix commands and queries in the same function
- A function either changes state OR returns data, not both
- This makes side effects explicit and testing easier

### Testable Design
- Write code with testing in mind from the start
- Use dependency injection for external dependencies
- Keep functions pure when possible (no side effects)
- Separate business logic from I/O operations
- Design for mockability

### Modern Python Patterns
- Use async/await for I/O operations
- Leverage context managers (`__aenter__`, `__aexit__`)
- Prefer composition over inheritance
- Use dataclasses or Pydantic models over dictionaries
- Follow Python naming conventions (snake_case for functions/variables)

### Code Structure
- Keep modules focused and cohesive
- Organize code by domain/feature, not by type
- Extract magic numbers and strings into named constants
- Avoid deep nesting (max 2-3 levels)
- One level of abstraction per function

## Testing
- Every public function should be easily testable
- Avoid tight coupling to external systems
- Use protocols/interfaces for abstraction
- Design for pytest compatibility

## What to Avoid
- Large functions (>20 lines usually indicates need for extraction)
- Unclear variable names (e.g., `data`, `temp`, `x`)
- Comments that explain what the code does
- Mutable default arguments
- Global state
- God classes/objects
- Mixing commands and queries (violating CQS)

## Example Good Code
```python
# Query - returns data
async def fetch_light_state(self, light_id: str) -> LightState:
    response = await self._client.get(f"lights/{light_id}")
    return LightState.model_validate(response)

# Command - changes state, returns None
async def turn_on_light(self, light_id: str) -> None:
    await self._client.post(f"lights/{light_id}/on")
```

## Example Bad Code
```python
async def get_data(self, id: str) -> dict:
    # Get the light state from the API
    resp = await self._client.get(f"lights/{id}")  # Call API
    return resp  # Return response

# Bad - mixing command and query
async def update_and_get_light(self, light_id: str, state: bool) -> LightState:
    await self._client.post(f"lights/{light_id}", {"on": state})
    return await self.fetch_light_state(light_id)  # Don't do this!
```

---

When in doubt: **Can someone understand what this code does without comments? Can it be easily tested? Does this function either change state OR return data, but not both?**