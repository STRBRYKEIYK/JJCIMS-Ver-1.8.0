import os
import tkinter as tk
from tkinter import messagebox, ttk
import importlib.util
import pyodbc
from cryptography.fernet import Fernet
from datetime import datetime


class AccountSettingsWizard:
    """Account settings multi-step wizard with clickable breadcrumbs & styled widgets."""

    def __init__(self, parent_frame, parent_app, width=1400, height=841):
        self.parent_frame = parent_frame
        self.app = parent_app
        self.width = width
        self.height = height
        self.username = getattr(self.app.parent, 'username', None)

        # State
        self.steps = []
        self.current_step = 0
        self.editing_enabled = False
        self.changed = False
        self._loaded = False
        self.original_values = {}

        # Paths
        base = os.path.dirname(__file__)
        self.db_path = os.path.abspath(os.path.join(base, '../../database/JJCIMS.accdb'))
        self.key_path = os.path.abspath(os.path.join(base, '../../../config/fernet_key.py'))

        # Root container
        self.container = tk.Frame(parent_frame, bg="#000000", width=self.width, height=self.height)
        self.container.pack_propagate(False)

        # Header
        self.header = tk.Frame(self.container, bg="#000000")
        self.header.pack(fill='x', pady=(12, 6), padx=24)
        tk.Label(self.header, text="Account Settings", font=("Segoe UI", 20, "bold"), bg="#000000", fg="#ffcc80").pack(side=tk.LEFT)
        self.progress_frame = tk.Frame(self.header, bg="#000000")
        self.progress_frame.pack(side=tk.RIGHT, padx=4)

        # Styles
        self._init_styles()

        # Step host
        self.step_frame = tk.Frame(self.container, bg="#101010")
        self.step_frame.pack(fill='both', expand=True, padx=24, pady=(0, 10))

        # Footer
        self.footer = tk.Frame(self.container, bg="#000000")
        self.footer.pack(fill='x', padx=24, pady=(0, 16))
        self.status_label = tk.Label(self.footer, text="", font=("Segoe UI", 10), bg="#000000", fg="#888888")
        self.status_label.pack(side=tk.LEFT)

        # Buttons
        self.edit_start_btn = ttk.Button(self.footer, text="Edit Account", command=self.start_editing, style='Accent.Rounded.TButton', width=18)
        self.edit_start_btn.pack(side=tk.RIGHT, padx=4)
        self.back_btn = ttk.Button(self.footer, text="◀ Back", command=self.prev_step, style='Secondary.Rounded.TButton', width=12, state='disabled')
        self.next_btn = ttk.Button(self.footer, text="Next ▶", command=self.next_step, style='Accent.Rounded.TButton', width=14, state='disabled')
        self.save_btn = ttk.Button(self.footer, text="Save", command=self.save_changes, style='Success.Rounded.TButton', width=12, state='disabled')
        self.cancel_btn = ttk.Button(self.footer, text="Cancel", command=self.cancel_changes, style='Danger.Rounded.TButton', width=12, state='disabled')

        # Vars
        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        # Overview step
        overview = self._build_overview_step()
        self.steps.append(overview)
        self._render_progress()
        self.show_step(0)

    # ---------------- Data -----------------
    def load_user_data(self):
        if not self.username:
            self.status_label.config(text="No username in session.")
            return
        try:
            conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' f'DBQ={self.db_path};')
            conn = pyodbc.connect(conn_str)
            cur = conn.cursor()
            cur.execute("SELECT [First Name], [Last Name], [Username], [Password] FROM [emp_list] WHERE [Username]=?", (self.username,))
            row = cur.fetchone()
            if row:
                self.first_name_var.set(row[0] or '')
                self.last_name_var.set(row[1] or '')
                self.username_var.set(row[2] or '')
                encrypted_pw = row[3] or ''
                self._original_encrypted_pw = encrypted_pw
                plain = self._decrypt_password(encrypted_pw)
                self.password_var.set(plain if plain is not None else '********')
                if hasattr(self, '_masked_pw_var'):
                    self._masked_pw_var.set('•' * 10 if self.password_var.get() else '')
                self._store_original()
            cur.close()
            conn.close()
            self._loaded = True
            self.status_label.config(text="Loaded at " + datetime.now().strftime('%H:%M:%S'))
        except Exception as e:
            self.status_label.config(text=f"Load failed: {e}")

    def _decrypt_password(self, encrypted):
        if not encrypted:
            return ''
        try:
            spec = importlib.util.spec_from_file_location('fernet_key', self.key_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fernet = Fernet(mod.FERNET_KEY)
            return fernet.decrypt(encrypted.encode()).decode()
        except Exception:
            return None

    def _encrypt_password(self, plain: str):
        spec = importlib.util.spec_from_file_location('fernet_key', self.key_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fernet = Fernet(mod.FERNET_KEY)
        return fernet.encrypt(plain.encode()).decode()

    def _store_original(self):
        self.original_values = {
            'first_name': self.first_name_var.get(),
            'last_name': self.last_name_var.get(),
            'username': self.username_var.get(),
            'password': self.password_var.get(),
        }

    # ---------------- Build Steps -----------------
    def _build_overview_step(self):
        frame = tk.Frame(self.step_frame, bg="#101010")
        center = tk.Frame(frame, bg="#101010")
        center.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(center, text="Account Overview", font=("Segoe UI", 22, "bold"), bg="#101010", fg="#ffcc80").pack(pady=(0, 20))
        grid = tk.Frame(center, bg="#101010")
        grid.pack()
        def add_row(r, label_text, var, mask=False):
            tk.Label(grid, text=label_text+":", font=("Segoe UI", 12, "bold"), bg="#101010", fg="#fffde7").grid(row=r, column=0, sticky='e', padx=(0,10), pady=6)
            lbl = tk.Label(grid, textvariable=var, font=("Segoe UI", 12), bg="#202020", fg="#ffecb3", width=30, anchor='w', padx=10)
            lbl.grid(row=r, column=1, pady=6)
            if mask:
                self._masked_pw_var = tk.StringVar(value='')
                lbl.config(textvariable=self._masked_pw_var)
        add_row(0, "First Name", self.first_name_var)
        add_row(1, "Last Name", self.last_name_var)
        add_row(2, "Username", self.username_var)
        add_row(3, "Password", self.password_var, mask=True)
        tk.Label(center, text="Click 'Edit Account' to modify details and access other steps.", font=("Segoe UI", 10), bg="#101010", fg="#999999").pack(pady=(18,0))
        return frame

    def _ensure_edit_steps(self):
        if len(self.steps) > 1:
            return
        self.steps.append(self._build_profile_step())
        self.steps.append(self._build_security_step())
        self._render_progress(active=self.current_step)

    def _build_profile_step(self):
        frame = tk.Frame(self.step_frame, bg="#101010")
        c = tk.Frame(frame, bg="#101010")
        c.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(c, text="Step 1: Profile", font=("Segoe UI", 18, "bold"), bg="#101010", fg="#ffcc80").pack(pady=(0,16))
        form = tk.Frame(c, bg="#101010")
        form.pack()
        self._add_entry(form, "First Name", self.first_name_var, 0)
        self._add_entry(form, "Last Name", self.last_name_var, 1)
        self._add_entry(form, "Username", self.username_var, 2)
        tk.Label(c, text="Update identification details.", font=("Segoe UI", 10), bg="#101010", fg="#999999").pack(pady=(14,0))
        return frame

    def _build_security_step(self):
        frame = tk.Frame(self.step_frame, bg="#101010")
        c = tk.Frame(frame, bg="#101010")
        c.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(c, text="Step 2: Security", font=("Segoe UI", 18, "bold"), bg="#101010", fg="#ffcc80").pack(pady=(0,16))
        form = tk.Frame(c, bg="#101010")
        form.pack()
        self.password_shown = False
        tk.Label(form, text="Password", bg="#101010", fg="#fffde7", font=("Segoe UI", 11)).grid(row=0, column=0, sticky='w', pady=6)
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, font=("Segoe UI", 11), show='•', width=30, style='Rounded.TEntry')
        self.password_entry.grid(row=0, column=1, pady=6, padx=(0,10))
        ttk.Button(form, text="Show", width=7, command=self.toggle_password, style='Secondary.Rounded.TButton').grid(row=0, column=2, pady=6)
        ttk.Button(form, text="Generate", width=10, command=self.generate_password, style='Accent.Rounded.TButton').grid(row=0, column=3, pady=6, padx=(4,0))
        self.strength_bar = tk.Canvas(form, width=260, height=10, bg="#202020", highlightthickness=0)
        self.strength_bar.grid(row=1, column=1, sticky='w', pady=(4,10))
        self.password_var.trace_add('write', lambda *_: self.update_strength())
        tk.Label(c, text="Use a strong password.", font=("Segoe UI", 10), bg="#101010", fg="#999999").pack(pady=(14,0))
        return frame


    def _add_entry(self, parent, label, var, row):
        tk.Label(parent, text=label, bg="#101010", fg="#fffde7", font=("Segoe UI", 11)).grid(row=row, column=0, sticky='w', pady=6)
        e = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 11), width=30, style='Rounded.TEntry')
        e.grid(row=row, column=1, pady=6, padx=(0,10))
        e.bind('<KeyRelease>', lambda _e: self._mark_changed())

    # ---------------- Navigation -----------------
    def show_step(self, index):
        if index < 0 or index >= len(self.steps):
            return
        if not self.editing_enabled and index != 0:
            return
        for s in self.steps:
            s.pack_forget()
        self.steps[index].pack(fill='both', expand=True)
        self.current_step = index
        self._update_nav_buttons()
        self._render_progress(active=index)
        if not self._loaded:
            self.load_user_data()

    def next_step(self):
        if not self.editing_enabled:
            return
        if self.current_step < len(self.steps)-1:
            self.show_step(self.current_step + 1)
        else:
            self.save_btn.config(state='normal')
            self.status_label.config(text="Review and Save your changes")

    def prev_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def _update_nav_buttons(self):
        if not self.editing_enabled:
            self.back_btn.config(state='disabled')
            self.next_btn.config(state='disabled')
            return
        self.back_btn.config(state='normal' if self.current_step > 1 else 'disabled')
        self.next_btn.config(text='Finish' if self.current_step == len(self.steps)-1 else 'Next ▶')

    def _render_progress(self, active=0):
        for w in self.progress_frame.winfo_children():
            w.destroy()
        names = ["Overview", "Profile", "Security"]
        for i, _ in enumerate(self.steps):
            step_name = names[i] if i < len(names) else f"Step {i+1}"
            wrapper = tk.Frame(self.progress_frame, bg='#000000')
            wrapper.pack(side=tk.LEFT, padx=4)
            color = '#ff6f00' if i == active else '#31363b'
            dot = tk.Canvas(wrapper, width=28, height=28, bg='#000000', highlightthickness=0, cursor='hand2')
            dot.create_oval(4,4,24,24, fill=color, outline=color)
            dot.create_text(14,14, text=str(i+1), fill='#fffde7', font=("Segoe UI", 10, 'bold'))
            dot.pack()
            lbl = tk.Label(wrapper, text=step_name, bg='#000000', fg=('#ffcc80' if i==active else '#bbb'), font=("Segoe UI", 8))
            lbl.pack()
            if i == 0 or self.editing_enabled:
                dot.bind('<Button-1>', lambda _e, idx=i: self._breadcrumb_click(idx))
                lbl.bind('<Button-1>', lambda _e, idx=i: self._breadcrumb_click(idx))

    # ---------------- Features -----------------
    def toggle_password(self):
        if not hasattr(self, 'password_entry'):
            return
        self.password_shown = not getattr(self, 'password_shown', False)
        self.password_entry.config(show='' if self.password_shown else '•')
        self._mark_changed()

    def _breadcrumb_click(self, index):
        if index == 0 or self.editing_enabled:
            self.show_step(index)

    def generate_password(self):
        import random
        import string
        pw = ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(14))
        self.password_var.set(pw)
        if hasattr(self, 'password_entry'):
            self.password_entry.config(show='•')
        self.password_shown = False
        self._mark_changed()

    def update_strength(self):
        if not hasattr(self, 'strength_bar'):
            return
        val = self.password_var.get()
        self.strength_bar.delete('all')
        if not val:
            return
        score = 0
        score += any(c.islower() for c in val)
        score += any(c.isupper() for c in val)
        score += any(c.isdigit() for c in val)
        score += any(c in '!@#$%^&*' for c in val)
        score += len(val) >= 12
        colors = ['#8d6e63', '#ff9800', '#ffc107', '#8bc34a', '#4caf50']
        w = int((score/5) * 260)
        self.strength_bar.create_rectangle(0,0,w,10, fill=colors[score-1] if score>0 else '#444444', outline='')

    def _mark_changed(self, *_):
        self.changed = True
        self.save_btn.config(state='normal')
        self.cancel_btn.config(state='normal')

    def cancel_changes(self):
        if not self.changed:
            if self.editing_enabled:
                self._exit_edit_mode()
            return
        if messagebox.askyesno("Discard Changes", "Revert all unsaved changes?"):
            self.first_name_var.set(self.original_values.get('first_name',''))
            self.last_name_var.set(self.original_values.get('last_name',''))
            self.username_var.set(self.original_values.get('username',''))
            self.password_var.set(self.original_values.get('password',''))
            self.changed = False
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            self.status_label.config(text="Reverted")
            self._exit_edit_mode()

    def save_changes(self):
        if not self.username:
            messagebox.showerror("Error", "No session username.")
            return
        try:
            if not all([self.first_name_var.get().strip(), self.last_name_var.get().strip(), self.username_var.get().strip(), self.password_var.get().strip()]):
                messagebox.showerror("Error", "All fields are required.")
                return
            conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' f'DBQ={self.db_path};')
            conn = pyodbc.connect(conn_str)
            cur = conn.cursor()
            encrypted_pw = self._encrypt_password(self.password_var.get().strip())
            original_username = getattr(self.app.parent, 'username', self.username)
            cur.execute("""
                UPDATE [emp_list]
                SET [First Name]=?, [Last Name]=?, [Username]=?, [Password]=?
                WHERE [Username]=?
            """, (
                self.first_name_var.get().strip(),
                self.last_name_var.get().strip(),
                self.username_var.get().strip(),
                encrypted_pw,
                original_username
            ))
            conn.commit()
            cur.close()
            conn.close()
            if hasattr(self.app.parent, 'username'):
                self.app.parent.username = self.username_var.get().strip()
            self.username = self.app.parent.username
            self._store_original()
            self.changed = False
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            self.status_label.config(text="Saved at " + datetime.now().strftime('%H:%M:%S'))
            messagebox.showinfo("Success", "Account settings saved.")
            self._exit_edit_mode()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")


    # ---------------- Public Helpers -----------------
    def enable_edit(self):
        if len(self.steps) > 1:
            prof = self.steps[1]
            for child in prof.winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Entry):
                        sub.focus_set()
                        return

    def toggle_password_visibility(self):
        self.toggle_password()

    def show(self):
        self.container.pack(fill='both', expand=True)
        if hasattr(self, '_masked_pw_var') and self.password_var.get():
            self._masked_pw_var.set('•' * 10)

    # ---------------- Editing Mode -----------------
    def start_editing(self):
        """Enter editing mode: reveal remaining steps & navigation."""
        self.editing_enabled = True
        self._ensure_edit_steps()
        self.edit_start_btn.pack_forget()
        self.back_btn.pack(side=tk.RIGHT, padx=4)
        self.next_btn.pack(side=tk.RIGHT, padx=4)
        self.save_btn.pack(side=tk.RIGHT, padx=4)
        self.cancel_btn.pack(side=tk.RIGHT, padx=4)
        self.next_btn.config(state='normal')
        self.show_step(1)
        self.status_label.config(text="Editing mode enabled")
        self._render_progress(active=self.current_step)

    def _exit_edit_mode(self):
        self.editing_enabled = False
        for btn in (self.back_btn, self.next_btn, self.save_btn, self.cancel_btn):
            btn.pack_forget()
        if not self.edit_start_btn.winfo_ismapped():
            self.edit_start_btn.pack(side=tk.RIGHT, padx=4)
        self.show_step(0)
        self.status_label.config(text="Viewing mode")
        self.changed = False
        if hasattr(self, '_masked_pw_var'):
            self._masked_pw_var.set('•' * 10 if self.password_var.get() else '')
        self._render_progress(active=self.current_step)

    # ---------------- Styles -----------------
    def _init_styles(self):
        try:
            style = ttk.Style()
            if 'clam' in style.theme_names():
                style.theme_use('clam')
            style.configure('Rounded.TEntry', fieldbackground='#202020', foreground='#ffecb3', insertcolor='#ffecb3', padding=6, relief='flat')
            common = dict(font=("Segoe UI", 10, 'bold'), padding=(12,6))
            style.configure('Accent.Rounded.TButton', background='#ff6f00', foreground='#fffde7', **common)
            style.map('Accent.Rounded.TButton', background=[('active', '#ff8124')])
            style.configure('Secondary.Rounded.TButton', background='#31363b', foreground='#fffde7', **common)
            style.map('Secondary.Rounded.TButton', background=[('active', '#3f464d')])
            style.configure('Success.Rounded.TButton', background='#2e7d32', foreground='#fffde7', **common)
            style.map('Success.Rounded.TButton', background=[('active', '#388e3c')])
            style.configure('Danger.Rounded.TButton', background='#c62828', foreground='#fffde7', **common)
            style.map('Danger.Rounded.TButton', background=[('active', '#d32f2f')])
        except Exception:
            pass