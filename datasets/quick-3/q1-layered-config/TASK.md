# Implement layered configuration resolution

Repair `configmerge.resolve(*layers)` without changing its public API. Layers are applied from lowest to highest precedence.

## Required behavior

- Every layer must be a dictionary. Calling `resolve()` with no layers returns `{}`.
- Merge dictionaries recursively. When both the existing and higher-precedence values are dictionaries, merge their children.
- Any other higher-precedence value replaces the lower value, including lists and scalar values.
- `None` is a deletion marker: it removes that key from the accumulated result. Deleting an absent key is a no-op.
- Every dictionary key, including nested keys, must be a non-empty string. Values may contain only dictionaries, lists, strings, numbers, booleans, and `None`; otherwise raise `ConfigError`.
- Validation covers values nested inside lists as well as dictionaries.
- Do not mutate a supplied layer or share mutable dictionaries/lists with the returned result.
- Repeated calls with the same inputs must return equal results.

Use only Python 3.11+ standard-library modules. Do not modify the public tests.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```
