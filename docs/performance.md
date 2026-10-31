# Performance checks

The performance follow-up keeps the existing request and event interfaces and
makes three small changes:

- Validate response JSON directly with Pydantic instead of first building a
  separate Python JSON tree.
- Reuse the write-response, mixed-resource and raw-resource validators.
- Return immediately when an event has no matching or wildcard subscribers.

Name lookup scans all names to detect duplicate exact matches and tied fuzzy
matches. It supports `fuzzy=False` and scoped scene lookup. Returning the first
exact match would silently select an ambiguous resource.

Successful HTTP responses containing malformed JSON or invalid resource data
raise `pydantic.ValidationError`. HTTP status errors are raised before parsing
the response body, including when an error response is not JSON.

## Reproduce the local measurements

```bash
uv run python benchmarks/clip_v2.py
```

The [benchmark](../benchmarks/clip_v2.py) uses in-memory HTTP responses and
requires no bridge or credentials. It reports the median of five samples.
The fixture contains 200 lights. Registry construction registers one namespace;
the raw-namespace and event measurements contain no HTTP work.

Selected measurements on Windows with Python 3.13.8, comparing the model
reorganization commit `b501e38` with the performance changes:

| Operation | Before | After |
| --- | ---: | ---: |
| Event without subscribers | 1.64 us | 0.20 us |
| Resource registry construction | 20.12 us | 0.23 us |
| Raw namespace construction | 10.29 us | 0.46 us |
| Parse 200 lights: peak traced Python allocations | 1317.6 KiB | 998.0 KiB |

The allocation comparison checks the old and new parsing paths in the same
process with `tracemalloc`. It measures Python allocations, not total process
memory. JSON parsing timings varied between runs, so no fixed parsing speedup
is claimed. These local operation costs do not predict network latency or
end-to-end bridge performance.
