import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pyotp
import os
# Sound imports removed

class UserRolesManager:
    def __init__(self, parent_settings, settings_win):
        self.parent_settings = parent_settings
        self.settings_win = settings_win
        self.user_tree = None
        self.original_user_data = {}
        self.save_roles_btn = None
        self.cancel_roles_btn = None
        # Wizard / state placeholders
        self._wizard_frame = None
        self._wizard_content = None
        self._wizard_active = False
        self._wizard_prev_focus = None
        self._wizard_steps = []
        self._wizard_step_index = 0
        self._wizard_flow_data = {}

    # --------------------------- Wizard Framework ---------------------------
    def _ensure_wizard_frame(self):
        if self._wizard_frame and self._wizard_frame.winfo_exists():
            return
        if not self.settings_win:
            return
        self._wizard_frame = tk.Frame(self.settings_win, bg="#101010")
        self._wizard_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._wizard_content = None
        self._wizard_active = True

    def _hide_wizard(self):
        try:
            if self._wizard_content and self._wizard_content.winfo_exists():
                self._wizard_content.destroy()
        except Exception:
            pass
        try:
            if self._wizard_frame and self._wizard_frame.winfo_exists():
                self._wizard_frame.destroy()
        except Exception:
            pass
        self._wizard_frame = None
        self._wizard_content = None
        self._wizard_active = False
        self._wizard_prev_focus = None
        self._wizard_flow_data = {}

    def _show_current_wizard_step(self):
        if not self._wizard_steps:
            return
        if self._wizard_content and self._wizard_content.winfo_exists():
            try:
                self._wizard_content.destroy()
            except Exception:
                pass
        self._wizard_content = tk.Frame(self._wizard_frame, bg="#101010")
        self._wizard_content.pack(fill='both', expand=True)
        try:
            step_fn = self._wizard_steps[self._wizard_step_index]
            step_fn(self._wizard_content, self._hide_wizard)
        except Exception as e:
            print(f"[DEBUG] Wizard step error: {e}")

    def _wizard_go_next(self):
        if self._wizard_step_index < len(self._wizard_steps)-1:
            self._wizard_step_index += 1
            self._show_current_wizard_step()

    def _wizard_go_back(self):
        if self._wizard_step_index > 0:
            self._wizard_step_index -= 1
            self._show_current_wizard_step()

    # ---------------- Add Employee Steps ----------------
    def _wizard_add_emp_step_details(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(frm, text='New Employee - Details', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
        for label, key in [('First Name','first_name'),('Last Name','last_name'),('Username','username')]:
            row = tk.Frame(frm, bg="#101010")
            row.pack(fill='x', pady=6)
            tk.Label(row, text=label, font=("Segoe UI",11), bg="#101010", fg="#fffde7").pack(anchor='w')
            var = tk.StringVar(value=d.get(key,''))
            ent = tk.Entry(row, textvariable=var, font=("Segoe UI",11), bg="#23272b", fg="#fffde7", relief='flat', insertbackground='#fffde7')
            ent.pack(fill='x', ipady=6)
            d[key+'_var'] = var
        lvl_row = tk.Frame(frm, bg="#101010")
        lvl_row.pack(fill='x', pady=6)
        tk.Label(lvl_row, text='Access Level', font=("Segoe UI",11), bg="#101010", fg="#fffde7").pack(anchor='w')
        d['access_level_var'] = tk.StringVar(value=d.get('access_level','Level 1'))
        ttk.Combobox(lvl_row, textvariable=d['access_level_var'], values=["Level 1","Level 2","Level 3"], state='readonly').pack(fill='x', ipady=3)
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=20)
        tk.Button(nav, text='Cancel', command=self._hide_wizard, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        tk.Button(nav, text='Next ▶', command=lambda: self._add_emp_details_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')

    def _add_emp_details_next(self):
        d = self._wizard_flow_data
        d['first_name'] = d['first_name_var'].get().strip()
        d['last_name'] = d['last_name_var'].get().strip()
        d['username'] = d['username_var'].get().strip()
        d['access_level'] = d['access_level_var'].get()
        if not d['first_name'] or not d['last_name'] or not d['username']:
            messagebox.showerror('Validation','All fields required.')
            return
        # Simple uniqueness check
        for _, info in self.original_user_data.items():
            if info['username'].lower() == d['username'].lower():
                messagebox.showerror('Validation','Username already exists.')
                return
        self._wizard_go_next()

    def _wizard_add_emp_step_credentials(self, parent, close_cb):
            d = self._wizard_flow_data
            frm = tk.Frame(parent, bg="#101010")
            frm.pack(fill='both', expand=True, padx=20, pady=20)
            tk.Label(frm, text='Set Credentials', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
            tk.Label(frm, text='Enter a temporary password (user can change later).', font=("Segoe UI",10), bg="#101010", fg="#bbb").pack(anchor='w')
            d['password_var'] = tk.StringVar(value='')
            tk.Entry(frm, textvariable=d['password_var'], show='•', font=("Segoe UI",11), bg="#23272b", fg="#fffde7", relief='flat', insertbackground='#fffde7').pack(fill='x', ipady=6, pady=(12,0))
            nav = tk.Frame(frm, bg="#101010")
            nav.pack(fill='x', pady=20)
            tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
            tk.Button(nav, text='Next ▶', command=lambda: self._wizard_go_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')


    def _wizard_add_emp_step_confirm(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=30, pady=30)
        tk.Label(frm, text='Confirm New Employee', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,15))
        summary = f"Username: {d.get('username')}\nName: {d.get('first_name')} {d.get('last_name')}\nAccess Level: {d.get('access_level')}"
        tk.Label(frm, text=summary, font=("Segoe UI",11), bg="#101010", fg="#fffde7", justify='left').pack(anchor='w')
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=30)
        tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        def finalize():
            pwd = d.get('password_var').get().strip() if d.get('password_var') else ''
            if not pwd:
                messagebox.showerror('Validation','Password required.')
                return
            if hasattr(self,'add_employee_to_database'):
                res = self.add_employee_to_database(d['first_name'], d['last_name'], d['username'], pwd, d['access_level'])
                success = res[0] if isinstance(res, tuple) else bool(res)
                msg = res[1] if isinstance(res, tuple) and len(res) > 1 else ''
            else:
                success, msg = False, 'Missing add method'
            if success:
                messagebox.showinfo('Success','Employee added successfully.')
                self._hide_wizard()
                self.load_user_data()
            else:
                messagebox.showerror('Error', f'Failed to add employee: {msg}')
        tk.Button(nav, text='Finish & Add', command=finalize, bg="#28a745", fg="#fff", relief='flat', width=18).pack(side='right')

    # ---------------- Launchers ----------------
    def launch_add_employee_wizard(self):
        self._ensure_wizard_frame()
        self._wizard_flow_data = {}
        self._wizard_steps = [
            self._wizard_add_emp_step_details,
            self._wizard_add_emp_step_credentials,
            self._wizard_add_emp_step_confirm
        ]
        self._wizard_step_index = 0
        self._show_current_wizard_step()

    def launch_edit_employee_wizard(self):
        if not self.user_tree or not self.user_tree.selection():
            messagebox.showwarning('Edit Employee','Select an employee first.')
            return
        sel = self.user_tree.selection()[0]
        orig = self.original_user_data.get(sel)
        if not orig:
            messagebox.showerror('Edit Employee','Original data not found.')
            return
        self._ensure_wizard_frame()
        self._wizard_flow_data = {'orig': orig}
        self._wizard_steps = [
            self._wizard_edit_emp_step_details,
            self._wizard_edit_emp_step_credentials,
            self._wizard_edit_emp_step_confirm
        ]
        self._wizard_step_index = 0
        self._show_current_wizard_step()

    def launch_bulk_operations_wizard(self):
        if not self.original_user_data:
            messagebox.showinfo('Bulk Operations','No employees loaded.')
            return
        self._ensure_wizard_frame()
        self._wizard_flow_data = {'selected': set()}
        self._wizard_steps = [
            self._wizard_bulk_step_select,
            self._wizard_bulk_step_configure,
            self._wizard_bulk_step_confirm
        ]
        self._wizard_step_index = 0
        self._show_current_wizard_step()

    # ---------------- Edit Employee Steps ----------------
    def _wizard_edit_emp_step_details(self, parent, close_cb):
        d = self._wizard_flow_data
        orig = d['orig']
        d['first_name'] = d.get('first_name', orig['first_name'])
        d['last_name'] = d.get('last_name', orig['last_name'])
        d['username'] = d.get('username', orig['username'])
        d['access_level'] = d.get('access_level', orig['access_level'])
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(frm, text='Edit Employee Details', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
        def field(label, key, readonly=False):
            row = tk.Frame(frm, bg="#101010")
            row.pack(fill='x', pady=6)
            tk.Label(row, text=label, font=("Segoe UI",11), bg="#101010", fg="#fffde7").pack(anchor='w')
            var = tk.StringVar(value=d[key])
            ent = tk.Entry(row, textvariable=var, font=("Segoe UI",11), bg="#23272b", fg="#fffde7", relief='flat', insertbackground='#fffde7', state='readonly' if readonly else 'normal')
            ent.pack(fill='x', ipady=6)
            d[key+'_var'] = var
        field('First Name','first_name')
        field('Last Name','last_name')
        field('Username','username')
        lvl_row = tk.Frame(frm, bg="#101010")
        lvl_row.pack(fill='x', pady=6)
        tk.Label(lvl_row, text='Access Level', font=("Segoe UI",11), bg="#101010", fg="#fffde7").pack(anchor='w')
        d['access_level_var'] = tk.StringVar(value=d['access_level'])
        ttk.Combobox(lvl_row, textvariable=d['access_level_var'], values=["Level 1","Level 2","Level 3"], state='readonly').pack(fill='x', ipady=3)
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=20)
        tk.Button(nav, text='Cancel', command=self._hide_wizard, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        tk.Button(nav, text='Next ▶', command=lambda: self._edit_emp_step_details_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')
    def _edit_emp_step_details_next(self):
        d = self._wizard_flow_data
        d['first_name'] = d['first_name_var'].get().strip()
        d['last_name'] = d['last_name_var'].get().strip()
        d['username'] = d['username_var'].get().strip()
        d['access_level'] = d['access_level_var'].get()
        if not d['first_name'] or not d['last_name'] or not d['username']:
            messagebox.showerror('Validation','All fields required.')
            return
        self._wizard_go_next()
    def _wizard_edit_emp_step_credentials(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(frm, text='Optional New Password', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
        tk.Label(frm, text='Leave blank to keep the existing password.', font=("Segoe UI",10), bg="#101010", fg="#bbb").pack(anchor='w')
        d['password_var'] = tk.StringVar(value='')
        ent = tk.Entry(frm, textvariable=d['password_var'], show='•', font=("Segoe UI",11), bg="#23272b", fg="#fffde7", relief='flat', insertbackground='#fffde7')
        ent.pack(fill='x', ipady=6, pady=(12,0))
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=20)
        tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        tk.Button(nav, text='Next ▶', command=lambda: self._wizard_go_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')
        ent.focus_set()
    def _wizard_edit_emp_step_confirm(self, parent, close_cb):
        d = self._wizard_flow_data
        o = d['orig']
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=30, pady=30)
        tk.Label(frm, text='Confirm Changes', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,15))
        summary = (f"Original Username: {o['username']}\nNew Username: {d['username']}\nName: {d['first_name']} {d['last_name']}\nAccess Level: {d['access_level']}")
        tk.Label(frm, text=summary, font=("Segoe UI",11), bg="#101010", fg="#fffde7", justify='left').pack(anchor='w')
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=30)
        tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        def apply_changes():
            new_pw = d['password_var'].get().strip() or None
            res = self.update_employee_in_database(o['username'], d['first_name'], d['last_name'], d['username'] if d['username']!=o['username'] else None, new_pw, d['access_level']) if hasattr(self,'update_employee_in_database') else (False,'Missing update method')
            if isinstance(res, tuple):
                success, msg = res
            else:
                success, _ = (True,'')
            if success:
                messagebox.showinfo('Success','Employee updated successfully.')
                self._hide_wizard()
                self.load_user_data()
            else:
                messagebox.showerror('Error', f'Failed to update employee: {msg}')
        tk.Button(nav, text='Finish & Save', command=apply_changes, bg="#28a745", fg="#fff", relief='flat', width=18).pack(side='right')

    # ---------------- Bulk Operations Steps ----------------
    def _wizard_bulk_step_select(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(frm, text='Select Employees', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
        tk.Label(frm, text='Double-click to toggle selection.', font=("Segoe UI",10), bg="#101010", fg="#bbb").pack(anchor='w', pady=(0,10))
        columns=('Name','Username','Level','Sel')
        tv = ttk.Treeview(frm, columns=columns, show='headings', height=14)
        for c, w in zip(columns,(180,140,80,50)):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor='center')
        tv.pack(fill='both', expand=True)
        d['bulk_tree'] = tv
        current_username = getattr(self.parent_settings.parent, 'username', None)
        for item_id, u in self.original_user_data.items():
            if current_username and u['username'].lower() == current_username.lower():
                continue
            name = f"{u['first_name']} {u['last_name']}".strip()
            tv.insert('', 'end', values=(name, u['username'], u['access_level'], '☐'))
        def toggle(event):
            iid = tv.identify_row(event.y)
            if not iid:
                return
            vals = list(tv.item(iid,'values'))
            if vals[3] == '☐':
                vals[3] = '☑'
                d['selected'].add(vals[1])
            else:
                vals[3] = '☐'
                d['selected'].discard(vals[1])
            tv.item(iid, values=vals)
        tv.bind('<Double-1>', toggle)
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=10)
        tk.Button(nav, text='Cancel', command=self._hide_wizard, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        tk.Button(nav, text='Next ▶', command=lambda: self._bulk_select_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')
    def _bulk_select_next(self):
        if not self._wizard_flow_data['selected']:
            messagebox.showwarning('No Selection','Select at least one employee.')
            return
        self._wizard_go_next()
    def _wizard_bulk_step_configure(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(frm, text='Configure Operation', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,10))
        d['new_level_var'] = tk.StringVar(value=d.get('new_level','Level 1'))
        row = tk.Frame(frm, bg="#101010")
        row.pack(fill='x', pady=8)
        tk.Label(row, text='New Access Level', font=("Segoe UI",11), bg="#101010", fg="#fffde7").pack(anchor='w')
        ttk.Combobox(row, textvariable=d['new_level_var'], values=["Level 1","Level 2","Level 3"], state='readonly').pack(fill='x', ipady=3)
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=20)
        tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        tk.Button(nav, text='Next ▶', command=lambda: self._bulk_config_next(), bg="#ff6f00", fg="#fff", relief='flat', width=14).pack(side='right')
    def _bulk_config_next(self):
        self._wizard_flow_data['new_level'] = self._wizard_flow_data['new_level_var'].get()
        self._wizard_go_next()
    def _wizard_bulk_step_confirm(self, parent, close_cb):
        d = self._wizard_flow_data
        frm = tk.Frame(parent, bg="#101010")
        frm.pack(fill='both', expand=True, padx=30, pady=30)
        tk.Label(frm, text='Confirm Bulk Operation', font=("Segoe UI",16,'bold'), bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0,15))
        summary = f"Employees: {len(d['selected'])}\nNew Access Level: {d['new_level']}"
        tk.Label(frm, text=summary, font=("Segoe UI",11), bg="#101010", fg="#fffde7", justify='left').pack(anchor='w')
        nav = tk.Frame(frm, bg="#101010")
        nav.pack(fill='x', pady=30)
        tk.Button(nav, text='◀ Back', command=self._wizard_go_back, bg="#444", fg="#fff", relief='flat', width=12).pack(side='left')
        def apply_bulk():
            successes = 0
            failures = []
            for uname in list(d['selected']):
                u = None
                for oid, ou in self.original_user_data.items():
                    if ou['username'] == uname:
                        u = ou
                        break
                if not u:
                    continue
                res = self.update_employee_in_database(uname, u['first_name'], u['last_name'], None, None, d['new_level']) if hasattr(self,'update_employee_in_database') else (False,'Missing update method')
                if isinstance(res, tuple):
                    success, msg = res
                else:
                    success = True
                if success:
                    successes += 1
                else:
                    failures.append(uname)
            if successes:
                extra = f" Failed: {', '.join(failures)}" if failures else ''
                messagebox.showinfo('Bulk Operation', f'Successfully updated {successes} employee(s).{extra}')
                self._hide_wizard()
                self.load_user_data()
            else:
                failure_list = ', '.join(failures) if failures else 'Unknown error'
                messagebox.showerror('Bulk Operation', f'Failed to update employees: {failure_list}')
        tk.Button(nav, text='Finish & Apply', command=apply_bulk, bg="#28a745", fg="#fff", relief='flat', width=18).pack(side='right')

    # ---------------------- Refactored Dialog Pages ------------------------
    def _page_authenticate_demotion(self, parent, close_cb, target_username, user_display_name, old_level, new_level, result_var):
        """Build authentication (password + optional 2FA) page for demotion."""
        wrapper = tk.Frame(parent, bg="#101010")
        wrapper.pack(fill='both', expand=True)
        tk.Label(wrapper, text="Authenticate Demotion", font=("Segoe UI", 18, "bold"),
                 bg="#101010", fg="#ff8c00").pack(anchor='w', pady=(0, 10))
        tk.Label(wrapper, text=f"User: {user_display_name}\nChanging: {old_level} → {new_level}",
                 font=("Segoe UI", 12), bg="#101010", fg="#e0e0e0", justify='left').pack(anchor='w', pady=(0, 15))

        form = tk.Frame(wrapper, bg="#101010")
        form.pack(anchor='w')
        tk.Label(form, text="Password:", font=("Segoe UI", 10, "bold"), bg="#101010", fg="#cccccc").grid(row=0, column=0, sticky='w')
        pwd_var = tk.StringVar()
        tk.Entry(form, textvariable=pwd_var, show='*', width=40, bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff").grid(row=1, column=0, pady=(2, 12), sticky='w')

        tk.Label(form, text="2FA Code (if enabled):", font=("Segoe UI", 10, "bold"), bg="#101010", fg="#cccccc").grid(row=2, column=0, sticky='w')
        otp_var = tk.StringVar()
        tk.Entry(form, textvariable=otp_var, width=25, bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff").grid(row=3, column=0, pady=(2, 20), sticky='w')

        status_var = tk.StringVar(value="Enter credentials to proceed.")
        tk.Label(wrapper, textvariable=status_var, font=("Segoe UI", 9), bg="#101010", fg="#888888").pack(anchor='w', pady=(0, 10))

        btn_bar = tk.Frame(wrapper, bg="#101010")
        btn_bar.pack(fill='x', pady=(10, 0))

        def do_cancel():
            result_var.set(0)
            close_cb()

        def do_auth():
            password = pwd_var.get().strip()
            otp_code = otp_var.get().strip()
            if not password:
                status_var.set("Password required.")
                return
            # Reuse existing verification helpers
            if not self.verify_target_user_credentials(target_username, password):
                status_var.set("Invalid password.")
                return
            if otp_code:
                if not self.verify_target_user_credentials_flexible(target_username, password, otp_code):
                    status_var.set("Invalid password / 2FA combination.")
                    return
            result_var.set(1)
            close_cb()

        tk.Button(btn_bar, text="Cancel", command=do_cancel, bg="#444444", fg="#ffffff", relief='flat', width=14).pack(side='left')
        tk.Button(btn_bar, text="Authenticate", command=do_auth, bg="#ff6f00", fg="#ffffff", relief='flat', width=18).pack(side='right')

    def _page_2fa_info(self, parent, close_cb, username, otp_secret):
        wrapper = tk.Frame(parent, bg="#101010")
        wrapper.pack(fill='both', expand=True)
        tk.Label(wrapper, text="🔐 2FA Setup Complete", font=("Segoe UI", 20, "bold"), bg="#101010", fg="#00ff88").pack(pady=(0, 10))
        tk.Label(wrapper, text=f"User: {username}", font=("Segoe UI", 12), bg="#101010", fg="#ffffff").pack()
        tk.Label(wrapper, text="Secret (store securely):", font=("Segoe UI", 11, "bold"), bg="#101010", fg="#ffcc00").pack(pady=(20, 4))
        secret_box = tk.Text(wrapper, height=2, width=50, bg="#1e1e1e", fg="#00ff88", relief='flat')
        secret_box.insert('1.0', otp_secret)
        secret_box.config(state='disabled')
        secret_box.pack()
        tk.Label(wrapper, text="Add this secret to an Authenticator app (TOTP).", font=("Segoe UI", 10), bg="#101010", fg="#cccccc").pack(pady=10)
        tk.Button(wrapper, text="Close", command=close_cb, bg="#ff6f00", fg="#ffffff", relief='flat', width=16).pack(pady=20)

    def create_full_interface(self, parent):
        """Build the main user roles management interface (Level 3)."""
        container = tk.Frame(parent, bg="#000000")
        container.pack(fill='both', expand=True, padx=18, pady=8)

        # Instructions
        inst = tk.Frame(container, bg="#000000")
        inst.pack(fill='x', pady=(0,10))
        tk.Label(inst, text="Instructions: Right-click on any user to change their access level.", font=("Segoe UI",10), bg="#000000", fg="#999", wraplength=600).pack(anchor='w')

        # Search
        srow = tk.Frame(container, bg="#000000")
        srow.pack(fill='x', pady=(0,10))
        tk.Label(srow, text="Search employees:", font=("Segoe UI",10), bg="#000000", fg="#fffde7").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_users)
        tk.Entry(srow, textvariable=self.search_var, font=("Segoe UI",10), bg="#23272b", fg="#fffde7", insertbackground="#fffde7", relief='flat', bd=1, width=30).pack(side='left', padx=(10,0), ipady=3)
        tk.Button(srow, text='Clear', font=("Segoe UI",9), bg='#666', fg='#fff', relief='flat', activebackground='#555', activeforeground='#fff', command=self.clear_search).pack(side='left', padx=(5,0))

        # Stats
        stats = tk.Frame(container, bg="#000000")
        stats.pack(fill='x', pady=(0,10))
        self.stats_label = tk.Label(stats, text='', font=("Segoe UI",9), bg="#000000", fg="#999")
        self.stats_label.pack(anchor='w')

        # Table
        tframe = tk.Frame(container, bg="#000000")
        tframe.pack(fill='both', expand=True, pady=(0,10))
        cols = ('Last Name','First Name','Access Level')
        self.user_tree = ttk.Treeview(tframe, columns=cols, show='headings', height=12)
        style = ttk.Style()
        style.configure('Treeview', background='#23272b', foreground='#fffde7', fieldbackground='#23272b')
        style.configure('Treeview.Heading', background='#2d3136', foreground='#fffde7', font=("Segoe UI",10,'bold'))
        style.configure('Modified.Treeview', background='#2d4a3e', foreground='#a8d8a8', fieldbackground='#2d4a3e')
        style.map('Modified.Treeview', background=[('selected','#4a6741')])
        for c in cols:
            self.user_tree.heading(c, text=f'{c} ↕', command=lambda col=c: self.sort_treeview(col))
        self.user_tree.column('Last Name', width=150, anchor='w')
        self.user_tree.column('First Name', width=150, anchor='w')
        self.user_tree.column('Access Level', width=120, anchor='center')
        vsb = ttk.Scrollbar(tframe, orient='vertical', command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        self.user_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # Buttons
        btn_row = tk.Frame(container, bg='#000000')
        btn_row.pack(anchor='e', pady=(10,0))
        mg = tk.Frame(btn_row, bg='#000000')
        mg.pack(side=tk.LEFT, padx=(0,20))
        self.add_emp_btn = tk.Button(mg, text='Add Employee', font=("Segoe UI",10), bg='#28a745', fg='#fff', relief='flat', activebackground='#218838', activeforeground='#fff', width=12, command=self.launch_add_employee_wizard)
        self.add_emp_btn.pack(side=tk.LEFT, padx=(0,5))
        self.remove_emp_btn = tk.Button(mg, text='Remove Employee', font=("Segoe UI",10), bg='#dc3545', fg='#fff', relief='flat', activebackground='#c82333', activeforeground='#fff', width=12, command=self.remove_employee_dialog)
        self.remove_emp_btn.pack(side=tk.LEFT, padx=(0,5))
        self.edit_emp_btn = tk.Button(mg, text='Edit Employee', font=("Segoe UI",10), bg='#ffc107', fg='#000', relief='flat', activebackground='#e0a800', activeforeground='#000', width=12, command=self.launch_edit_employee_wizard)
        self.edit_emp_btn.pack(side=tk.LEFT, padx=(0,5))
        self.bulk_ops_btn = tk.Button(mg, text='Bulk Operations', font=("Segoe UI",10), bg='#6f42c1', fg='#fff', relief='flat', activebackground='#5a36a1', activeforeground='#fff', width=12, command=self.launch_bulk_operations_wizard)
        self.bulk_ops_btn.pack(side=tk.LEFT)
        self.cancel_roles_btn = tk.Button(btn_row, text='Cancel', font=("Segoe UI",11), bg='#666', fg='#fff', relief='flat', activebackground='#555', activeforeground='#fff', width=12, command=self.cancel_changes)
        self.cancel_roles_btn.pack(side=tk.RIGHT, padx=(10,0))
        self.save_roles_btn = tk.Button(btn_row, text='💾 Save Changes', font=("Segoe UI",10), bg='#6c757d', fg='white', relief='flat', activebackground='#5a6268', activeforeground='#fff', width=15, command=self.save_changes_simplified)
        self.save_roles_btn.pack(side=tk.RIGHT)

        # Bindings
        self.user_tree.bind('<Button-3>', self.on_right_click)
        self.user_tree.bind('<F5>', lambda e: self.refresh_data())
        self.user_tree.bind('<Delete>', self.delete_key_pressed)
        self.user_tree.bind('<Return>', self.enter_key_pressed)
        self.user_tree.bind('<Control-p>', lambda e: self.show_pending_changes_summary())
        self.user_tree.bind('<Double-1>', lambda e: self.launch_edit_employee_wizard() if self.user_tree.selection() else None)

        # Shortcuts info
        sc = tk.Frame(container, bg='#000000')
        sc.pack(fill='x', pady=(5,0))
        tk.Label(sc, text='💡 Shortcuts: F5=Refresh | Delete=Remove | Enter=Edit | Double-click=Edit | Right-click=Context Menu | Ctrl+P=Show Pending Changes', font=("Segoe UI",8), bg='#000000', fg='#666').pack(anchor='w')
        ci = tk.Frame(container, bg='#000000')
        ci.pack(fill='x', pady=(2,0))
        tk.Label(ci, text='📝 Changes are temporary until saved. Modified rows show ● symbol. Window title shows * when unsaved.', font=("Segoe UI",8), bg='#000000', fg='#888').pack(anchor='w')

        try:
            (self.settings_win or container).after(0, self.load_user_data)
        except Exception:
            pass
        return container

    # Backwards compatibility for callers expecting create_user_roles_frame
    def create_user_roles_frame(self, parent):
        return self.create_full_interface(parent)

    def sort_treeview(self, column):
        """Sort treeview by column"""
        try:
            # Toggle sort direction if same column clicked, otherwise default to ascending
            if self.sort_column == column:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_reverse = False
            
            self.sort_column = column
            
            # Get all items and their data
            items_data = []
            for item in self.user_tree.get_children():
                values = self.user_tree.item(item)['values']
                items_data.append((item, values))
            
            # Map column names to indices
            column_index = {
                'Last Name': 0,
                'First Name': 1, 
                'Access Level': 2
            }
            
            # Sort the data
            if column in column_index:
                idx = column_index[column]
                items_data.sort(key=lambda x: str(x[1][idx]).lower(), reverse=self.sort_reverse)
            
            # Update header text to show sort direction
            sort_arrow = ' ↓' if self.sort_reverse else ' ↑'
            for col in ['Last Name', 'First Name', 'Access Level']:
                if col == column:
                    self.user_tree.heading(col, text=f'{col}{sort_arrow}')
                else:
                    self.user_tree.heading(col, text=f'{col} ↕')
            
            # Reorder items in treeview
            for index, (item, values) in enumerate(items_data):
                self.user_tree.move(item, '', index)
                
        except Exception as e:
            print(f"[DEBUG] Error sorting treeview: {e}")

    def load_user_data(self):
        """Load user data and populate the table"""
        print("[DEBUG] load_user_data called")

        if not self.user_tree:
            print("[DEBUG] user_tree not available, scheduling retry...")
            if hasattr(self, 'settings_win') and self.settings_win:
                self.settings_win.after(50, self.load_user_data)
            return
        # Clear existing data and reset state
        try:
            self.user_tree.delete(*self.user_tree.get_children())
        except Exception:
            pass
        self.original_user_data.clear()
        self.sort_column = None
        self.sort_reverse = False
        self.has_pending_changes = False
        self.pending_changes.clear()
        try:
            self.user_tree.heading('Last Name', text='Last Name ↕')
            self.user_tree.heading('First Name', text='First Name ↕')
            self.user_tree.heading('Access Level', text='Access Level ↕')
        except Exception:
            pass

        from database import get_connector, get_db_path
        connector = None
        try:
            connector = get_connector(get_db_path())
            rows = connector.fetchall(
                "SELECT [Last Name], [First Name], [Middle Name], [Username], [Access Level] FROM [emp_list] ORDER BY [Last Name], [First Name]"
            )
            for row in rows:
                last_name = row[0] or ""
                first_name = row[1] or ""
                access_level = row[4] or "Level 1"
                item_id = self.user_tree.insert('', 'end', values=(last_name, first_name, access_level))
                self.original_user_data[item_id] = {
                    'last_name': last_name,
                    'first_name': first_name,
                    'middle_name': row[2] or "",
                    'username': row[3] or "",
                    'access_level': access_level
                }
            print(f"[DEBUG] Loaded {len(rows)} user records")
        except Exception as e:
            print(f"[DEBUG] Error loading user data: {e}")
        finally:
            try:
                if connector:
                    connector.close()
            except Exception:
                pass

    def save_changes_test(self):
        """Test save method without authentication to debug freezing"""
        print("[DEBUG] Starting test save process...")
        changes = []

        # Check for changes
        for item_id in self.user_tree.get_children():
            values = self.user_tree.item(item_id)['values']
            if item_id in self.original_user_data:
                original_data = self.original_user_data[item_id]
                current_level = values[2]
                if current_level != original_data['access_level']:
                    changes.append({
                        'item_id': item_id,
                        'username': original_data['username'],
                        'first_name': original_data['first_name'],
                        'last_name': original_data['last_name'],
                        'old_level': original_data['access_level'],
                        'new_level': current_level
                    })

        if not changes:
            messagebox.showinfo("No Changes", "No changes to save.")
            return

        print(f"[DEBUG] Found {len(changes)} changes to save (test mode)")

        print("[DEBUG] Connecting to database (test mode)...")
        from database import get_connector, get_db_path
        connector = None
        try:
            connector = get_connector(get_db_path())
            for i, change in enumerate(changes):
                print(f"[DEBUG] Processing change {i+1}/{len(changes)}: {change['username']} -> {change['new_level']}")
                connector.execute_query(
                    "UPDATE [emp_list] SET [Access Level]=? WHERE [Username]=?",
                    (change['new_level'], change['username'])
                )
            print("[DEBUG] Test save completed successfully")
            messagebox.showinfo("Success", f"Successfully updated {len(changes)} user(s) (test mode).")
            self.load_user_data()
        except Exception as e:
            print(f"[DEBUG] Test save error: {e}")
            messagebox.showerror("Error", f"Failed to save changes: {e}")
        finally:
            try:
                if connector:
                    connector.close()
            except Exception:
                pass
            # Recalculate final Level 3 count after proposed changes
            final_level_3_count = 0
            for item_id2 in self.user_tree.get_children():
                values2 = self.user_tree.item(item_id2)['values']
                future_level = values2[2]
                # Apply pending change if this row is in changes list
                for ch in changes:
                    if ch['item_id'] == item_id2:
                        future_level = ch['new_level']
                        break
                if future_level == 'Level 3':
                    final_level_3_count += 1
            if final_level_3_count == 0:
                messagebox.showerror("Invalid Operation",
                                     "Cannot save changes: This would result in no Level 3 users remaining in the system.\n\n"
                                     "You must promote at least one other user to Level 3 before demoting yourself.")
                return
        
        # Check for sensitive changes requiring authentication
        demotion_changes = [c for c in changes if c['old_level'] in ['Level 2', 'Level 3'] and c['new_level'] == 'Level 1']
        promotion_changes = [c for c in changes if c['old_level'] == 'Level 1' and c['new_level'] in ['Level 2', 'Level 3']]
        
        # Require authentication for demotions (target user credentials)
        if demotion_changes:
            if not self.authenticate_sensitive_changes(demotion_changes):
                return
        
        # Require authentication for promotions (current admin credentials)
        if promotion_changes:
            if not self.authenticate_admin_promotions(promotion_changes):
                return
        
        # Apply changes to database
        conn = None
        cursor = None
        connector = None
        try:
            from database import get_connector, get_db_path
            print("[DEBUG] Connecting to database for save operation...")
            connector = get_connector(get_db_path())

            conn = connector.connect()
            cursor = conn.cursor()

            print(f"[DEBUG] Applying {len(changes)} changes to database...")
            for i, change in enumerate(changes):
                print(f"[DEBUG] Processing change {i+1}/{len(changes)}: {change['username']} -> {change['new_level']}")

                # Check if this is a demotion from Level 2/3 to Level 1
                if change['old_level'] in ['Level 2', 'Level 3'] and change['new_level'] == 'Level 1':
                    # Clear password and 2FA secret for demoted users
                    cursor.execute(
                        "UPDATE [emp_list] SET [Access Level]=?, [Password]=?, [2FA Secret]=? WHERE [Username]=?",
                        (change['new_level'], None, None, change['username'])
                    )
                    print(f"[DEBUG] Cleared credentials for demoted user: {change['username']}")
                else:
                    # Normal access level update without clearing credentials
                    cursor.execute(
                        "UPDATE [emp_list] SET [Access Level]=? WHERE [Username]=?",
                        (change['new_level'], change['username'])
                    )

                # Commit after each change to prevent large transaction locks
                conn.commit()

            print("[DEBUG] Database changes completed successfully")

            # Count demotions for success message
            demoted_users = [c for c in changes if c['old_level'] in ['Level 2', 'Level 3'] and c['new_level'] == 'Level 1']

            if demoted_users:
                success_msg = f"Successfully updated {len(changes)} user(s).\n\n"
                success_msg += f"Security Notice: Cleared credentials for {len(demoted_users)} demoted user(s):\n"
                for user in demoted_users:
                    success_msg += f"• {user['first_name']} {user['last_name']}\n"
                success_msg += "\nThese users will need to reset their passwords before logging in again."
                messagebox.showinfo("Success", success_msg)
            else:
                messagebox.showinfo("Success", f"Successfully updated {len(changes)} user(s).")

            print("[DEBUG] Refreshing user data after save...")
            self.load_user_data()  # Refresh the data

        except Exception as e:
            print(f"[DEBUG] Save error: {e}")
            messagebox.showerror("Error", f"Failed to save changes: {e}")

        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if connector:
                    connector.close()
                    print("[DEBUG] Database connection closed")
                elif conn:
                    conn.close()
            except Exception as close_error:
                print(f"[DEBUG] Error closing database connection: {close_error}")

    def authenticate_sensitive_changes(self, sensitive_changes):
        """Require password and 2FA authentication from users being demoted"""
        for change in sensitive_changes:
            user_name = f"{change['first_name']} {change['last_name']}"
            if not self.authenticate_user_demotion(change['username'], user_name, change['old_level'], change['new_level']):
                return False
        return True

    def authenticate_user_demotion(self, target_username, user_display_name, old_level, new_level):
        """Authenticate a specific user being demoted"""
        print(f"[DEBUG] Starting authentication for user demotion: {user_display_name}")
        
        # Create authentication dialog for the specific user (properly sized with Alt+Tab support)
        auth_win = tk.Toplevel(self.settings_win)
        auth_win.title("Authentication Required - User Demotion")
        auth_win.geometry("650x550")
        auth_win.resizable(True, True)  # Make resizable
        auth_win.minsize(600, 500)  # Set minimum size
        auth_win.configure(bg="#000000")
        auth_win.transient(self.settings_win)
        auth_win.grab_set()
        
        # Center the window
        auth_win.update_idletasks()
        x = (auth_win.winfo_screenwidth() // 2) - (650 // 2)
        y = (auth_win.winfo_screenheight() // 2) - (550 // 2)
        auth_win.geometry(f"650x550+{x}+{y}")
        
        # Add protocol handler for unexpected closure
        def on_closing():
            print("[DEBUG] Authentication dialog closing unexpectedly")
            try:
                auth_win.destroy()
            except Exception as e:
                print(f"[DEBUG] Error destroying auth dialog: {e}")
        
        # Create main frame with border-like appearance
        main_frame = tk.Frame(auth_win, bg="#ff6f00", bd=0)
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Create container with scrollbar
        container = tk.Frame(main_frame, bg="#000000", bd=0)
        container.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container, bg="#000000", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#000000")
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', bind_to_mousewheel)
        canvas.bind('<Leave>', unbind_from_mousewheel)
        
        # Content frame (now inside scrollable frame)
        content_frame = tk.Frame(scrollable_frame, bg="#000000", bd=0)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Close button frame
        close_frame = tk.Frame(content_frame, bg="#000000")
        close_frame.pack(fill='x', pady=(0, 10))
        
        def cancel_auth():
            auth_win.destroy()
        
        tk.Button(close_frame, text="×", command=cancel_auth,
                 font=("Segoe UI", 12, "bold"), bg="#000000", fg="#ff6f00", 
                 relief='flat', bd=0, width=2, pady=0).pack(side='right')
        
        # Title with warning icon (enhanced)
        title_frame = tk.Frame(content_frame, bg="#000000")
        title_frame.pack(pady=(10, 15))
        
        tk.Label(title_frame, text="⚠️", font=("Segoe UI", 24), bg="#000000", fg="#ff6f00").pack()
        tk.Label(title_frame, text="Credential Surrender Required", 
                font=("Segoe UI", 16, "bold"), bg="#000000", fg="#fffde7").pack(pady=(5, 0))
        
        # Information panel
        info_panel_frame = tk.Frame(content_frame, bg="#2d1810", relief='solid', bd=1)
        info_panel_frame.pack(fill='x', pady=(15, 20))
        
        info_panel_text = """🔐 Security Notice:
When demoting a user's access level, the target user must authenticate themselves to confirm the demotion. This ensures that access level changes are authorized and prevents unauthorized privilege escalation attacks.

The user being demoted must provide their credentials to surrender their current access level."""
        
        tk.Label(info_panel_frame, text=info_panel_text, font=("Segoe UI", 10),
                bg="#2d1810", fg="#ffcc80", justify='left', wraplength=580).pack(padx=15, pady=12, anchor='w')
        
        # User info and warning message (enhanced)
        info_frame = tk.Frame(content_frame, bg="#000000")
        info_frame.pack(pady=(0, 20), fill='x')
        
        tk.Label(info_frame, text=f"User: {user_display_name}", 
                font=("Segoe UI", 12, "bold"), bg="#000000", fg="#fffde7").pack(pady=(0, 5))
        tk.Label(info_frame, text=f"Access Level Change: {old_level} → {new_level}", 
                font=("Segoe UI", 11), bg="#000000", fg="#ffcc00").pack(pady=(0, 10))
        
        warning_text = "The user being demoted must surrender their credentials.\nChoose ONE authentication method below:"
        tk.Label(info_frame, text=warning_text, 
                font=("Segoe UI", 10), bg="#000000", fg="#ff6f00", justify='center').pack(pady=(0, 10))
        
        # Authentication method selection (enhanced)
        method_frame = tk.Frame(content_frame, bg="#000000")
        method_frame.pack(pady=(0, 20), fill='x')
        
        auth_method = tk.StringVar(value="password")
        
        # Method selection with better styling
        tk.Label(method_frame, text="Authentication Method:", 
                font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7").pack(anchor='w', pady=(0, 8))
        
        radio_frame = tk.Frame(method_frame, bg="#000000")
        radio_frame.pack(anchor='w', pady=(0, 10))
        
        password_radio = tk.Radiobutton(radio_frame, text="🔑 Password Authentication", variable=auth_method, value="password",
                                       bg="#000000", fg="#fffde7", selectcolor="#23272b", 
                                       activebackground="#000000", activeforeground="#fffde7",
                                       font=("Segoe UI", 10))
        password_radio.pack(anchor='w', pady=2)
        
        tfa_radio = tk.Radiobutton(radio_frame, text="📱 2FA Code Authentication", variable=auth_method, value="2fa",
                                  bg="#000000", fg="#fffde7", selectcolor="#23272b",
                                  activebackground="#000000", activeforeground="#fffde7",
                                  font=("Segoe UI", 10))
        tfa_radio.pack(anchor='w', pady=2)
        
        # Credentials frame (enhanced)
        cred_frame = tk.Frame(content_frame, bg="#000000")
        cred_frame.pack(pady=(0, 20), fill='x')
        
        # Password field
        password_label = tk.Label(cred_frame, text=f"🔑 {user_display_name}'s Password:", 
                                 font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7")
        password_label.pack(anchor='w', pady=(0, 5))
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(cred_frame, textvariable=password_var, show='*', 
                                font=("Segoe UI", 11), bg="#23272b", fg="#fffde7",
                                insertbackground="#fffde7", relief='flat', bd=1)
        password_entry.pack(pady=(0, 15), fill='x', ipady=8)
        
        # 2FA field
        tfa_label = tk.Label(cred_frame, text=f"📱 {user_display_name}'s 2FA Code:", 
                            font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7")
        tfa_label.pack(anchor='w', pady=(0, 5))
        
        tfa_var = tk.StringVar()
        tfa_entry = tk.Entry(cred_frame, textvariable=tfa_var, 
                           font=("Segoe UI", 11), bg="#23272b", fg="#fffde7",
                           insertbackground="#fffde7", relief='flat', bd=1)
        tfa_entry.pack(pady=(0, 15), fill='x', ipady=8)
        
        # Enhanced instructions
        instruction_frame = tk.Frame(cred_frame, bg="#1a1a2e", relief='solid', bd=1)
        instruction_frame.pack(fill='x', pady=(0, 15))
        
        instruction_text = """📋 Authentication Instructions:
• Password Method: Enter the user's password and leave 2FA field empty
• 2FA Method: Enter the user's current 2FA code and leave password field empty
• Only ONE method is required for authentication
• The user must be present to provide their credentials"""
        
        tk.Label(instruction_frame, text=instruction_text, 
                font=("Segoe UI", 9), bg="#1a1a2e", fg="#b0b0b0", justify='left').pack(padx=12, pady=10, anchor='w')
        
        # Result variable
        auth_result = {'success': False}
        
        def verify_auth():
            selected_method = auth_method.get()
            password = password_var.get().strip()
            tfa_code = tfa_var.get().strip()
            
            # Validate input based on selected method
            if selected_method == "password":
                if not password:
                    messagebox.showerror("Input Required", "Please enter the user's password.")
                    return
                # Clear 2FA field to ensure only password is used
                tfa_code = ""
            elif selected_method == "2fa":
                if not tfa_code:
                    messagebox.showerror("Input Required", "Please enter the user's 2FA code.")
                    return
                # Clear password field to ensure only 2FA is used
                password = ""
            
            if self.verify_target_user_credentials_flexible(target_username, password, tfa_code, selected_method):
                auth_result['success'] = True
                auth_win.destroy()
            else:
                method_name = "password" if selected_method == "password" else "2FA code"
                messagebox.showerror("Authentication Failed", 
                                   f"Invalid {method_name} for {user_display_name}.\n" +
                                   f"The user must provide their correct {method_name}.")
        
        # Buttons frame (enhanced)
        btn_frame = tk.Frame(content_frame, bg="#000000")
        btn_frame.pack(pady=(20, 15))
        
        tk.Button(btn_frame, text="Cancel Demotion", command=cancel_auth,
                 font=("Segoe UI", 11), bg="#666", fg="#fff", relief='flat', 
                 activebackground="#555", activeforeground="#fff", width=18).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="Verify & Proceed", command=verify_auth,
                 font=("Segoe UI", 11, "bold"), bg="#dc3545", fg="#fff", relief='flat',
                 activebackground="#c82333", activeforeground="#fff", width=18).pack(side=tk.LEFT, padx=10)
        
        # Focus on password field initially
        password_entry.focus()
        
        # Enhanced keyboard navigation
        password_entry.bind('<Return>', lambda e: tfa_entry.focus())
        tfa_entry.bind('<Return>', lambda e: verify_auth())
        
        # Bind escape key to cancel
        auth_win.bind('<Escape>', lambda e: cancel_auth())
        
        # Bind Alt+Tab for window switching (better accessibility)
        auth_win.focus_set()
        
        # Wait for dialog to close with timeout protection
        try:
            auth_win.wait_window()
        except Exception as e:
            print(f"[DEBUG] Dialog wait error: {e}")
            try:
                auth_win.destroy()
            except Exception as close_err:
                print(f"[DEBUG] Error during auth dialog cleanup: {close_err}")
            return False
        
        return auth_result['success']

    def verify_target_user_credentials_flexible(self, target_username, password, tfa_code, auth_method):
        """Verify the target user's credentials using either password OR 2FA"""
        connector = None
        try:
            from database import get_connector, get_db_path
            connector = get_connector(get_db_path())
            row = connector.fetchone("SELECT [Password], [2FA Secret] FROM [emp_list] WHERE [Username]=?", (target_username,))

            if not row:
                return False

            if auth_method == "password":
                if not password:
                    return False
                if not row[0]:
                    return False
                try:
                    decrypted_password = self._decrypt_password(row[0])
                    return password == decrypted_password
                except Exception as decrypt_error:
                    print(f"[DEBUG] Password decryption error: {decrypt_error}")
                    return False
            elif auth_method == "2fa":
                if not tfa_code:
                    return False
                if not row[1]:
                    return False
                try:
                    decrypted_secret = self._decrypt_2fa_secret(row[1])
                    totp = pyotp.TOTP(decrypted_secret)
                    return totp.verify(tfa_code)
                except Exception as tfa_error:
                    print(f"[DEBUG] 2FA verification error: {tfa_error}")
                    return False

            return False
        except Exception as e:
            print(f"[DEBUG] Target user flexible authentication error: {e}")
            return False
        finally:
            try:
                if connector:
                    connector.close()
            except Exception:
                pass

    def verify_target_user_credentials(self, target_username, password, tfa_code):
        """Verify the target user's password and 2FA code (the user being demoted)"""
        connector = None
        try:
            from database import get_connector, get_db_path
            connector = get_connector(get_db_path())
            row = connector.fetchone("SELECT [Password], [2FA Secret] FROM [emp_list] WHERE [Username]=?", (target_username,))

            if not row:
                return False

            # Verify password
            try:
                decrypted_password = self._decrypt_password(row[0])
                if password != decrypted_password:
                    return False
            except Exception as decrypt_err:
                print(f"[DEBUG] Password decrypt/compare error: {decrypt_err}")
                return False

            # Verify 2FA
            if row[1]:  # If 2FA is set up for target user
                try:
                    decrypted_secret = self._decrypt_2fa_secret(row[1])
                    totp = pyotp.TOTP(decrypted_secret)
                    if not totp.verify(tfa_code):
                        return False
                except Exception as tfa_err:
                    print(f"[DEBUG] 2FA verify error: {tfa_err}")
                    return False
            else:
                # If no 2FA is set up for target user, tfa_code should be empty
                if tfa_code.strip():
                    return False

            return True
        except Exception as e:
            print(f"[DEBUG] Target user authentication error: {e}")
            return False
        finally:
            try:
                if connector:
                    connector.close()
            except Exception:
                pass

    def cancel_changes(self):
        """Cancel changes and reload original data"""
        if self.has_pending_changes:
            # Ask for confirmation if there are pending changes
            change_count = len(self.pending_changes)
            result = messagebox.askyesno(
                "Discard Changes?", 
                f"You have {change_count} unsaved change{'s' if change_count != 1 else ''}.\n\n"
                "Are you sure you want to discard all changes and reload the original data?",
                icon='warning'
            )
            if result:
                print(f"[DEBUG] User confirmed discarding {change_count} pending changes")
                self.load_user_data()
            else:
                print("[DEBUG] User cancelled change discard")
        else:
            # No pending changes, just reload
            self.load_user_data()
    
    def authenticate_admin_promotions(self, promotion_changes):
        """Require current admin authentication for promoting users to Level 2/3"""
        # Get current admin's information
        current_username = getattr(self.parent_settings.parent, 'username', None)
        if not current_username:
            messagebox.showerror("Error", "Unable to identify current user for authentication.")
            return False
        
        # Get current admin's display name
        try:
            from database import get_connector, get_db_path
            connector = get_connector(get_db_path())
            conn = None
            cursor = None
            try:
                conn = connector.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT [First Name], [Last Name] FROM [emp_list] WHERE [Username]=?", (current_username,))
                row = cursor.fetchone()
            except Exception as e:
                print(f"[DEBUG] Error getting admin display name: {e}")
                row = None
            finally:
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    connector.close()
                except Exception:
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass

            if row:
                admin_display_name = f"{row[0] or ''} {row[1] or ''}".strip()
            else:
                admin_display_name = current_username
        except Exception as e:
            print(f"[DEBUG] Error getting admin display name: {e}")
            admin_display_name = current_username
        
        # Create promotion summary
        promotion_summary = []
        for change in promotion_changes:
            user_name = f"{change['first_name']} {change['last_name']}"
            promotion_summary.append(f"• {user_name}: {change['old_level']} → {change['new_level']}")
        
        return self.authenticate_admin_promotion(current_username, admin_display_name, promotion_summary)

    def authenticate_admin_promotion(self, admin_username, admin_display_name, promotion_summary):
        """Authenticate the current admin for user promotions"""
        # Create authentication dialog with larger size and scrolling capability
        auth_win = tk.Toplevel(self.settings_win)
        auth_win.title("Authentication Required - User Promotion")
        auth_win.geometry("650x550")
        auth_win.minsize(500, 400)  # Set minimum size
        auth_win.configure(bg="#000000")
        auth_win.transient(self.settings_win)
        auth_win.grab_set()
        
        # Make window resizable
        auth_win.resizable(True, True)
        
        # Center the window
        auth_win.update_idletasks()
        x = self.settings_win.winfo_rootx() + (self.settings_win.winfo_width() // 2) - 325
        y = self.settings_win.winfo_rooty() + (self.settings_win.winfo_height() // 2) - 275
        auth_win.geometry(f"650x550+{x}+{y}")
        
        def cancel_admin_auth():
            auth_win.destroy()
        
        # Create main scrollable frame
        main_frame = tk.Frame(auth_win, bg="#000000")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame, bg="#000000", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#000000")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind('<Enter>', bind_mousewheel)
        canvas.bind('<Leave>', unbind_mousewheel)
        
        # Create content frame (this replaces the old content_frame)
        content_frame = tk.Frame(scrollable_frame, bg="#000000")
        content_frame.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Close button frame
        close_frame = tk.Frame(content_frame, bg="#000000")
        close_frame.pack(fill='x', padx=5, pady=(0, 10))
        
        tk.Button(close_frame, text="×", command=cancel_admin_auth,
                 font=("Segoe UI", 12, "bold"), bg="#000000", fg="#00a8ff", 
                 relief='flat', bd=0, width=2, pady=0).pack(side='right')
        
        # Title with security icon (enhanced spacing)
        title_frame = tk.Frame(content_frame, bg="#000000")
        title_frame.pack(pady=(10, 15))
        
        tk.Label(title_frame, text="🔐", font=("Segoe UI", 24), bg="#000000", fg="#00a8ff").pack()
        tk.Label(title_frame, text="Admin Authorization Required", 
                font=("Segoe UI", 16, "bold"), bg="#000000", fg="#fffde7").pack(pady=(5, 0))
        
        # Enhanced info frame with better styling
        info_frame = tk.Frame(content_frame, bg="#1c1c1c", relief='solid', bd=1)
        info_frame.pack(pady=(0, 20), padx=5, fill='x')
        
        # Admin info section
        admin_section = tk.Frame(info_frame, bg="#1c1c1c")
        admin_section.pack(fill='x', padx=15, pady=(15, 10))
        
        tk.Label(admin_section, text=f"Administrator: {admin_display_name}", 
                font=("Segoe UI", 12, "bold"), bg="#1c1c1c", fg="#fffde7").pack()
        
        # Promotion summary section
        promo_section = tk.Frame(info_frame, bg="#1c1c1c")
        promo_section.pack(fill='x', padx=15, pady=(10, 15))
        
        tk.Label(promo_section, text="User Promotions to Authorize:", 
                font=("Segoe UI", 11, "bold"), bg="#1c1c1c", fg="#00d9ff").pack(pady=(0, 8))
        
        # Promotion list with better formatting
        promotion_text = "\n".join(promotion_summary)
        tk.Label(promo_section, text=promotion_text, 
                font=("Segoe UI", 10), bg="#1c1c1c", fg="#00ff88", justify='left').pack()
        
        # Security warning with better styling
        warning_section = tk.Frame(info_frame, bg="#1c1c1c")
        warning_section.pack(fill='x', padx=15, pady=(10, 15))
        
        warning_text = "As a Level 3 administrator, you must verify your identity\nto authorize these privilege elevations."
        tk.Label(warning_section, text=warning_text, 
                font=("Segoe UI", 10), bg="#1c1c1c", fg="#ffcc00", justify='center').pack(pady=(0, 5))
        
        # Authentication method selection with better spacing
        method_frame = tk.Frame(content_frame, bg="#000000")
        method_frame.pack(pady=(10, 15), padx=20, fill='x')
        
        auth_method = tk.StringVar(value="password")
        
        # Method selection radio buttons
        tk.Label(method_frame, text="Authentication Method:", 
                font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7").pack(anchor='w', pady=(0, 8))
        
        radio_frame = tk.Frame(method_frame, bg="#000000")
        radio_frame.pack(anchor='w', pady=(0, 10))
        
        password_radio = tk.Radiobutton(radio_frame, text="Your Password", variable=auth_method, value="password",
                                       bg="#000000", fg="#fffde7", selectcolor="#23272b", 
                                       activebackground="#000000", activeforeground="#fffde7",
                                       font=("Segoe UI", 10))
        password_radio.pack(side='left', padx=(0, 20))
        
        tfa_radio = tk.Radiobutton(radio_frame, text="Your 2FA Code", variable=auth_method, value="2fa",
                                  bg="#000000", fg="#fffde7", selectcolor="#23272b",
                                  activebackground="#000000", activeforeground="#fffde7",
                                  font=("Segoe UI", 10))
        tfa_radio.pack(side='left')
        
        # Credentials frame with enhanced styling
        cred_frame = tk.Frame(content_frame, bg="#000000")
        cred_frame.pack(pady=(5, 15), padx=20, fill='x')
        
        # Password field
        password_label = tk.Label(cred_frame, text="Your Password:", 
                                 font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7")
        password_label.pack(anchor='w', pady=(0, 5))
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(cred_frame, textvariable=password_var, show='*', 
                                font=("Segoe UI", 11), width=40)
        password_entry.pack(pady=(0, 15), fill='x')
        
        # 2FA field
        tfa_label = tk.Label(cred_frame, text="Your 2FA Code:", 
                            font=("Segoe UI", 11, "bold"), bg="#000000", fg="#fffde7")
        tfa_label.pack(anchor='w', pady=(0, 5))
        
        tfa_var = tk.StringVar()
        tfa_entry = tk.Entry(cred_frame, textvariable=tfa_var, 
                           font=("Segoe UI", 11), width=40)
        tfa_entry.pack(pady=(0, 10), fill='x')
        
        # Instructions with better formatting
        instruction_text = "• Password: Enter your password, leave 2FA empty\n• 2FA: Enter your 2FA code, leave password empty"
        tk.Label(cred_frame, text=instruction_text, 
                font=("Segoe UI", 9), bg="#000000", fg="#999", justify='left').pack(anchor='w')
        
        # Result variable
        auth_result = {'success': False}
        
        def verify_admin_auth():
            selected_method = auth_method.get()
            password = password_var.get().strip()
            tfa_code = tfa_var.get().strip()
            
            # Validate input based on selected method
            if selected_method == "password":
                if not password:
                    messagebox.showerror("Input Required", "Please enter your password.")
                    return
                # Clear 2FA field to ensure only password is used
                tfa_code = ""
            elif selected_method == "2fa":
                if not tfa_code:
                    messagebox.showerror("Input Required", "Please enter your 2FA code.")
                    return
                # Clear password field to ensure only 2FA is used
                password = ""
            
            if self.verify_target_user_credentials_flexible(admin_username, password, tfa_code, selected_method):
                auth_result['success'] = True
                auth_win.destroy()
            else:
                method_name = "password" if selected_method == "password" else "2FA code"
                messagebox.showerror("Authentication Failed", 
                                   f"Invalid {method_name}.\nPlease verify your credentials and try again.")
        
        # Buttons frame with enhanced styling
        btn_frame = tk.Frame(content_frame, bg="#000000")
        btn_frame.pack(pady=(15, 10))
        
        tk.Button(btn_frame, text="Cancel Promotions", command=cancel_admin_auth,
                 font=("Segoe UI", 11), bg="#666", fg="#fff", relief='flat', width=18).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="Authorize & Proceed", command=verify_admin_auth,
                 font=("Segoe UI", 11, "bold"), bg="#00a8ff", fg="#fff", relief='flat', width=18).pack(side=tk.LEFT, padx=10)
        
        # Focus on password field initially
        password_entry.focus()
        
        # Enhanced keyboard bindings
        auth_win.bind('<Escape>', lambda e: cancel_admin_auth())
        auth_win.bind('<Return>', lambda e: verify_admin_auth())
        
        # Update canvas scroll region after all widgets are added
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Wait for dialog to close with timeout protection
        try:
            auth_win.wait_window()
        except Exception as e:
            print(f"[DEBUG] Admin dialog wait error: {e}")
            try:
                auth_win.destroy()
            except Exception as close_err:
                print(f"[DEBUG] Error during admin auth dialog cleanup: {close_err}")
            return False
        
        return auth_result['success']

    def save_changes_simplified(self):
        """Save changes with basic security checks but without complex authentication"""
        print("[DEBUG] Starting simplified save process...")

        # Check if there are any pending changes
        if not self.has_pending_changes or not self.pending_changes:
            messagebox.showinfo("No Changes", "No changes to save.")
            return

        # Convert pending changes to the format expected by the rest of the method
        changes = []
        for item_id, change_data in self.pending_changes.items():
            if change_data['type'] == 'access_level_change':
                original_data = self.original_user_data[item_id]
                changes.append({
                    'item_id': item_id,
                    'username': change_data['username'],
                    'first_name': original_data['first_name'],
                    'last_name': original_data['last_name'],
                    'old_level': change_data['original_level'],
                    'new_level': change_data['new_level']
                })

        print(f"[DEBUG] Found {len(changes)} changes to save (simplified mode)")

        # Basic security check: prevent last Level 3 user from demoting themselves
        current_username = getattr(self.parent_settings.parent, 'username', None)
        level_3_demotions = [c for c in changes if c['old_level'] == 'Level 3' and c['new_level'] != 'Level 3']
        self_demotion = [c for c in level_3_demotions if c['username'] == current_username]

        if self_demotion:
            final_level_3_count = 0
            for item_id in self.user_tree.get_children():
                values = self.user_tree.item(item_id)['values']
                if values[2] == 'Level 3':
                    final_level_3_count += 1

            if final_level_3_count == 0:
                messagebox.showerror(
                    "Invalid Operation",
                    "Cannot save changes: This would result in no Level 3 users remaining in the system.\n\n"
                    "You must promote at least one other user to Level 3 before demoting yourself."
                )
                return

        # Handle promotions - setup credentials for users being promoted
        promotion_changes = [c for c in changes if c['old_level'] == 'Level 1' and c['new_level'] in ['Level 2', 'Level 3']]
        promotion_setups = {}

        for change in promotion_changes:
            print(f"[DEBUG] Setting up promoted user: {change['first_name']} {change['last_name']}")

            # Test database connection before setup
            if not self.test_database_connection():
                messagebox.showerror("Database Error", "Cannot connect to database. Please check the connection and try again.")
                return

            setup_result = self.setup_promoted_user(
                change['username'],
                change['first_name'],
                change['last_name'],
                change['new_level']
            )

            if setup_result is None:
                print(f"[DEBUG] User setup cancelled for {change['username']}")
                return  # User cancelled the setup

            print(f"[DEBUG] Setup result for {change['username']}: {setup_result}")
            promotion_setups[change['username']] = setup_result
            print(f"[DEBUG] Setup completed for {change['username']}: new username = {setup_result['username']}")

        # Show confirmation for sensitive changes
        sensitive_changes = [c for c in changes if c['old_level'] in ['Level 2', 'Level 3'] or c['new_level'] in ['Level 2', 'Level 3']]
        if sensitive_changes:
            change_summary = ""
            for change in sensitive_changes:
                change_summary += f"• {change['first_name']} {change['last_name']}: {change['old_level']} → {change['new_level']}\n"

            result = messagebox.askyesno(
                "Confirm Sensitive Changes",
                f"The following changes involve elevated access levels:\n\n{change_summary}\n"
                "Are you sure you want to proceed?"
            )
            if not result:
                return

        # Apply changes to database
        conn = None
        connector = None
        try:
            from database import get_connector, get_db_path
            print("[DEBUG] Connecting to database (simplified mode)...")
            connector = get_connector(get_db_path())
            conn = connector.connect()
            cursor = conn.cursor()

            for i, change in enumerate(changes):
                print(f"[DEBUG] Processing change {i+1}/{len(changes)}: {change['username']} -> {change['new_level']}")

                # Check if this is a demotion from Level 2/3 to Level 1
                if change['old_level'] in ['Level 2', 'Level 3'] and change['new_level'] == 'Level 1':
                    # Clear password and 2FA secret for demoted users (security measure)
                    cursor.execute(
                        "UPDATE [emp_list] SET [Access Level]=?, [Password]=?, [2FA Secret]=? WHERE [Username]=?",
                        (change['new_level'], None, None, change['username'])
                    )
                    print(f"[DEBUG] Cleared credentials for demoted user: {change['username']}")

                # Check if this is a promotion with credential setup
                elif change['username'] in promotion_setups:
                    setup_info = promotion_setups[change['username']]

                    print(f"[DEBUG] Processing promotion setup for: {setup_info['username']}")

                    # Update credentials using the helper method
                    try:
                        print(
                            f"[DEBUG] About to call update_user_credentials with: old_username={change['username']}, "
                            f"new_username={setup_info['username']}, setup_2fa={setup_info['setup_2fa']}"
                        )
                        cred_result = self.update_user_credentials(
                            change['username'],
                            setup_info['username'],
                            setup_info['password'],
                            setup_info['setup_2fa']
                        )

                        print(f"[DEBUG] Credential update result: {cred_result}")

                        if not cred_result.get('success', False):
                            error_msg = cred_result.get('error', 'Unknown error during credential update')
                            raise Exception(f"Failed to update credentials for {change['username']}: {error_msg}")

                        # Update access level separately since username might have changed
                        print(f"[DEBUG] Updating access level for: {setup_info['username']}")
                        cursor.execute(
                            "UPDATE [emp_list] SET [Access Level]=? WHERE [Username]=?",
                            (change['new_level'], setup_info['username'])
                        )

                        print(f"[DEBUG] Updated promoted user: {setup_info['username']} -> {change['new_level']}")

                        # Show 2FA setup info if applicable
                        if setup_info['setup_2fa'] and cred_result.get('otp_secret'):
                            # We'll show this after all database operations are complete
                            change['show_2fa_info'] = {
                                'username': setup_info['username'],
                                'otp_secret': cred_result['otp_secret']
                            }
                            print("[DEBUG] 2FA info prepared for display")

                    except Exception as cred_error:
                        print(f"[DEBUG] Error in credential update process: {cred_error}")
                        raise cred_error

                else:
                    # Normal access level update without credential changes
                    cursor.execute(
                        "UPDATE [emp_list] SET [Access Level]=? WHERE [Username]=?",
                        (change['new_level'], change['username'])
                    )

                conn.commit()

            cursor.close()
            try:
                if connector:
                    connector.close()
            except Exception:
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
            print("[DEBUG] Simplified save completed successfully")

            # Show 2FA setup information for promoted users
            for change in changes:
                if 'show_2fa_info' in change:
                    try:
                        print(f"[DEBUG] Showing 2FA setup info for: {change['show_2fa_info']['username']}")
                        self.show_2fa_setup_info(
                            change['show_2fa_info']['username'],
                            change['show_2fa_info']['otp_secret']
                        )
                    except Exception as tfa_error:
                        print(f"[DEBUG] Error showing 2FA info: {tfa_error}")
                        # Continue anyway, don't let this block the success message

            # Count different types of changes for success message
            demoted_users = [c for c in changes if c['old_level'] in ['Level 2', 'Level 3'] and c['new_level'] == 'Level 1']
            promoted_users = [c for c in changes if c['old_level'] == 'Level 1' and c['new_level'] in ['Level 2', 'Level 3']]

            success_msg = f"Successfully updated {len(changes)} user(s).\n\n"

            if promoted_users:
                success_msg += f"Promoted Users ({len(promoted_users)}):\n"
                for change in promoted_users:
                    setup_info = promotion_setups.get(change['username'], {})
                    username_display = setup_info.get('username', change['username'])
                    tfa_status = " (with 2FA)" if setup_info.get('setup_2fa') else ""
                    success_msg += f"• {change['first_name']} {change['last_name']} → {change['new_level']}{tfa_status}\n"
                    if setup_info.get('username') != change['username']:
                        success_msg += f"  Username changed: {change['username']} → {username_display}\n"
                success_msg += "\n"

            if demoted_users:
                success_msg += f"Security Notice: Cleared credentials for {len(demoted_users)} demoted user(s):\n"
                for user in demoted_users:
                    success_msg += f"• {user['first_name']} {user['last_name']}\n"
                success_msg += "\nThese users will need to reset their passwords before logging in again.\n\n"

            success_msg += "All promoted users have been provided with new credentials and are ready to log in."
            messagebox.showinfo("Success", success_msg)

            # Reset pending changes and refresh data
            self.has_pending_changes = False
            self.pending_changes.clear()
            self.load_user_data()  # Refresh the data from database

        except Exception as e:
            print(f"[DEBUG] Simplified save error: {e}")
            messagebox.showerror("Error", f"Failed to save changes: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                    print("[DEBUG] Simplified database connection closed")
                except Exception as close_err:
                    print(f"[DEBUG] Error closing simplified save connection: {close_err}")

    def on_right_click(self, event):
        """Show context menu on right-click for the user tree.
        Provides quick actions: Edit, Remove, Promote, Demote.
        Safe no-op if no item under cursor. Avoids AttributeError seen earlier.
        """
        try:
            if not self.user_tree:
                return
            # Identify row under cursor
            item_id = self.user_tree.identify_row(event.y)
            if item_id:
                # Select it
                self.user_tree.selection_set(item_id)
            else:
                # Clicked empty area – clear selection
                self.user_tree.selection_remove(self.user_tree.selection())
                return

            # Lazy-create (or recreate) context menu each time to reflect state
            menu = tk.Menu(self.user_tree, tearoff=0, bg="#23272b", fg="#ffffff", activebackground="#444", activeforeground="#ffffff", relief='flat')
            menu.add_command(label="Edit", command=lambda: self.edit_employee_dialog())
            menu.add_command(label="Remove", command=lambda: self.remove_employee_dialog())

            # Determine current level for promote/demote options
            values = self.user_tree.item(item_id).get('values', [])
            current_level = values[2] if len(values) > 2 else 'Level 1'

            def change_level(new_level):
                if not item_id:
                    return
                if len(values) < 3:
                    return
                old_level = values[2]
                if old_level == new_level:
                    return
                # Update tree display
                new_vals = list(values)
                new_vals[2] = new_level
                self.user_tree.item(item_id, values=new_vals)
                # Track pending change
                self.has_pending_changes = True
                self.pending_changes[item_id] = {
                    'type': 'access_level_change',
                    'username': self.original_user_data.get(item_id, {}).get('username', ''),
                    'original_level': old_level,
                    'new_level': new_level
                }
                try:
                    self.update_save_button_state()
                except Exception:
                    pass

            # Add promote/demote entries based on current level
            if current_level == 'Level 1':
                menu.add_command(label="Promote to Level 2", command=lambda: change_level('Level 2'))
                menu.add_command(label="Promote to Level 3", command=lambda: change_level('Level 3'))
            elif current_level == 'Level 2':
                menu.add_command(label="Promote to Level 3", command=lambda: change_level('Level 3'))
                menu.add_command(label="Demote to Level 1", command=lambda: change_level('Level 1'))
            elif current_level == 'Level 3':
                menu.add_command(label="Demote to Level 2", command=lambda: change_level('Level 2'))
                menu.add_command(label="Demote to Level 1", command=lambda: change_level('Level 1'))

            menu.add_separator()
            menu.add_command(label="Show Pending Changes", command=self.show_pending_changes_summary)

            try:
                menu.tk_popup(event.x_root, event.y_root)
            except Exception as e:
                print(f"[DEBUG] Error in on_right_click (popup): {e}")
            finally:
                try:
                    menu.grab_release()
                except Exception:
                    pass
        except Exception as outer_e:
            print(f"[DEBUG] Error in on_right_click outer block: {outer_e}")

    def show_pending_changes_summary(self):
        """Display a summary of pending access level changes."""
        try:
            if not self.has_pending_changes or not self.pending_changes:
                messagebox.showinfo("Pending Changes", "No pending changes.")
                return

            lines = []
            for item_id, change in self.pending_changes.items():
                if change.get('type') == 'access_level_change':
                    orig = change.get('original_level')
                    new = change.get('new_level')
                    user = self.original_user_data.get(item_id, {})
                    name = f"{user.get('first_name','')} {user.get('last_name','')}".strip()
                    username = user.get('username','')
                    lines.append(f"• {name} ({username}) : {orig} → {new}")

            if not lines:
                messagebox.showinfo("Pending Changes", "No pending changes.")
                return

            summary = f"Total pending changes: {len(lines)}\n\n" + "\n".join(lines)
            messagebox.showinfo("Pending Changes Summary", summary)
        except Exception as e:
            print(f"[DEBUG] Error in show_pending_changes_summary: {e}")

    def setup_promoted_user(self, username, first_name, last_name, new_level):
        """Allow admin to setup password and optionally edit username for promoted user"""
        print(f"[DEBUG] Starting promoted user setup for: {username}")


    def check_username_exists(self, username):
        """Check if a username already exists in the database"""
        from database import get_connector, get_db_path
        connector = None
        try:
            connector = get_connector(get_db_path())
            row = connector.fetchone("SELECT COUNT(*) FROM [emp_list] WHERE [Username]=?", (username,))
            count = row[0] if row else 0
            return count > 0
        except Exception as e:
            print(f"[DEBUG] Error checking username existence: {e}")
            return False
        finally:
            try:
                if connector:
                    connector.close()
            except Exception:
                pass

    def update_user_credentials(self, old_username, new_username, password, setup_2fa=False):
        """Update user credentials in the database"""
        conn = None
        print(f"[DEBUG] Starting credential update for user: {old_username} -> {new_username}")
        from database import get_connector, get_db_path
        db_path = get_db_path()
        if not os.path.exists(db_path):
            error_msg = f"Database file not found at: {db_path}"
            print(f"[DEBUG] {error_msg}")
            messagebox.showerror("Database Error", error_msg)
            return {'success': False, 'error': error_msg}
        print(f"[DEBUG] Using database path: {db_path}")
        
        # Encrypt password using helper method
        encrypted_password = self._encrypt_password(password)
        print("[DEBUG] Password encrypted successfully")
        
        # Setup 2FA if requested
        otp_secret = None
        encrypted_otp_secret = None
        if setup_2fa:
            print("[DEBUG] Setting up 2FA for user")
            otp_secret = pyotp.random_base32()
            encrypted_otp_secret = self._encrypt_2fa_secret(otp_secret)
            print("[DEBUG] 2FA secret generated and encrypted")
        
        print("[DEBUG] Connecting to database...")
        try:
            connector = get_connector(db_path)
            conn = None
            cursor = None
            try:
                conn = connector.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM [emp_list] WHERE [Username]=?", (old_username,))
                if cursor.fetchone()[0] == 0:
                    error_msg = f"Original username '{old_username}' not found in database"
                    print(f"[DEBUG] {error_msg}")
                    return {'success': False, 'error': error_msg}
                if old_username != new_username:
                    cursor.execute("SELECT COUNT(*) FROM [emp_list] WHERE [Username]=?", (new_username,))
                    if cursor.fetchone()[0] > 0:
                        error_msg = f"New username '{new_username}' already exists in database"
                        print(f"[DEBUG] {error_msg}")
                        return {'success': False, 'error': error_msg}
                rows_affected = 0
                if setup_2fa:
                    cursor.execute("UPDATE [emp_list] SET [Username]=?, [Password]=?, [2FA Secret]=? WHERE [Username]=?",
                                (new_username, encrypted_password, encrypted_otp_secret, old_username))
                    rows_affected = cursor.rowcount
                else:
                    cursor.execute("UPDATE [emp_list] SET [Username]=?, [Password]=? WHERE [Username]=?",
                                (new_username, encrypted_password, old_username))
                    rows_affected = cursor.rowcount
                if rows_affected == 0:
                    error_msg = f"Update operation affected 0 rows. Username '{old_username}' may not exist."
                    print(f"[DEBUG] {error_msg}")
                    return {'success': False, 'error': error_msg}
                conn.commit()
                # Verify update
                verify_cursor = conn.cursor()
                verify_cursor.execute("SELECT COUNT(*) FROM [emp_list] WHERE [Username]=?", (new_username,))
                found = verify_cursor.fetchone()[0]
                verify_cursor.close()
                if found == 0 and old_username != new_username:
                    error_msg = f"Verification failed: Username '{new_username}' not found after update"
                    print(f"[DEBUG] {error_msg}")
                    return {'success': False, 'error': error_msg}
                if setup_2fa and otp_secret:
                    return {'success': True, 'otp_secret': otp_secret}
                else:
                    return {'success': True}
            except Exception as db_err:
                error_msg = f"Database error: {db_err}"
                print(f"[DEBUG] {error_msg}")
                return {'success': False, 'error': error_msg}
            finally:
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    connector.close()
                except Exception:
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass
        except Exception as e:
            print(f"[DEBUG] Error updating user credentials: {e}")
            return {'success': False, 'error': str(e)}

    def show_2fa_setup_info(self, username, otp_secret):
        """Show 2FA setup information to the admin"""
    # (Legacy dialog implementation removed; wizard version overrides earlier.)

    def test_database_connection(self):
        """Test database connection to help debug freezing issues"""
        try:
            print("[DEBUG] Testing database connection...")
            from database import get_connector, get_db_path
            db_path = get_db_path()
            print(f"[DEBUG] Database path: {db_path}")
            print("[DEBUG] Attempting connection...")
            connector = get_connector(db_path)
            try:
                row = connector.fetchone("SELECT COUNT(*) FROM [emp_list]")
                count = row[0] if row else 0
                print(f"[DEBUG] Query executed, found {count} records")
            finally:
                try:
                    connector.close()
                except Exception:
                    pass
            print("[DEBUG] Connection closed successfully")
            return True
            
        except Exception as e:
            print(f"[DEBUG] Database connection test failed: {e}")
            return False

    def filter_users(self, *args):
        """Filter users based on search query"""
        try:
            if not self.user_tree or not hasattr(self, 'search_var'):
                return
                
            search_query = self.search_var.get().lower().strip()
            
            # Store all original data in a separate backup if not already done
            if not hasattr(self, 'all_user_data'):
                self.all_user_data = self.original_user_data.copy()
            
            # Clear current display
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            # Clear the current mapping
            self.original_user_data.clear()
            
            # Collect matching items
            matching_items = []
            for item_id, user_data in self.all_user_data.items():
                first_name = user_data['first_name'].lower()
                last_name = user_data['last_name'].lower()
                username = user_data['username'].lower()
                access_level = user_data['access_level'].lower()
                
                # Check if search query matches any field
                if (not search_query or 
                    search_query in first_name or
                    search_query in last_name or
                    search_query in username or
                    search_query in access_level):
                    matching_items.append(user_data)
            
            # Sort matching items if there's an active sort
            if self.sort_column and matching_items:
                column_map = {
                    'Last Name': 'last_name',
                    'First Name': 'first_name',
                    'Access Level': 'access_level'
                }
                if self.sort_column in column_map:
                    sort_key = column_map[self.sort_column]
                    matching_items.sort(key=lambda x: str(x[sort_key]).lower(), reverse=self.sort_reverse)
            
            # Insert sorted and filtered results
            visible_count = 0
            for user_data in matching_items:
                new_item_id = self.user_tree.insert('', 'end', 
                                                   values=(user_data['last_name'], 
                                                          user_data['first_name'], 
                                                          user_data['access_level']))
                # Update mapping for new item ID
                self.original_user_data[new_item_id] = user_data.copy()
                visible_count += 1
            
            # Update header display to show current sort
            if self.sort_column:
                sort_arrow = ' ↓' if self.sort_reverse else ' ↑'
                for col in ['Last Name', 'First Name', 'Access Level']:
                    if col == self.sort_column:
                        self.user_tree.heading(col, text=f'{col}{sort_arrow}')
                    else:
                        self.user_tree.heading(col, text=f'{col} ↕')
            
            # Update statistics
            self.update_statistics(visible_count)
            
        except Exception as e:
            print(f"[DEBUG] Error filtering users: {e}")

    def clear_search(self):
        """Clear search and reload all users"""
        try:
            if hasattr(self, 'search_var'):
                self.search_var.set("")
                # Reload all data when search is cleared
                self.load_user_data()
        except Exception as e:
            print(f"[DEBUG] Error clearing search: {e}")

    def update_statistics(self, visible_count=None):
        """Update statistics display"""
        try:
            if not hasattr(self, 'stats_label') or not self.stats_label:
                return
                
            # Count access levels
            level_counts = {"Level 1": 0, "Level 2": 0, "Level 3": 0}
            total_count = 0
            
            if visible_count is None:
                # Count from treeview (all visible items)
                for item in self.user_tree.get_children():
                    values = self.user_tree.item(item)['values']
                    if len(values) >= 3:
                        access_level = values[2]
                        if access_level in level_counts:
                            level_counts[access_level] += 1
                        total_count += 1
            else:
                # Count from visible items when filtering
                for item in self.user_tree.get_children():
                    values = self.user_tree.item(item)['values']
                    if len(values) >= 3:
                        access_level = values[2]
                        if access_level in level_counts:
                            level_counts[access_level] += 1
                total_count = visible_count
            
            # Create statistics text
            stats_text = f"Total: {total_count} employees | "
            stats_text += f"Level 1: {level_counts['Level 1']} | "
            stats_text += f"Level 2: {level_counts['Level 2']} | "
            stats_text += f"Level 3: {level_counts['Level 3']}"
            
            if hasattr(self, 'search_var') and self.search_var.get().strip():
                stats_text += " (filtered)"
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            print(f"[DEBUG] Error updating statistics: {e}")

    def refresh_data(self):
        """Refresh user data and clear any filters"""
        try:
            if hasattr(self, 'search_var'):
                self.search_var.set("")
            self.load_user_data()
        except Exception as e:
            print(f"[DEBUG] Error refreshing data: {e}")
            messagebox.showerror("Error", f"Failed to refresh data: {e}")

    def edit_employee_context(self, item):
        """Edit employee from context menu"""
        try:
            # Select the item first
            self.user_tree.selection_set(item)
            # Call the edit dialog
            self.edit_employee_dialog()
        except Exception as e:
            print(f"[DEBUG] Error in edit_employee_context: {e}")

    def remove_employee_context(self, item):
        """Remove employee from context menu"""
        try:
            # Select the item first
            self.user_tree.selection_set(item)
            # Call the remove dialog
            self.remove_employee_dialog()
        except Exception as e:
            print(f"[DEBUG] Error in remove_employee_context: {e}")

    def delete_key_pressed(self, event):
        """Handle Delete key press"""
        try:
            if self.user_tree.selection():
                self.remove_employee_dialog()
        except Exception as e:
            print(f"[DEBUG] Error in delete_key_pressed: {e}")

    def enter_key_pressed(self, event):
        """Handle Enter key press"""
        try:
            if self.user_tree.selection():
                self.edit_employee_dialog()
        except Exception as e:
            print(f"[DEBUG] Error in enter_key_pressed: {e}")

    def validate_user_input(self, first_name, last_name, username, password=None):
        """Comprehensive user input validation"""
        errors = []
        
        # Name validation
        if not first_name or not first_name.strip():
            errors.append("First name is required")
        elif len(first_name.strip()) < 2:
            errors.append("First name must be at least 2 characters long")
        elif not all(c.isalpha() or c.isspace() or c in "'-." for c in first_name):
            errors.append("First name contains invalid characters")
            
        if not last_name or not last_name.strip():
            errors.append("Last name is required")
        elif len(last_name.strip()) < 2:
            errors.append("Last name must be at least 2 characters long")
        elif not all(c.isalpha() or c.isspace() or c in "'-." for c in last_name):
            errors.append("Last name contains invalid characters")
            
        # Username validation
        if not username or not username.strip():
            errors.append("Username is required")
        elif len(username.strip()) < 2:
            errors.append("Username must be at least 2 characters long")
        elif len(username.strip()) > 50:
            errors.append("Username must be less than 50 characters")
        elif not username.replace('_', '').replace('.', '').isalnum():
            errors.append("Username can only contain letters, numbers, dots, and underscores")
        elif username.strip().lower() in ['admin', 'administrator', 'root', 'system', 'bypass']:
            errors.append("Username is reserved and cannot be used")
            
        # Password validation (if provided)
        if password is not None:
            if not password or len(password) < 8:
                errors.append("Password must be at least 8 characters long")
            elif len(password) > 128:
                errors.append("Password must be less than 128 characters")
            elif not any(c.isupper() for c in password):
                errors.append("Password must contain at least one uppercase letter")
            elif not any(c.islower() for c in password):
                errors.append("Password must contain at least one lowercase letter")
            elif not any(c.isdigit() for c in password):
                errors.append("Password must contain at least one number")
                
        return errors

    def get_user_count_by_level(self, level):
        """Get count of users by access level"""
        try:
            from database import get_connector, get_db_path
            connector = get_connector(get_db_path())
            conn = connector.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM [emp_list] WHERE [Access Level]=?", (level,))
            count = cursor.fetchone()[0]
            cursor.close()
            try:
                if connector:
                    connector.close()
            except Exception:
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
            
            return count
            
        except Exception as e:
            print(f"[DEBUG] Error getting user count by level: {e}")
            return 0

    def bulk_operations_dialog(self):
        """Show dialog for bulk operations on multiple employees"""
        try:
            # Create dialog window
            dialog = tk.Toplevel(self.settings_win)
            dialog.title("Bulk Operations")
            dialog.geometry("650x600")
            dialog.configure(bg="#000000")
            dialog.resizable(True, True)  # Make resizable
            dialog.minsize(600, 500)  # Set minimum size
            dialog.transient(self.settings_win)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
            y = (dialog.winfo_screenheight() // 2) - (600 // 2)
            dialog.geometry(f"650x600+{x}+{y}")
            
            # Create main container with scrollbar
            container = tk.Frame(dialog, bg="#000000")
            container.pack(fill='both', expand=True)
            
            # Create canvas and scrollbar
            canvas = tk.Canvas(container, bg="#000000", highlightthickness=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#000000")
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Main frame (now inside scrollable frame)
            main_frame = tk.Frame(scrollable_frame, bg="#000000")
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Enable mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            def bind_to_mousewheel(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def unbind_from_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
            
            canvas.bind('<Enter>', bind_to_mousewheel)
            canvas.bind('<Leave>', unbind_from_mousewheel)
            
            # Title
            title_label = tk.Label(main_frame, text="Bulk Operations", 
                                 font=("Segoe UI", 16, "bold"), bg="#000000", fg="#fffde7")
            title_label.pack(pady=(0, 20))
            
            # Instructions
            instructions = tk.Label(main_frame, 
                                  text="Select employees below and choose an operation to apply to all selected users.",
                                  font=("Segoe UI", 10), bg="#000000", fg="#999", wraplength=550)
            instructions.pack(pady=(0, 15))
            
            # Employee selection frame
            selection_frame = tk.Frame(main_frame, bg="#000000")
            selection_frame.pack(fill='both', expand=True, pady=(0, 15))
            
            # Employee listbox with checkboxes (using Treeview)
            columns = ('Select', 'Name', 'Username', 'Current Level')
            employee_tree = ttk.Treeview(selection_frame, columns=columns, show='headings', height=10)
            
            # Configure columns
            employee_tree.heading('Select', text='☐')
            employee_tree.heading('Name', text='Name')
            employee_tree.heading('Username', text='Username')
            employee_tree.heading('Current Level', text='Current Level')
            
            employee_tree.column('Select', width=50, anchor='center')
            employee_tree.column('Name', width=150, anchor='w')
            employee_tree.column('Username', width=120, anchor='w')
            employee_tree.column('Current Level', width=100, anchor='center')
            
            # Scrollbar
            scrollbar_bulk = ttk.Scrollbar(selection_frame, orient='vertical', command=employee_tree.yview)
            employee_tree.configure(yscrollcommand=scrollbar_bulk.set)
            
            employee_tree.pack(side='left', fill='both', expand=True)
            scrollbar_bulk.pack(side='right', fill='y')
            
            # Track selected items
            selected_items = set()
            
            # Load employee data
            def load_employee_data():
                for item in employee_tree.get_children():
                    employee_tree.delete(item)
                
                current_username = getattr(self.parent_settings.parent, 'username', None)
                
                for item_id, user_data in self.original_user_data.items():
                    name = f"{user_data['first_name']} {user_data['last_name']}"
                    username = user_data['username']
                    access_level = user_data['access_level']
                    
                    # Skip current user to prevent self-modification
                    if current_username and username.lower() == current_username.lower():
                        continue
                    
                    employee_tree.insert('', 'end', values=('☐', name, username, access_level))
            
            # Toggle selection
            def toggle_selection(event):
                item = employee_tree.selection()[0] if employee_tree.selection() else None
                if item:
                    values = list(employee_tree.item(item)['values'])
                    if values[0] == '☐':
                        values[0] = '☑'
                        selected_items.add(item)
                    else:
                        values[0] = '☐'
                        selected_items.discard(item)
                    employee_tree.item(item, values=values)
                    update_selection_count()
            
            def select_all():
                for item in employee_tree.get_children():
                    values = list(employee_tree.item(item)['values'])
                    values[0] = '☑'
                    employee_tree.item(item, values=values)
                    selected_items.add(item)
                update_selection_count()
            
            def select_none():
                for item in employee_tree.get_children():
                    values = list(employee_tree.item(item)['values'])
                    values[0] = '☐'
                    employee_tree.item(item, values=values)
                selected_items.clear()
                update_selection_count()
            
            def update_selection_count():
                count = len(selected_items)
                selection_label.config(text=f"Selected: {count} employees")
            
            employee_tree.bind('<Double-1>', toggle_selection)
            
            # Selection controls
            selection_controls = tk.Frame(main_frame, bg="#000000")
            selection_controls.pack(fill='x', pady=(0, 15))
            
            tk.Button(selection_controls, text="Select All", font=("Segoe UI", 9),
                     bg="#007AFF", fg="#fff", relief='flat', width=10,
                     command=select_all).pack(side='left', padx=(0, 5))
            
            tk.Button(selection_controls, text="Select None", font=("Segoe UI", 9),
                     bg="#666", fg="#fff", relief='flat', width=10,
                     command=select_none).pack(side='left', padx=(0, 10))
            
            selection_label = tk.Label(selection_controls, text="Selected: 0 employees",
                                     font=("Segoe UI", 9), bg="#000000", fg="#999")
            selection_label.pack(side='left')
            
            # Operations frame
            operations_frame = tk.Frame(main_frame, bg="#000000")
            operations_frame.pack(fill='x', pady=(0, 15))
            
            # Operation selection
            op_label = tk.Label(operations_frame, text="Operation:", font=("Segoe UI", 11),
                               bg="#000000", fg="#fffde7")
            op_label.pack(anchor='w', pady=(0, 5))
            
            operation_var = tk.StringVar(value="change_access_level")
            
            # Radio buttons for operations
            tk.Radiobutton(operations_frame, text="Change Access Level", 
                          variable=operation_var, value="change_access_level",
                          font=("Segoe UI", 10), bg="#000000", fg="#fffde7",
                          selectcolor="#23272b", activebackground="#000000",
                          activeforeground="#fffde7").pack(anchor='w')
            
            # Access level selection (only shown for access level change)
            level_frame = tk.Frame(operations_frame, bg="#000000")
            level_frame.pack(anchor='w', padx=(20, 0), pady=(5, 0))
            
            tk.Label(level_frame, text="New Access Level:", font=("Segoe UI", 10),
                    bg="#000000", fg="#fffde7").pack(side='left')
            
            new_level_var = tk.StringVar(value="Level 1")
            level_combo = ttk.Combobox(level_frame, textvariable=new_level_var,
                                     values=["Level 1", "Level 2", "Level 3"],
                                     state="readonly", font=("Segoe UI", 10), width=10)
            level_combo.pack(side='left', padx=(10, 0))
            
            # Buttons frame
            btn_frame = tk.Frame(main_frame, bg="#000000")
            btn_frame.pack(anchor='e', pady=(20, 0))
            
            def execute_bulk_operation():
                if not selected_items:
                    messagebox.showwarning("No Selection", "Please select at least one employee.")
                    return
                
                operation = operation_var.get()
                if operation == "change_access_level":
                    new_level = new_level_var.get()
                    
                    # Confirm operation
                    count = len(selected_items)
                    confirm_msg = f"Are you sure you want to change the access level of {count} selected employee(s) to {new_level}?"
                    
                    if messagebox.askyesno("Confirm Bulk Operation", confirm_msg):
                        success_count = 0
                        failed_users = []
                        
                        for item in selected_items:
                            values = employee_tree.item(item)['values']
                            username = values[2]  # Username is at index 2
                            
                            # Find the user data
                            user_data = None
                            for orig_item_id, orig_user_data in self.original_user_data.items():
                                if orig_user_data['username'] == username:
                                    user_data = orig_user_data
                                    break
                            
                            if user_data:
                                # FIX: pass correct arguments (new_username=None, new_password=None, access_level=new_level)
                                # Previous code mistakenly passed new_level as new_password causing password overwrite attempts
                                success, message = self.update_employee_in_database(
                                    username,  # original_username
                                    user_data['first_name'],
                                    user_data['last_name'],
                                    None,      # new_username
                                    None,      # new_password
                                    new_level  # access_level
                                )
                                
                                if success:
                                    success_count += 1
                                else:
                                    failed_users.append(f"{user_data['first_name']} {user_data['last_name']}")
                        
                        # Show results
                        if success_count > 0:
                            result_msg = f"Successfully updated {success_count} employee(s)."
                            if failed_users:
                                result_msg += f"\n\nFailed to update: {', '.join(failed_users)}"
                            messagebox.showinfo("Bulk Operation Complete", result_msg)
                            dialog.destroy()
                            self.load_user_data()  # Refresh the main list
                        elif failed_users:
                            messagebox.showerror("Bulk Operation Failed", 
                                               f"Failed to update: {', '.join(failed_users)}")
            
            def cancel_bulk():
                dialog.destroy()
            
            # Cancel button
            cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                                 bg="#666", fg="#fff", relief='flat',
                                 activebackground="#555", activeforeground="#fff",
                                 width=10, command=cancel_bulk)
            cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Execute button
            execute_btn = tk.Button(btn_frame, text="Execute Operation", font=("Segoe UI", 11, "bold"),
                                  bg="#6f42c1", fg="#fff", relief='flat',
                                  activebackground="#5a36a1", activeforeground="#fff",
                                  width=15, command=execute_bulk_operation)
            execute_btn.pack(side=tk.RIGHT)
            
            # Load data
            load_employee_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open bulk operations dialog: {e}")

    def add_employee_dialog(self):
        """Show dialog to add a new employee"""
        try:
            # Create dialog window
            dialog = tk.Toplevel(self.settings_win)
            dialog.title("Add New Employee")
            dialog.geometry("550x650")
            dialog.configure(bg="#000000")
            dialog.resizable(True, True)  # Make resizable
            dialog.minsize(500, 550)  # Set minimum size
            dialog.transient(self.settings_win)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
            y = (dialog.winfo_screenheight() // 2) - (650 // 2)
            dialog.geometry(f"550x650+{x}+{y}")
            
            # Create main container with scrollbar
            container = tk.Frame(dialog, bg="#000000")
            container.pack(fill='both', expand=True)
            
            # Create canvas and scrollbar
            canvas = tk.Canvas(container, bg="#000000", highlightthickness=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#000000")
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Main frame (now inside scrollable frame)
            main_frame = tk.Frame(scrollable_frame, bg="#000000")
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Enable mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            def bind_to_mousewheel(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def unbind_from_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
            
            canvas.bind('<Enter>', bind_to_mousewheel)
            canvas.bind('<Leave>', unbind_from_mousewheel)
            
            # Title
            title_label = tk.Label(main_frame, text="Add New Employee", 
                                 font=("Segoe UI", 16, "bold"), bg="#000000", fg="#fffde7")
            title_label.pack(pady=(0, 10))
            
            # Information panel
            info_frame = tk.Frame(main_frame, bg="#1a1a2e", relief='solid', bd=1)
            info_frame.pack(fill='x', pady=(0, 20))
            
            info_text = """💡 Password Requirements:
• At least 8 characters long
• Include uppercase and lowercase letters
• Include at least one number
• Username must be unique and 2+ characters"""
            
            info_label = tk.Label(info_frame, text=info_text, font=("Segoe UI", 9),
                                bg="#1a1a2e", fg="#b0b0b0", justify='left')
            info_label.pack(padx=15, pady=10, anchor='w')
            
            # Entry variables
            first_name_var = tk.StringVar()
            last_name_var = tk.StringVar()
            username_var = tk.StringVar()
            password_var = tk.StringVar()
            access_level_var = tk.StringVar(value="Level 1")
            
            # Form fields
            fields = [
                ("First Name:", first_name_var),
                ("Last Name:", last_name_var),
                ("Username:", username_var),
                ("Password:", password_var)
            ]
            
            entries = {}
            for field_name, var in fields:
                field_frame = tk.Frame(main_frame, bg="#000000")
                field_frame.pack(fill='x', pady=(0, 15))
                
                label = tk.Label(field_frame, text=field_name, font=("Segoe UI", 11),
                               bg="#000000", fg="#fffde7")
                label.pack(anchor='w', pady=(0, 5))
                
                if field_name == "Password:":
                    entry = tk.Entry(field_frame, textvariable=var, font=("Segoe UI", 11),
                                   bg="#23272b", fg="#fffde7", insertbackground="#fffde7",
                                   relief='flat', bd=1, show="*")
                else:
                    entry = tk.Entry(field_frame, textvariable=var, font=("Segoe UI", 11),
                                   bg="#23272b", fg="#fffde7", insertbackground="#fffde7",
                                   relief='flat', bd=1)
                entry.pack(fill='x', ipady=8)
                entries[field_name] = entry
            
            # Access Level field
            access_frame = tk.Frame(main_frame, bg="#000000")
            access_frame.pack(fill='x', pady=(0, 15))
            
            access_label = tk.Label(access_frame, text="Access Level:", font=("Segoe UI", 11),
                                  bg="#000000", fg="#fffde7")
            access_label.pack(anchor='w', pady=(0, 5))
            
            access_combo = ttk.Combobox(access_frame, textvariable=access_level_var,
                                      values=["Level 1", "Level 2", "Level 3"],
                                      state="readonly", font=("Segoe UI", 11))
            access_combo.pack(fill='x', ipady=5)
            
            # Validation message frame
            validation_frame = tk.Frame(main_frame, bg="#000000")
            validation_frame.pack(fill='x', pady=(10, 0))
            
            validation_label = tk.Label(validation_frame, text="", font=("Segoe UI", 9),
                                       bg="#000000", fg="#ff6b6b", justify='left')
            validation_label.pack(fill='x', anchor='w')
            
            # Configure validation label to update wraplength on resize
            def update_wraplength(event=None):
                width = validation_frame.winfo_width()
                if width > 1:  # Only update if frame has been rendered
                    validation_label.config(wraplength=max(300, width - 20))
            
            validation_frame.bind('<Configure>', update_wraplength)
            dialog.after(100, update_wraplength)  # Set initial wraplength
            
            # Buttons frame
            btn_frame = tk.Frame(main_frame, bg="#000000")
            btn_frame.pack(pady=(20, 0), anchor='e')
            
            def validate_and_add():
                # Clear previous validation message
                validation_label.config(text="")
                
                # Get values
                first_name = first_name_var.get().strip()
                last_name = last_name_var.get().strip()
                username = username_var.get().strip()
                password = password_var.get().strip()
                access_level = access_level_var.get()
                
                # Use comprehensive validation
                validation_errors = self.validate_user_input(first_name, last_name, username, password)
                
                # Check if username already exists
                if not validation_errors and self.username_exists(username):
                    validation_errors.append("Username already exists. Please choose a different username.")
                
                # Display validation errors
                if validation_errors:
                    validation_label.config(text=" • ".join(validation_errors))
                    return
                
                # Add the employee
                success, message = self.add_employee_to_database(first_name, last_name, username, 
                                                               password, access_level)
                if success:
                    messagebox.showinfo("Success", "Employee added successfully!")
                    dialog.destroy()
                    self.load_user_data()  # Refresh the user list
                else:
                    validation_label.config(text=f"Error: {message}")
            
            def cancel_add():
                dialog.destroy()
            
            # Cancel button
            cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                                 bg="#666", fg="#fff", relief='flat',
                                 activebackground="#555", activeforeground="#fff",
                                 width=10, command=cancel_add)
            cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Add button
            add_btn = tk.Button(btn_frame, text="Add Employee", font=("Segoe UI", 11, "bold"),
                              bg="#28a745", fg="#fff", relief='flat',
                              activebackground="#218838", activeforeground="#fff",
                              width=12, command=validate_and_add)
            add_btn.pack(side=tk.RIGHT)
            
            # Focus on first entry
            entries["First Name:"].focus()
            
            # Set up tab order for better keyboard navigation
            entries["First Name:"].bind('<Return>', lambda e: entries["Last Name:"].focus())
            entries["Last Name:"].bind('<Return>', lambda e: entries["Username:"].focus())
            entries["Username:"].bind('<Return>', lambda e: entries["Password:"].focus())
            entries["Password:"].bind('<Return>', lambda e: access_combo.focus())
            access_combo.bind('<Return>', lambda e: validate_and_add())
            
            # Bind Escape key to cancel
            dialog.bind('<Escape>', lambda e: cancel_add())
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open add employee dialog: {e}")

    def remove_employee_dialog(self):
        """Show dialog to remove an employee"""
        try:
            # Get selected item
            selected = self.user_tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select an employee to remove.")
                return
                
            item_id = selected[0]
            if item_id not in self.original_user_data:
                messagebox.showerror("Error", "Could not find employee data.")
                return
                
            user_data = self.original_user_data[item_id]
            display_name = f"{user_data['first_name']} {user_data['last_name']}"
            username = user_data['username']
            
            # Prevent removal of current user
            current_username = getattr(self.parent_settings.parent, 'username', None)
            if current_username and username.lower() == current_username.lower():
                messagebox.showwarning("Cannot Remove", "You cannot remove your own account.")
                return
            
            # Confirm removal
            confirm_msg = f"Are you sure you want to remove employee:\n\n{display_name} ({username})\n\nThis action cannot be undone."
            if not messagebox.askyesno("Confirm Removal", confirm_msg):
                return
            
            # Remove from database
            success, message = self.remove_employee_from_database(username)
            if success:
                messagebox.showinfo("Success", f"Employee {display_name} has been removed successfully!")
                self.load_user_data()  # Refresh the user list
            else:
                messagebox.showerror("Error", f"Failed to remove employee: {message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove employee: {e}")

    def edit_employee_dialog(self):
        """Show dialog to edit an employee"""
        try:
            # Get selected item
            selected = self.user_tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select an employee to edit.")
                return
                
            item_id = selected[0]
            if item_id not in self.original_user_data:
                messagebox.showerror("Error", "Could not find employee data.")
                return
                
            user_data = self.original_user_data[item_id]
            
            # Create dialog window
            dialog = tk.Toplevel(self.settings_win)
            dialog.title("Edit Employee")
            dialog.geometry("550x600")
            dialog.configure(bg="#000000")
            dialog.resizable(True, True)  # Make resizable
            dialog.minsize(500, 500)  # Set minimum size
            dialog.transient(self.settings_win)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
            y = (dialog.winfo_screenheight() // 2) - (600 // 2)
            dialog.geometry(f"550x600+{x}+{y}")
            
            # Create main container with scrollbar
            container = tk.Frame(dialog, bg="#000000")
            container.pack(fill='both', expand=True)
            
            # Create canvas and scrollbar
            canvas = tk.Canvas(container, bg="#000000", highlightthickness=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#000000")
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Main frame (now inside scrollable frame)
            main_frame = tk.Frame(scrollable_frame, bg="#000000")
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Enable mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            def bind_to_mousewheel(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def unbind_from_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
            
            canvas.bind('<Enter>', bind_to_mousewheel)
            canvas.bind('<Leave>', unbind_from_mousewheel)
            
            # Title
            title_label = tk.Label(main_frame, text="Edit Employee", 
                                 font=("Segoe UI", 16, "bold"), bg="#000000", fg="#fffde7")
            title_label.pack(pady=(0, 10))
            
            # Information panel
            info_frame = tk.Frame(main_frame, bg="#1a1a2e", relief='solid', bd=1)
            info_frame.pack(fill='x', pady=(0, 20))
            
            info_text = """💡 Edit Information:
• Username can be changed (must be unique)
• ⚠️ Changing your own username will require re-login
• Leave password blank to keep current password
• New passwords must meet security requirements
• Changes are applied immediately after clicking Update"""
            
            info_label = tk.Label(info_frame, text=info_text, font=("Segoe UI", 9),
                                bg="#1a1a2e", fg="#b0b0b0", justify='left')
            info_label.pack(padx=15, pady=10, anchor='w')
            
            # Entry variables with current values
            first_name_var = tk.StringVar(value=user_data['first_name'])
            last_name_var = tk.StringVar(value=user_data['last_name'])
            username_var = tk.StringVar(value=user_data['username'])
            access_level_var = tk.StringVar(value=user_data['access_level'])
            
            # Check if this is the current user's own record
            current_user = getattr(self.parent_settings.parent, 'username', None)
            is_current_user = current_user and current_user == user_data['username']
            
            # Form fields (all editable now)
            fields = [
                ("First Name:", first_name_var, False),
                ("Last Name:", last_name_var, False),
                ("Username:", username_var, False)  # Now editable
            ]
            
            entries = {}
            for field_name, var, readonly in fields:
                field_frame = tk.Frame(main_frame, bg="#000000")
                field_frame.pack(fill='x', pady=(0, 15))
                
                label = tk.Label(field_frame, text=field_name, font=("Segoe UI", 11),
                               bg="#000000", fg="#fffde7")
                label.pack(anchor='w', pady=(0, 5))
                
                # Special styling for username field if it's the current user
                username_bg = "#2a2a3e" if field_name == "Username:" and is_current_user else "#23272b"
                
                entry = tk.Entry(field_frame, textvariable=var, font=("Segoe UI", 11),
                               bg=username_bg if not readonly else "#444",
                               fg="#fffde7" if not readonly else "#888",
                               insertbackground="#fffde7",
                               relief='flat', bd=1,
                               state="readonly" if readonly else "normal")
                entry.pack(fill='x', ipady=8)
                entries[field_name] = entry
                
                # Add real-time username validation
                if field_name == "Username:":
                    username_status_label = tk.Label(field_frame, text="", font=("Segoe UI", 9),
                                                    bg="#000000", fg="#4CAF50")
                    username_status_label.pack(anchor='w', pady=(2, 0))
                    
                    # Add special indicator if this is current user
                    if is_current_user:
                        current_user_label = tk.Label(field_frame, text="👤 This is your own username", 
                                                     font=("Segoe UI", 8, "italic"),
                                                     bg="#000000", fg="#ff9800")
                        current_user_label.pack(anchor='w', pady=(2, 0))
                    
                    def check_username_availability(*args):
                        new_username = username_var.get().strip()
                        original_username = user_data['username']
                        
                        if not new_username:
                            username_status_label.config(text="", fg="#888")
                        elif new_username == original_username:
                            username_status_label.config(text="✓ Current username", fg="#888")
                        elif len(new_username) < 2:
                            username_status_label.config(text="⚠ Username must be at least 2 characters", fg="#ff9800")
                        elif self.username_exists(new_username, original_username):
                            username_status_label.config(text="✗ Username already exists", fg="#f44336")
                        else:
                            username_status_label.config(text="✓ Username available", fg="#4CAF50")
                    
                    # Bind username change event
                    username_var.trace('w', check_username_availability)
                    # Initial check
                    check_username_availability()
            
            # Access Level field
            access_frame = tk.Frame(main_frame, bg="#000000")
            access_frame.pack(fill='x', pady=(0, 15))
            
            access_label = tk.Label(access_frame, text="Access Level:", font=("Segoe UI", 11),
                                  bg="#000000", fg="#fffde7")
            access_label.pack(anchor='w', pady=(0, 5))
            
            access_combo = ttk.Combobox(access_frame, textvariable=access_level_var,
                                      values=["Level 1", "Level 2", "Level 3"],
                                      state="readonly", font=("Segoe UI", 11))
            access_combo.pack(fill='x', ipady=5)
            
            # Password reset section
            password_frame = tk.Frame(main_frame, bg="#000000")
            password_frame.pack(fill='x', pady=(15, 0))
            
            password_label = tk.Label(password_frame, text="New Password (leave blank to keep current):", 
                                    font=("Segoe UI", 11), bg="#000000", fg="#fffde7")
            password_label.pack(anchor='w', pady=(0, 5))
            
            password_var = tk.StringVar()
            password_entry = tk.Entry(password_frame, textvariable=password_var, font=("Segoe UI", 11),
                                    bg="#23272b", fg="#fffde7", insertbackground="#fffde7",
                                    relief='flat', bd=1, show="*")
            password_entry.pack(fill='x', ipady=8)
            
            # Validation message frame
            validation_frame = tk.Frame(main_frame, bg="#000000")
            validation_frame.pack(fill='x', pady=(10, 0))
            
            validation_label = tk.Label(validation_frame, text="", font=("Segoe UI", 9),
                                       bg="#000000", fg="#ff6b6b", justify='left')
            validation_label.pack(fill='x', anchor='w')
            
            # Configure validation label to update wraplength on resize
            def update_edit_wraplength(event=None):
                width = validation_frame.winfo_width()
                if width > 1:  # Only update if frame has been rendered
                    validation_label.config(wraplength=max(300, width - 20))
            
            validation_frame.bind('<Configure>', update_edit_wraplength)
            dialog.after(100, update_edit_wraplength)  # Set initial wraplength
            
            # Buttons frame
            btn_frame = tk.Frame(main_frame, bg="#000000")
            btn_frame.pack(pady=(20, 0), anchor='e')
            
            def validate_and_update():
                # Clear previous validation message
                validation_label.config(text="")
                
                # Get values
                first_name = first_name_var.get().strip()
                last_name = last_name_var.get().strip()
                new_username = username_var.get().strip()
                original_username = user_data['username']  # Store original username
                new_password = password_var.get().strip()
                access_level = access_level_var.get()
                
                # Check if username changed
                username_changed = new_username != original_username
                
                # Validate username change
                if username_changed:
                    # Check if new username already exists (excluding current username)
                    if self.username_exists(new_username, original_username):
                        validation_label.config(text="Error: Username already exists. Please choose a different username.")
                        return
                    
                    # Check if user is editing their own username
                    current_user = getattr(self.parent_settings.parent, 'username', None)
                    if current_user and current_user == original_username:
                        # Show detailed confirmation dialog for own username change
                        confirm_dialog = tk.Toplevel(dialog)
                        confirm_dialog.title("Confirm Username Change")
                        confirm_dialog.geometry("500x300")
                        confirm_dialog.configure(bg="#000000")
                        confirm_dialog.transient(dialog)
                        confirm_dialog.grab_set()
                        
                        # Center the confirmation dialog
                        confirm_dialog.update_idletasks()
                        x = (confirm_dialog.winfo_screenwidth() // 2) - (250)
                        y = (confirm_dialog.winfo_screenheight() // 2) - (150)
                        confirm_dialog.geometry(f"500x300+{x}+{y}")
                        
                        # Warning content
                        warning_frame = tk.Frame(confirm_dialog, bg="#000000")
                        warning_frame.pack(fill='both', expand=True, padx=20, pady=20)
                        
                        tk.Label(warning_frame, text="⚠️ Username Change Confirmation", 
                               font=("Segoe UI", 14, "bold"), bg="#000000", fg="#ff9800").pack(pady=(0, 15))
                        
                        warning_text = f"""You are about to change your own username:

From: '{original_username}'
To: '{new_username}'

IMPORTANT:
• You will be logged out immediately after this change
• You must log in again using the NEW username: '{new_username}'
• Make sure you remember the new username
• Your password will remain the same

Are you absolutely sure you want to proceed?"""
                        
                        tk.Label(warning_frame, text=warning_text, font=("Segoe UI", 10),
                               bg="#000000", fg="#fffde7", justify='left', wraplength=450).pack(pady=(0, 20))
                        
                        # Buttons for confirmation dialog
                        btn_frame = tk.Frame(warning_frame, bg="#000000")
                        btn_frame.pack(anchor='e')
                        
                        proceed_with_change = [False]  # Use list to modify from inner function
                        
                        def confirm_username_change():
                            proceed_with_change[0] = True
                            confirm_dialog.destroy()
                            
                        def cancel_username_change():
                            proceed_with_change[0] = False
                            confirm_dialog.destroy()
                        
                        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                                bg="#666", fg="#fff", relief='flat',
                                activebackground="#555", activeforeground="#fff",
                                width=12, command=cancel_username_change).pack(side=tk.RIGHT, padx=(10, 0))
                        
                        tk.Button(btn_frame, text="Yes, Change Username", font=("Segoe UI", 11, "bold"),
                                bg="#f44336", fg="#fff", relief='flat',
                                activebackground="#d32f2f", activeforeground="#fff",
                                width=18, command=confirm_username_change).pack(side=tk.RIGHT)
                        
                        # Wait for user response
                        confirm_dialog.wait_window()
                        
                        if not proceed_with_change[0]:
                            return
                
                # Use comprehensive validation (password optional for updates)
                validation_errors = self.validate_user_input(first_name, last_name, new_username, 
                                                           new_password if new_password else None)
                
                # Display validation errors
                if validation_errors:
                    validation_label.config(text=" • ".join(validation_errors))
                    return
                
                # Update the employee
                success, message = self.update_employee_in_database(original_username, first_name, last_name, 
                                                                  new_username if username_changed else None,
                                                                  new_password if new_password else None, 
                                                                  access_level)
                if success:
                    # Check if user changed their own username
                    current_user = getattr(self.parent_settings.parent, 'username', None)
                    if username_changed and current_user and current_user == original_username:
                        messagebox.showinfo("Success", 
                                          f"Username changed successfully from '{original_username}' to '{new_username}'.\n\n"
                                          f"You will be logged out and need to log in again with your new username: '{new_username}'")
                        dialog.destroy()
                        # Handle logout
                        self.handle_current_user_logout()
                    else:
                        messagebox.showinfo("Success", "Employee updated successfully!")
                        dialog.destroy()
                        self.load_user_data()  # Refresh the user list
                else:
                    validation_label.config(text=f"Error: {message}")
            
            def cancel_edit():
                dialog.destroy()
            
            # Cancel button
            cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                                 bg="#666", fg="#fff", relief='flat',
                                 activebackground="#555", activeforeground="#fff",
                                 width=10, command=cancel_edit)
            cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Update button
            update_btn = tk.Button(btn_frame, text="Update Employee", font=("Segoe UI", 11, "bold"),
                                 bg="#ffc107", fg="#000", relief='flat',
                                 activebackground="#e0a800", activeforeground="#000",
                                 width=14, command=validate_and_update)
            update_btn.pack(side=tk.RIGHT)
            
            # Focus on first entry
            entries["First Name:"].focus()
            
            # Set up tab order for better keyboard navigation
            entries["First Name:"].bind('<Return>', lambda e: entries["Last Name:"].focus())
            entries["Last Name:"].bind('<Return>', lambda e: access_combo.focus())
            access_combo.bind('<Return>', lambda e: password_entry.focus())
            password_entry.bind('<Return>', lambda e: validate_and_update())
            
            # Bind Escape key to cancel
            dialog.bind('<Escape>', lambda e: cancel_edit())
            
        except Exception as e:
            try:
                messagebox.showerror("Error", f"Failed to open edit employee dialog: {e}")
            except Exception:
                print(f"[DEBUG] Failed showing error dialog: {e}")
