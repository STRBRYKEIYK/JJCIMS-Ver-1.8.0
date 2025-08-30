"""Utility script to list distinct item type/category values from ITEMSDB.

Adds diagnostics to help resolve Access 'Too few parameters. Expected N' errors
which usually mean a misspelled table or column name in Access/pyodbc.
"""

from database import get_connector, get_db_path
import sys
from typing import List, Optional


POSSIBLE_TYPE_COLUMN_NAMES = [
    "TYPE",
    "ITEM_TYPE",
    "ITEMTYPE",
    "CATEGORY",
    "CAT",
    "ITEM_CATEGORY",
]


def get_columns(cursor, table: str) -> List[str]:
    """Return column names for a table (case preserved as returned)."""
    cursor.execute(f'SELECT * FROM [{table}] WHERE 1=0')  # no rows, just metadata
    return [desc[0] for desc in cursor.description]


def find_type_column(columns: List[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in columns}
    for candidate in POSSIBLE_TYPE_COLUMN_NAMES:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    # Heuristic fallback: look for any column containing 'type' or 'cat'
    for c in columns:
        cl = c.lower()
        if "type" in cl or cl.endswith("cat") or "category" in cl:
            return c
    return None


def main():  # noqa: D401
    print("Connecting to database...")
    db = get_connector(get_db_path())
    db.connect()
    cursor = db.connection.cursor()
    table_name = "ITEMSDB"

    try:
        try:
            columns = get_columns(cursor, table_name)
        except Exception as meta_err:  # noqa: BLE001
            print(f"Failed to read metadata for table [{table_name}].")
            print("Original error:", meta_err)
            print("HINT: Ensure the table name is correct (check spelling/case) and that the Access DB contains it.")
            return 2

        print(f"Discovered {len(columns)} columns in [{table_name}]: {', '.join(columns)}")

        type_col = find_type_column(columns)
        if not type_col:
            print("Could not automatically identify a column representing item type/category.")
            print("Consider renaming one of the columns to one of:")
            print(", ".join(POSSIBLE_TYPE_COLUMN_NAMES))
            return 3

        print(f"Using column [{type_col}] to enumerate distinct values.")
        # Multiple fallback patterns to combat reserved words / syntax edge cases
        base_col = f"[{type_col}]"
        query_attempts = [
            (
                "Distinct with where/order (alias order)",
                f"SELECT DISTINCT {base_col} AS TYPE_VALUE FROM [{table_name}] "
                f"WHERE {base_col} IS NOT NULL AND {base_col} <> '' ORDER BY TYPE_VALUE",
            ),
            (
                "Simplest distinct (no where/order)",
                f"SELECT DISTINCT {base_col} AS TYPE_VALUE FROM [{table_name}]",
            ),
            (
                "Group by", f"SELECT {base_col} AS TYPE_VALUE FROM [{table_name}] GROUP BY {base_col}",
            ),
            (
                "Cast to text", f"SELECT DISTINCT CStr({base_col}) AS TYPE_VALUE FROM [{table_name}] WHERE {base_col} IS NOT NULL",
            ),
            (
                "Top 5 raw", f"SELECT TOP 5 {base_col} AS TYPE_VALUE FROM [{table_name}]",
            ),
        ]

        rows = None
        last_error = None
        for label, q in query_attempts:
            try:
                print(f"Attempt: {label}")
                cursor.execute(q)
                rows = cursor.fetchall()
                print(f" -> Success with '{label}' (returned {len(rows)} rows pre-filter).")
                break
            except Exception as e:  # noqa: BLE001
                last_error = e
                print(f" -> Failed '{label}': {e}")

        if rows is None:
            print("All query attempts failed.")
            print("Last error:", last_error)
            print("NEXT STEPS:")
            print(" 1. Open the Access DB directly and verify the column really is named exactly '" + type_col + "'.")
            print(" 2. If it is a reserved word (TYPE is reserved), consider renaming it (e.g., ITEM_TYPE) or referencing via alias only.")
            print(" 3. Ensure no user-defined Access parameter named TYPE shadows the field.")
            return 4

        # Filter out null/empty values client-side if the successful query variant omitted filtering
        cleaned = [r for r in rows if r[0] not in (None, "")] if rows else []
        # Deduplicate in Python if variant lacked DISTINCT
        unique_values = []
        seen = set()
        for r in cleaned:
            v = r[0]
            if v not in seen:
                seen.add(v)
                unique_values.append(v)
        unique_values.sort(key=lambda x: (str(x).lower()))

        if not unique_values:
            print("No distinct non-empty values found.")
            return 0

        print("Available type/category values:")
        for v in unique_values:
            print(f" - {v}")
        return 0
    finally:
        try:
            cursor.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            db.connection.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.exit(main())
