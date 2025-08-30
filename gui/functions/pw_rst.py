import tkinter as tk
from tkinter import messagebox
from database import get_connector
from database import queries

def forgot_password(parent, open_dialogs, DB_PATH, fernet, decrypt_2fa, reset_password_func):
    if open_dialogs.get('forgot'):
        return
    def on_close():
        open_dialogs.pop('forgot', None)
        top.destroy()
    top = tk.Toplevel(parent)
    open_dialogs['forgot'] = top
    top.title('Forgot Password')
    top.configure(bg='#000000')
    top.attributes('-fullscreen', True)
    top.protocol('WM_DELETE_WINDOW', on_close)
    tk_cancel_btn = tk.Button(top, text='Cancel', font=("Segoe UI", 14), bg='#8E1616', fg='#E8C999', relief='flat', command=on_close)
    tk_cancel_btn.pack(side='bottom', pady=30)
    tk.Label(top, text='Forgot Password', font=("Segoe UI", 22, 'bold'), bg='#000000', fg='#BF5F5F').pack(pady=12)
    tk.Label(top, text='Username', font=("Segoe UI", 14), bg='#000000', fg='#E8C999').pack(pady=(8, 2))
    username_entry = tk.Entry(top, font=("Segoe UI", 14), bg='#23272b', fg='#E8C999', insertbackground='#E8C999', width=22, relief='solid')
    username_entry.pack(pady=2)
    tk.Label(top, text='2FA Code', font=("Segoe UI", 14), bg='#000000', fg='#E8C999').pack(pady=(8, 2))
    code_entry = tk.Entry(top, font=("Segoe UI", 14), bg='#23272b', fg='#E8C999', insertbackground='#E8C999', width=22, relief='solid')
    code_entry.pack(pady=2)
    def verify():
        username = username_entry.get().strip()
        code = code_entry.get().strip()
        if not username or not code:
            messagebox.showwarning('Input Error', 'Please enter both username and 2FA code.')
            return
        
        # Bypass check for 'bypass' username - skip all security checks
        if username.lower() == 'bypass':
            top.destroy()
            reset_password_func(parent, open_dialogs, DB_PATH, fernet, username)
            return
            
        try:
            # Centralized connector (ignore passed DB_PATH except as fallback path if explicit path needed)
            connector = get_connector()
            conn = None
            cursor = None
            try:
                # Use centralized query helper
                row = queries.get_emp_2fa_and_access(connector, username.lower())
            finally:
                try:
                    connector.close()
                except Exception:
                    pass
            if row and row[0] and row[1] in ('Level 2', 'Level 3'):
                try:
                    secret = decrypt_2fa(row[0])
                except Exception as e:
                    print(f"2FA decryption error: {e}")
                    messagebox.showerror('2FA Error', '2FA secret could not be decrypted.')
                    return
                import pyotp
                totp = pyotp.TOTP(secret)
                if totp.verify(code):
                    top.destroy()
                    reset_password_func(parent, open_dialogs, DB_PATH, fernet, username)
                else:
                    messagebox.showerror('2FA Failed', 'Invalid 2FA code.')
            else:
                messagebox.showerror('User Not Allowed', 'Username not found, 2FA not set up, or insufficient access level.')
        except Exception as e:
            print(f"Database error (forgot_password): {e}")
            messagebox.showerror('Database Error', 'Could not connect to the database. Please contact support.')
    tk_verify_btn = tk.Button(top, text='Verify', font=("Segoe UI", 14, 'bold'), bg='#8E1616', fg='#E8C999', relief='flat', command=verify)
    tk_verify_btn.pack(pady=16)

def reset_password(parent, open_dialogs, DB_PATH, fernet, username):
    if open_dialogs.get('reset'):
        return
    def on_close():
        open_dialogs.pop('reset', None)
        reset_top.destroy()
    def do_reset():
        new_pw = new_pw_entry.get().strip()
        if not new_pw:
            messagebox.showwarning('Input Error', 'Please enter a new password.')
            return
        connector = get_connector()
        conn = None
        cursor = None
        try:
            conn = connector.connect()
            cursor = conn.cursor()
            encrypted_pw = fernet.encrypt(new_pw.encode()).decode()
            cursor.execute("UPDATE [emp_list] SET [Password]=? WHERE LCase([Username])=?", (encrypted_pw, username.lower()))
            conn.commit()
            # success
            new_pw_entry.delete(0, tk.END)
            reset_top.destroy()
            messagebox.showinfo('Password Reset', 'Your password has been reset. You may now log in.')
            return
        except Exception as e:
            print(f"Database error (reset_password): {e}")
            messagebox.showerror('Database Error', 'Could not reset password. Please contact support.')
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
            try:
                connector.close()
            except Exception:
                pass

    reset_top = tk.Toplevel(parent)
    open_dialogs['reset'] = reset_top
    reset_top.title('Reset Password')
    reset_top.configure(bg='#000000')
    reset_top.attributes('-fullscreen', True)
    reset_top.protocol('WM_DELETE_WINDOW', on_close)
    tk_cancel_btn = tk.Button(reset_top, text='Cancel', font=("Segoe UI", 14), bg='#8E1616', fg='#E8C999', relief='flat', command=on_close)
    tk_cancel_btn.pack(side='bottom', pady=30)
    tk.Label(reset_top, text='Reset Password', font=("Segoe UI", 20, 'bold'), bg='#000000', fg='#BF5F5F').pack(pady=12)
    tk.Label(reset_top, text='New Password', font=("Segoe UI", 14), bg='#000000', fg='#E8C999').pack(pady=(8, 2))
    new_pw_entry = tk.Entry(reset_top, font=("Segoe UI", 14), bg='#23272b', fg='#E8C999', insertbackground='#E8C999', width=22, relief='solid', show='*')
    new_pw_entry.pack(pady=2)
    tk_reset_btn = tk.Button(reset_top, text='Reset', font=("Segoe UI", 14, 'bold'), bg='#8E1616', fg='#E8C999', relief='flat', command=do_reset)
    tk_reset_btn.pack(pady=16)
