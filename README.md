# PostgreSQL B-Tree Index Fragmentation: UUIDv4 vs. UUIDv7

A containerized benchmark measuring how random (`UUIDv4`) versus time-ordered (`UUIDv7`) primary keys affect PostgreSQL B-Tree index size and insertion throughput across **5,000,000 rows**.

## Benchmark Results (5M Rows)

| Metric | UUIDv4 (Random) | UUIDv7 (Time-Ordered) | Difference |
| :--- | :--- | :--- | :--- |
| **Total Insert Time** | `100.48s` | `62.32s` | `-37.98%` (`-38.16s`) |
| **Insert Throughput** | `49,760.04 rows/s` | `80,225.83 rows/s` | `+61.23%` |
| **Index Size** | `191 MB` | `150 MB` | `-21.47%` (`-41 MB`) |

## Why UUID Key Ordering Matters in B-Trees

PostgreSQL indexes including primary key indexes use **B-Trees** that keep keys sorted:

* **UUIDv4 (Random):** Because bits are pseudo-random, new keys land in arbitrary locations across existing B-Tree leaf pages. When a target page is already full, PostgreSQL performs a **page split**, copying roughly half the entries into a new page and leaving empty space behind alongside extra random disk I/O which causes index bloat.
* **UUIDv7 (Time-Ordered):** Because the leading bits encode a Unix epoch timestamp, newly generated keys are increasing over time sequentially (just the leading bits). Inserts predominantly append to the **rightmost edge** of the B-Tree, filling pages sequentially with minimal page splits and much better cache locality.

## Architecture & Test Setup

- **Database:** PostgreSQL 16 (`postgres:16-alpine`) launched with `shared_buffers=16MB`, `max_wal_size=1GB`, and `checkpoint_timeout=5min` so the 5M-row index exceeds buffer cache and forces realistic page eviction, WAL activity, and disk I/O.
- **Benchmark Runner:** Python 3.12 (`python:3.12-alpine`) using `psycopg2`, `fastuuid7`, and `rich`, orchestrated via Docker Compose with a `pg_isready` healthcheck so `run.py` waits until PostgreSQL is ready before connecting.

## Quick Start

1. **Build and run the benchmark tests:**
   ```bash
   docker compose run --rm --build uuid-benchmark
   ```

2. **Clean up and reset the database:**
   ```bash
   docker compose down -v
   ```
