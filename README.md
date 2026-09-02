# kawa
Coding Agent

## Basic Harness Example

Run the deterministic example without an API key:

```bash
uv run python -m examples.basic_harness
```

It uses a fake Provider that first requests the `echo` tool and then returns a
final answer. The example demonstrates the Harness event stream:

```python
async for event in harness.prompt("use the echo tool"):
    print(event)
```
