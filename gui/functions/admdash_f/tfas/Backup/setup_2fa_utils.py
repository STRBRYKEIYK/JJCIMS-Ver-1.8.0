import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Add this import
from PIL import ImageTk
import pyotp
import qrcode
import os
from database import get_connector

def load_fernet_key(fernet_key_path):
    """Load or generate a Fernet key from the given path."""
    from cryptography.fernet import Fernet
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('fernet_key', fernet_key_path)
        fernet_key_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fernet_key_mod)
        if getattr(fernet_key_mod, 'FERNET_KEY', None):
            return fernet_key_mod.FERNET_KEY
    except Exception:
        pass
    key = Fernet.generate_key()
    with open(fernet_key_path, 'w') as f:
        f.write('# Fernet key for 2FA\nfrom cryptography.fernet import Fernet\n')
        f.write(f'FERNET_KEY = {repr(key)}\n')
    return key

def encrypt_2fa(secret, fernet):
    return fernet.encrypt(secret.encode('utf-8')).decode('utf-8')

def resolve_path(path):
    # Always resolve relative to the current working directory (project root)
    return os.path.abspath(path)

def get_project_root():
    # Find the JJCFPIS project root from this file's location
    current = os.path.abspath(__file__)
    while True:
        current, tail = os.path.split(current)
        if tail.lower() == "jjcfpis" or not tail:
            break
    return os.path.join(current, "JJCFPIS")

def get_abs_path_from_project_root(*relative_parts):
    # This file is under JJCFPIS/gui/functions/admdash_f/tfas/
    jjcfpis_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    return os.path.join(jjcfpis_root, *relative_parts)

def setup_2fa(
    parent,
    username,
    db_path,
    fernet_key_path,
    colors=None,
    popup=True,
    on_success=None,
):
    default_colors = {
        'bg': '#181c1f',
        'fg': '#fffde7',
        'entry_bg': '#23272b',
        'button_bg': '#f5f5f7',
        'button_fg': '#0071e3',
        'accent': '#ff6f00',
        'mac_btn_red': '#ff5f57',
        'mac_btn_yellow': '#ffbd2e',
        'mac_btn_green': '#28c840',
    }
    C = {**default_colors, **(colors or {})}

    from cryptography.fernet import Fernet
    key = load_fernet_key(fernet_key_path)
    fernet = Fernet(key)
    # --- macOS Button Style ---
    style = ttk.Style()
    macos_button_bg = '#F5F5F7'
    macos_button_fg = '#1C1C1E'
    macos_button_border = '#D1D1D6'
    macos_button_active_bg = '#E5E5EA'
    macos_button_font = ("Segoe UI", 12, "bold")
    style.configure(
        "MacOS.TButton",
        font=macos_button_font,
        background=macos_button_bg,
        foreground=macos_button_fg,
        borderwidth=1,
        focustickness=2,
        focuscolor=macos_button_border,
        relief="flat",
        padding=(16, 8),
    )
    style.map(
        "MacOS.TButton",
        background=[('active', macos_button_active_bg), ('pressed', macos_button_active_bg)],
        foreground=[('active', macos_button_fg), ('pressed', macos_button_fg)],
        bordercolor=[('focus', macos_button_border), ('!focus', macos_button_border)]
    )

    def do_generate_and_show(content, entered_username):
        new_secret = pyotp.random_base32()
        for widget in content.winfo_children():
            if getattr(widget, 'is_dynamic', False):
                widget.destroy()
        uri = pyotp.totp.TOTP(new_secret).provisioning_uri(name=entered_username, issuer_name='JJCFPIS')
        qr_img = qrcode.make(uri)
        qr_img = qr_img.resize((160, 160))
        qr_photo = ImageTk.PhotoImage(qr_img)
        qr_label = tk.Label(content, image=qr_photo, bg=C['bg'])
        qr_label.image = qr_photo
        qr_label.is_dynamic = True
        qr_label.pack(pady=(10, 6))
        secret_label = tk.Label(content, text=f'{new_secret}', font=("Segoe UI", 10), bg=C['bg'], fg=C['fg'])
        secret_label.is_dynamic = True
        secret_label.pack(pady=(2, 2))
        instr_label = tk.Label(content, text='Scan QR & enter 6-digit code:', font=("Segoe UI", 10), bg=C['bg'], fg=C['fg'])
        instr_label.is_dynamic = True
        instr_label.pack(pady=(8, 2))
        code_entry = tk.Entry(content, font=("Segoe UI", 14), bg=C['entry_bg'], fg=C['fg'], insertbackground=C['fg'], width=8, relief='solid', justify='center')
        code_entry.is_dynamic = True
        code_entry.pack(pady=8)
        def verify_code():
            code = code_entry.get().strip()
            totp = pyotp.TOTP(new_secret)
            if totp.verify(code):
                try:
                    enc_secret = encrypt_2fa(new_secret, fernet)
                    ac = get_connector(db_path)
                    ac.execute_query(
                        "UPDATE [emp_list] SET [2FA Secret]=? WHERE LCase([Username])=?",
                        params=(enc_secret, entered_username.lower()),
                    )
                    messagebox.showinfo('2FA Setup', '2FA setup complete!')
                    if popup:
                        win.destroy()
                    if on_success:
                        on_success()
                except Exception as e:
                    messagebox.showerror('Database Error', f'Could not save 2FA: {e}')
                    # Do NOT close the window on error
            else:
                messagebox.showerror('Invalid Code', 'Invalid code. 2FA not set up.')
                # Do NOT close the window on error
        verify_btn = tk.Button(content, text='Verify', font=("Segoe UI", 12, 'bold'), bg=C['button_bg'], fg=C['button_fg'], relief='flat', activebackground='#e5e5ea', activeforeground=C['button_fg'], command=verify_code, cursor='hand2')
        verify_btn.is_dynamic = True
        verify_btn.pack(pady=8)

    if popup:
        win = tk.Toplevel(parent)
        win.title("Setup 2FA - JJCIMS")
        win.attributes('-fullscreen', True)  # Fullscreen with proper Alt+Tab support
        win.configure(bg=C['bg'])
        # macOS style title bar
        title_bar = tk.Frame(win, bg=C['bg'], relief='flat', bd=0, height=28)
        title_bar.pack(fill='x', side='top')
        # macOS window buttons
        btn_frame = tk.Frame(title_bar, bg=C['bg'], height=28)
        btn_frame.pack(side='left', padx=10, pady=6)
        for color in (C['mac_btn_red'], C['mac_btn_yellow'], C['mac_btn_green']):
            btn = tk.Canvas(btn_frame, width=14, height=14, bg=C['bg'], highlightthickness=0, bd=0)
            btn.create_oval(2, 2, 12, 12, fill=color, outline=color)
            btn.pack(side='left', padx=2)
        close_btn = tk.Canvas(btn_frame, width=14, height=14, bg=C['bg'], highlightthickness=0, bd=0)
        close_btn.create_oval(2, 2, 12, 12, fill=C['mac_btn_red'], outline=C['mac_btn_red'])
        close_btn.bind('<Button-1>', lambda e: win.destroy())
        close_btn.place(x=0, y=0)
        content = tk.Frame(win, bg=C['bg'])
        content.pack(fill='both', expand=True, padx=24, pady=12)
    else:
        content = tk.Frame(parent, bg=C['bg'])

    tk.Label(content, text='Username', font=("Segoe UI", 12), bg=C['bg'], fg=C['fg']).pack(pady=(8, 2))
    username_var = tk.StringVar(value=username)
    username_entry = tk.Entry(content, font=("Segoe UI", 12), bg=C['entry_bg'], fg=C['fg'], insertbackground=C['fg'], width=18, relief='solid', textvariable=username_var)
    username_entry.pack(pady=2)
    def on_generate():
        entered_username = username_var.get().strip()
        if not entered_username:
            messagebox.showwarning('Input Error', 'Please enter a username.')
            return
        # If caller passed an explicit db_path, ensure it exists. Otherwise let the connector resolve the canonical DB.
        if db_path and not os.path.isfile(db_path):
            messagebox.showerror('Database Error', f"Database file not found:\n{db_path}\n\nPlease ensure the file exists at this path. The application uses the canonical database at 'database/JJCIMS.accdb'.")
            return
        try:
            ac = get_connector(db_path)
            row_secret = ac.get_2fa_secret(entered_username.lower())
            if row_secret is None:
                messagebox.showerror('User Not Found', 'Username not found.')
                return
            if row_secret:
                messagebox.showinfo('2FA Exists', '2FA is already set up for this user.')
                return
        except Exception as e:
            messagebox.showerror('Database Error', f'Could not check 2FA: {e}')
            return
        do_generate_and_show(content, entered_username)
    # macOS style minimal button
    gen_btn = tk.Button(content, text='Generate 2FA', font=("Segoe UI", 12, 'bold'), bg=C['button_bg'], fg=C['button_fg'], relief='flat', activebackground='#e5e5ea', activeforeground=C['button_fg'], command=on_generate, cursor='hand2')
    gen_btn.pack(pady=12)
    close_btn2 = tk.Button(content, text="Close", command=(win.destroy if popup else content.destroy), font=("Segoe UI", 11, "bold"), bg=C['button_bg'], fg=C['button_fg'], relief='flat', activebackground='#e5e5ea', activeforeground=C['button_fg'], width=10, cursor='hand2')
    close_btn2.pack(pady=4)

    if not popup:
        return content
