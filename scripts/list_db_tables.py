from database import get_db_path, get_connector

print('Resolved DB path:', get_db_path())
try:
    conn = get_connector().connect()
    cur = conn.cursor()
    print('\nTables found:')
    # Try using cursor.tables() if available
    try:
        for row in cur.tables(tableType='TABLE'):
            # row might be a pyodbc.Row; print table name
            try:
                print(' -', row.table_name)
            except Exception:
                print(' -', row)
    except Exception:
        # Fallback: query MSysObjects (may be restricted)
        try:
            cur.execute("SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0")
            for r in cur.fetchall():
                print(' -', r[0])
        except Exception as e:
            print('Could not enumerate tables via cursor.tables() or MSysObjects:', e)
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
except Exception as e:
    print('Error connecting to DB:', e)
