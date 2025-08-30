"""Centralized SQL query helpers.

Place common SQL strings and small convenience wrappers here so UI code
doesn't need to construct or execute raw SQL strings directly.
"""
from datetime import datetime


def update_item_out(connector, name, qty):
    """Increment the OUT counter for an item by name."""
    query = "UPDATE ITEMSDB SET [OUT] = [OUT] + ? WHERE [NAME] = ?"
    connector.execute_query(query, (qty, name))


def get_unit_of_measure(connector, name):
    """Return the unit of measure string for an item name or None."""
    row = connector.fetchone("SELECT [UNIT OF MEASURE] FROM ITEMSDB WHERE [NAME] = ?", (name,))
    if row and row[0]:
        return row[0]
    return None


def insert_emp_log(connector, name, details, when=None):
    """Insert a log entry into emp_logs. when may be (date_str, time_str) or None."""
    if when is None:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
    else:
        date_str, time_str = when
    connector.execute_query(
        "INSERT INTO [emp_logs] ([DATE], [TIME], [NAME], [DETAILS]) VALUES (?, ?, ?, ?)",
        (date_str, time_str, name, details)
    )


def get_emp_2fa_and_access(connector, username_lower):
    """Return (2FA Secret, Access Level) for a lowercase username or None."""
    return connector.fetchone("SELECT [2FA Secret], [Access Level] FROM [emp_list] WHERE LCase([Username])=?", (username_lower,))


def fetch_items_for_employee_dashboard(connector):
    """Return rows for the employee dashboard item list."""
    return connector.fetchall("SELECT ID, [ITEMS], [Supplier], [PO no] FROM [ITEMSDB]")


def fetch_items_by_type(connector, category):
    """Return item rows filtered by TYPE."""
    return connector.fetchall(
        "SELECT ID, NAME, BRAND, TYPE, LOCATION, UNIT_OF_MEASURE, STATUS, BALANCE FROM JJCIMS WHERE TYPE = ?",
        (category,)
    )


# -------------------------
# User / Auth helpers
# -------------------------
def get_user_by_username(connector, username):
    """Return full user row for exact Username (case-sensitive) or None."""
    return connector.fetchone("SELECT * FROM [emp_list] WHERE [Username]=?", (username,))


def get_user_by_username_lower(connector, username_lower):
    """Return row for lowercase username comparison (useful when callers store lowercased usernames)."""
    return connector.fetchone("SELECT * FROM [emp_list] WHERE LCase([Username])=?", (username_lower,))


def username_exists(connector, username):
    row = connector.fetchone("SELECT COUNT(*) FROM [emp_list] WHERE [Username]=?", (username,))
    return bool(row and row[0])


def update_user_password(connector, username_lower, encrypted_password):
    """Update password for a username (case-insensitive using LCase)."""
    connector.execute_query("UPDATE [emp_list] SET [Password]=? WHERE LCase([Username])=?", (encrypted_password, username_lower))


def update_user_access_level(connector, username, new_level):
    connector.execute_query("UPDATE [emp_list] SET [Access Level]=? WHERE [Username]=?", (new_level, username))


def set_user_2fa_secret(connector, username, encrypted_secret):
    connector.execute_query("UPDATE [emp_list] SET [2FA Secret]=? WHERE [Username]=?", (encrypted_secret, username))


# -------------------------
# Admin / Items CRUD
# -------------------------
def add_item(connector, item_fields_tuple):
    """Insert a new row into ITEMSDB. Caller is responsible for building the field tuple in the right order."""
    # The project historically uses a long INSERT; keep callers in control of the exact SQL to avoid mismatches.
    connector.execute_query(
        "INSERT INTO ITEMSDB (NAME, BRAND, TYPE, LOCATION, UNIT_OF_MEASURE, STATUS, BALANCE, [OUT]) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        item_fields_tuple,
    )


def update_item_by_id(connector, item_id, fields_dict):
    """Update only the fields provided in fields_dict for the given ID.

    fields_dict: {column_name: value}
    """
    if not fields_dict:
        return
    set_clause = ", ".join([f"[{k}] = ?" for k in fields_dict.keys()])
    params = tuple(fields_dict.values()) + (item_id,)
    query = f"UPDATE ITEMSDB SET {set_clause} WHERE ID = ?"
    connector.execute_query(query, params)


def delete_item_by_name(connector, name):
    connector.execute_query("DELETE FROM ITEMSDB WHERE NAME = ?", (name,))


def fetch_item_unit_of_measure(connector, name):
    return get_unit_of_measure(connector, name)


# -------------------------
# Logs & dashboards
# -------------------------
def insert_admin_log(connector, user, details, when=None):
    if when is None:
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
    else:
        date_str, time_str = when
    connector.execute_query(
        "INSERT INTO [adm_logs] ([DATE],[TIME],[USER],[DETAILS]) VALUES (?,?,?,?)",
        (date_str, time_str, user, details),
    )


def fetch_emp_logs(connector, limit=500):
    return connector.fetchall("SELECT [DATE], [TIME], [NAME], [DETAILS] FROM [emp_logs] ORDER BY [DATE] DESC, [TIME] DESC")


def fetch_admin_logs(connector, limit=500):
    return connector.fetchall("SELECT [DATE], [TIME], [USER], [DETAILS] FROM [adm_logs] ORDER BY [DATE] DESC, [TIME] DESC")


def clear_emp_logs(connector):
    connector.execute_query("DELETE FROM [emp_logs]")


def clear_admin_logs(connector):
    connector.execute_query("DELETE FROM [adm_logs]")


# -------------------------
# Utility
# -------------------------
def table_exists(connector, table_name):
    row = connector.fetchone("SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0 AND Name=?", (table_name,))
    return bool(row)

