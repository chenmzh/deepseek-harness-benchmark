# Repair the inventory reservation service

The service in this repository reserves stock and cancels reservations using a JSON-backed store. Repair it without changing the public `InventoryService` API.

## Required behavior

- `reserve(sku, quantity, request_id)` creates at most one reservation for a successful request ID.
- Repeating a successful request returns exactly the original result and never removes stock twice.
- An unsuccessful reserve attempt must not permanently consume its request ID. It may succeed later after stock becomes available.
- `cancel(reservation_id, request_id)` is idempotent by both cancellation request ID and reservation state. Stock may be restored at most once.
- Unknown reservations raise `ReservationNotFound`; invalid quantities raise `ValueError`.
- State must survive constructing a new `InventoryService` for the same database path.
- Every persisted state must preserve `available + active_reserved == initial_stock` for each SKU.
- Persistence must replace the previous JSON state atomically. A failed write must not expose a partially written database.

Keep the project dependency-free and compatible with Python 3.11 or newer. Do not alter the public tests or replace the JSON store with an external service.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```

Implement the repair, run relevant checks, and briefly report what changed and what you verified.
