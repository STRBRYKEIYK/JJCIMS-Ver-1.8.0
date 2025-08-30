import csv
import re
from datetime import datetime
from pathlib import Path

csv_path = r"c:\Users\KEIYK\OneDrive\Documents\ITEMSDB.csv"
out_path = Path(r"d:\JJC OJT WORKS\New JJCIMS\Backup\JJCIMS VER 1.6.0\ITEMSDB.sql")

def clean_price(s):
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    # Remove any currency symbols, question marks, quotes and commas
    s = re.sub(r"[^0-9.\-]", "", s)
    if s == "":
        return None
    try:
        v = float(s)
        return f"{v:.2f}"
    except Exception:
        return None


def parse_date(s):
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    # Try common formats
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d.strftime("%Y-%m-%d")
        except Exception:
            pass
    # If it looks like YYYY-MM-DD already
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return s
    return None


def sql_str(s):
    if s is None:
        return 'NULL'
    s = s.strip()
    if s == "":
        return 'NULL'
    s = s.replace("'", "''")
    return f"'{s}'"


def sql_value(val, is_int=False, is_dec=False, is_date=False):
    # Return raw SQL tokens (no surrounding commas) - numbers and NULL are unquoted
    if val is None:
        return 'NULL'
    if is_int:
        try:
            return str(int(float(val)))
        except Exception:
            return 'NULL'
    if is_dec:
        try:
            # format decimals with 2 fraction digits
            return f"{float(val):.2f}"
        except Exception:
            return 'NULL'
    if is_date:
        # date values should be 'YYYY-MM-DD' or NULL
        return sql_str(val)
    return sql_str(val)


def batch_inserts(rows, batch_size=100):
    """Yield batched INSERT statements (single INSERT with multiple rows)"""
    cols = ['item_name','brand','item_type','location','unit_of_measure','in_qty','out_qty','min_stock','price_per_unit','last_po','supplier']
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i+batch_size]
        values_lines = []
        for r in chunk:
            vals = [
                sql_value(r['item_name']),
                sql_value(r['brand']),
                sql_value(r['item_type']),
                sql_value(r['location']),
                sql_value(r['unit_of_measure']),
                sql_value(r['in_qty'], is_int=True),
                sql_value(r['out_qty'], is_int=True),
                sql_value(r['min_stock'], is_int=True),
                sql_value(r['price_per_unit'], is_dec=True),
                sql_value(r['last_po'], is_date=True),
                sql_value(r['supplier']),
            ]
            values_lines.append('  (' + ', '.join(vals) + ')')
        stmt = 'INSERT INTO itemsdb (' + ', '.join(cols) + ') VALUES\n' + ',\n'.join(values_lines) + ';\n'
        yield stmt


create_stmt = '''CREATE TABLE IF NOT EXISTS itemsdb (
  item_no INT PRIMARY KEY AUTO_INCREMENT,
  item_name VARCHAR(255) NOT NULL,
  brand VARCHAR(255),
  item_type VARCHAR(255),
  location VARCHAR(255),
  unit_of_measure VARCHAR(50),
  in_qty INT,
  out_qty INT,
  balance INT GENERATED ALWAYS AS (in_qty - out_qty) STORED,
  min_stock INT,
  deficit INT GENERATED ALWAYS AS (min_stock - balance) STORED,
  price_per_unit DECIMAL(10,2),
  cost DECIMAL(10,2) GENERATED ALWAYS AS (price_per_unit * balance) STORED,
  item_status VARCHAR(20) GENERATED ALWAYS AS (
    CASE
      WHEN balance <= 0 THEN 'Out Of Stock'
      WHEN balance <= deficit THEN 'Low In Stock'
      ELSE 'In Stock'
    END
  ) STORED,
  last_po DATE,
  supplier VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

rows = []
with open(csv_path, newline='', encoding='utf-8-sig') as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        # Map CSV headers to table columns
        name = r.get('NAME') or r.get('Name')
        brand = r.get('BRAND')
        item_type = r.get('TYPE')
        location = r.get('LOCATION')
        unit = r.get('UNIT OF MEASURE') or r.get('UNIT')
        in_qty = r.get('IN') or r.get('In')
        out_qty = r.get('OUT') or r.get('Out')
        min_stock = r.get('MIN STOCK')
        price_raw = r.get('PRICE PER UNIT') or r.get('PRICE')
        last_po_raw = r.get('LAST PO')
        supplier = r.get('SUPPLIER')

        price = clean_price(price_raw)
        last_po = parse_date(last_po_raw)

        rows.append({
            'item_name': name,
            'brand': brand,
            'item_type': item_type,
            'location': location,
            'unit_of_measure': unit,
            'in_qty': in_qty,
            'out_qty': out_qty,
            'min_stock': min_stock,
            'price_per_unit': price,
            'last_po': last_po,
            'supplier': supplier,
        })

# Write SQL file
with out_path.open('w', encoding='utf-8') as out:
    out.write('-- Generated from ITEMSDB.csv\n')
    out.write('-- Cleaned and batched by generate_itemsdb_sql.py\n')
    out.write(create_stmt + '\n')
    # write batched INSERTs
    for stmt in batch_inserts(rows, batch_size=100):
        out.write(stmt + '\n')

print(f'Wrote SQL to: {out_path}')
print(f'Rows processed: {len(rows)}')
