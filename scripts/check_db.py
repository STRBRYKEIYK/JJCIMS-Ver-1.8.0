import sys
import pyodbc
p = sys.argv[1]
print('DB:', p)
try:
    conn = pyodbc.connect(f"DRIVER={'{'}Microsoft Access Driver (*.mdb, *.accdb){'}'};DBQ={p};")
    cur = conn.cursor()
    try:
        for r in cur.tables(tableType='TABLE'):
            try:
                print(' -', r.table_name)
            except Exception:
                print(' -', r)
    except Exception as e:
        try:
            cur.execute('SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0')
            for rr in cur.fetchall():
                print(' -', rr[0])
        except Exception as e:
            print('Could not enumerate tables:', e)
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
    print('Connection error:', e)
