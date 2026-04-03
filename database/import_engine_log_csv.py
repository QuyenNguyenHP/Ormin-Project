import csv
import os
import sqlite3
import time
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "ORMIN.db")
CSV_FOLDER = os.path.join(BASE_DIR, "csv")
TABLE_NAME = "engine_log"
CSV_HAS_HEADER = False
ARCHIVE_FOLDER = os.path.join(BASE_DIR, "csv archive")
POLL_SECONDS = 2


def normalize(name: str) -> str:
    return name.strip().lower()


def get_table_columns(conn: sqlite3.Connection, table: str) -> list[tuple[str, int]]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    # Returns list of (column_name, is_pk)
    return [(row[1], row[5]) for row in cur.fetchall()]


def read_csv_rows(csv_path: str) -> list[dict]:
    # Try UTF-8 with BOM first, then fallback to Windows-1252 if needed.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(csv_path, "r", newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return []
                return list(reader)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Unable to decode CSV file", b"", 0, 0, "Unknown encoding")


def read_csv_rows_no_header(csv_path: str) -> list[list[str]]:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(csv_path, "r", newline="", encoding=encoding) as f:
                reader = csv.reader(f)
                rows = [row for row in reader if row]
                return rows
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Unable to decode CSV file", b"", 0, 0, "Unknown encoding")


def choose_columns_for_headerless(table_cols: list[tuple[str, int]], csv_width: int) -> list[str]:
    cols = [c for c, _ in table_cols]
    if len(cols) == csv_width:
        return cols

    pk_cols = [c for c, is_pk in table_cols if is_pk]
    if len(cols) - 1 == csv_width and len(pk_cols) == 1:
        return [c for c, is_pk in table_cols if not is_pk]

    # Fallback: take the first N columns
    return cols[:csv_width]


def import_csv_file(conn: sqlite3.Connection, csv_path: str, table_cols: list[tuple[str, int]]) -> int:
    if CSV_HAS_HEADER:
        rows = read_csv_rows(csv_path)
        if not rows:
            return 0

        table_map = {normalize(c): c for c, _ in table_cols}
        csv_headers = rows[0].keys()
        csv_map = {normalize(h): h for h in csv_headers}

        used_cols = [table_map[n] for n in csv_map.keys() if n in table_map]
        if not used_cols:
            return 0

        cols_sql = ", ".join([f'"{c}"' for c in used_cols])
        placeholders = ", ".join(["?"] * len(used_cols))
        insert_sql = f'INSERT INTO {TABLE_NAME} ({cols_sql}) VALUES ({placeholders})'
    else:
        rows = read_csv_rows_no_header(csv_path)
        if not rows:
            return 0

        used_cols = choose_columns_for_headerless(table_cols, len(rows[0]))
        if not used_cols:
            return 0

        cols_sql = ", ".join([f'"{c}"' for c in used_cols])
        placeholders = ", ".join(["?"] * len(used_cols))
        insert_sql = f'INSERT INTO {TABLE_NAME} ({cols_sql}) VALUES ({placeholders})'

    def to_value(v):
        if v is None:
            return None
        v = v.strip() if isinstance(v, str) else v
        return v if v != "" else None

    data = []
    if CSV_HAS_HEADER:
        for row in rows:
            values = []
            for col in used_cols:
                csv_col = csv_map[normalize(col)]
                values.append(to_value(row.get(csv_col)))
            data.append(values)
    else:
        for row in rows:
            values = [to_value(v) for v in row[: len(used_cols)]]
            data.append(values)

    cur = conn.cursor()
    cur.executemany(insert_sql, data)
    return len(data)


def import_once(conn: sqlite3.Connection) -> int:
    if not os.path.isdir(CSV_FOLDER):
        print(f"CSV folder not found: {CSV_FOLDER}")
        return 0

    table_cols = get_table_columns(conn, TABLE_NAME)
    if not table_cols:
        print(f"Table not found or has no columns: {TABLE_NAME}")
        return 0

    csv_files = [
        os.path.join(CSV_FOLDER, f)
        for f in os.listdir(CSV_FOLDER)
        if f.lower().endswith(".csv")
    ]
    if not csv_files:
        return 0

    total_inserted = 0
    for csv_path in sorted(csv_files):
        try:
            inserted = import_csv_file(conn, csv_path, table_cols)
            conn.commit()
            total_inserted += inserted
            file_name = os.path.basename(csv_path)
            print(f"Imported {inserted} rows from {file_name}")

            os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
            archived_path = os.path.join(ARCHIVE_FOLDER, file_name)
            if os.path.exists(archived_path):
                base, ext = os.path.splitext(file_name)
                archived_path = os.path.join(
                    ARCHIVE_FOLDER,
                    f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}",
                )
            os.replace(csv_path, archived_path)
            print(f"Moved to archive: {os.path.basename(archived_path)}")
        except Exception as e:
            conn.rollback()
            print(f"Failed to import {os.path.basename(csv_path)}: {e}")

    return total_inserted


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print(f"Watching for new CSV files in: {CSV_FOLDER}")
    print(f"Archive folder: {ARCHIVE_FOLDER}")
    try:
        while True:
            inserted = import_once(conn)
            if inserted:
                print(f"Imported {inserted} rows in this cycle.")
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
