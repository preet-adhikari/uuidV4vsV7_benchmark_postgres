import os
import time
import uuid

from rich.table import Table
from fastuuid7 import uuid7
import psycopg2
from psycopg2.extras import execute_batch
from rich.console import Console
console = Console()

# Connect to database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "password"),
    dbname=os.getenv("DB_NAME", "fragment_db"),
)


# Flush data to the hard drive
conn.autocommit = True


# Open a session
cursor = conn.cursor()


# Drop table commands
cursor.execute(
    "DROP TABLE IF EXISTS uuid_version_4"
)

cursor.execute(
    "DROP TABLE IF EXISTS uuid_version_7"
)

# Create table that'll be used for v4
cursor.execute(
    "CREATE TABLE uuid_version_4 ("
    "id uuid PRIMARY KEY,"
    "FirstName varchar(255) NOT NULL)"
)

# Create table that'll be used for v7
cursor.execute(
    "CREATE TABLE uuid_version_7 ("
    "id uuid PRIMARY KEY,"
    "FirstName varchar(255) NOT NULL)"
)

TOTAL_BATCHES = 50
BATCH_SIZE = 100_000
TOTAL_ROWS = TOTAL_BATCHES * BATCH_SIZE

total_v4_time = 0.0
total_v7_time = 0.0

total_v4_index = ""
total_v7_index = ""
print("Let the page fragmentation begin!")
with console.status("Working..."):
    for i in range(TOTAL_BATCHES):

        uuid_v4_rows = [(str(uuid.uuid4()), f"user{i}") for i in range(BATCH_SIZE)]
        start_time_uuid_v4 = time.time()
        execute_batch(
            cursor,
            "INSERT INTO uuid_version_4 (id, Firstname) VALUES (%s, %s)",
            uuid_v4_rows,
        )
        end_time_uuid_v4 = time.time()
        time_taken_for_uuidv4_insertion = end_time_uuid_v4 - start_time_uuid_v4
        total_v4_time += time_taken_for_uuidv4_insertion
        insertion_per_second_v4 = 100_000 / time_taken_for_uuidv4_insertion
        print(f"Insertion throughput for uuidv4s : {insertion_per_second_v4}")

        uuid_v7_rows = [(str(uuid7()), f"user{i}") for i in range(BATCH_SIZE)]
        start_time_uuid_v7 = time.time()
        execute_batch(
            cursor,
            "INSERT INTO uuid_version_7 (id, Firstname) VALUES (%s, %s)",
            uuid_v7_rows,
        )
        end_time_uuid_v7 = time.time()
        time_taken_for_uuidv7_insertion = end_time_uuid_v7 - start_time_uuid_v7
        total_v7_time += time_taken_for_uuidv7_insertion
        insertion_per_second_v7 = 100_000/ time_taken_for_uuidv7_insertion
        print(f"Insertion throughput for uuidv7s : {insertion_per_second_v7}")

        print()
        print(f"Final stats for batch no {i}")

        print("-----------------------")
        cursor.execute("SELECT pg_size_pretty(pg_relation_size('uuid_version_4_pkey'))")
        v4_result = cursor.fetchone()
        total_v4_index = v4_result
        print(
            f"Index size of uuid_version_4 : {v4_result[0] if v4_result else 'Cursor Empty'}"
        )

        print()

        cursor.execute("SELECT pg_size_pretty(pg_relation_size('uuid_version_7_pkey'))")
        v7_result = cursor.fetchone()
        total_v7_index = v7_result
        print(f"Index size of uuid_version_7 : {v7_result[0] if v7_result else 'Cursor Empty'}")
        print("-----------------------")


overall_v4_throughput = TOTAL_ROWS / total_v4_time
overall_v7_throughput = TOTAL_ROWS / total_v7_time

v4_index_display = total_v4_index[0] if total_v4_index else "Cursor Empty"
v7_index_display = total_v7_index[0] if total_v7_index else "Cursor Empty"

table = Table(title="Final Benchmark Summary (5M Rows)")

table.add_column("Metric", style="bold cyan")
table.add_column("UUIDv4", justify="right", style="yellow")
table.add_column("UUIDv7", justify="right", style="green")

table.add_row(
    "Total Insert Time",
    f"{total_v4_time:.2f}s",
    f"{total_v7_time:.2f}s",
)
table.add_row(
    "Overall Throughput (rows/s)",
    f"{overall_v4_throughput:.2f}",
    f"{overall_v7_throughput:.2f}",
)
table.add_row(
    "Final Index Size",
    v4_index_display,
    v7_index_display,
)

console.print()
console.print(table)
