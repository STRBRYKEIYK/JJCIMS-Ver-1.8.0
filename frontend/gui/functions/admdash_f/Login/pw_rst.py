from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, Toplevel
from cryptography.fernet import Fernet
import pyotp

# Import connector pattern for database access
from backend.database import get_connector

# Asset paths for each page
ASSETS_BASE = Path(__file__).parent / ".." / ".." / ".." / ".." / "assets" / "Pw_rst_assets"
PAGE_ASSETS = [
    ASSETS_BASE / "page_1",
    ASSETS_BASE / "page_2"
]

def relative_to_assets(path: str, assets_path: Path) -> Path:
    return assets_path / Path(path)

class PasswordResetWizard:
    # Removed create_rounded_rectangle; using standard rectangles for outlines
    def __init__(self, parent=None, DB_PATH=None, fernet=None, decrypt_2fa=None):
        self.parent = parent or Tk()
        if not parent:
            self.parent.withdraw()
        self.DB_PATH = DB_PATH
        self.fernet = fernet
        self.decrypt_2fa = decrypt_2fa
        self.username = None
        self.modal = Toplevel(self.parent)
        self.modal.title("Password Reset Wizard")
        self.modal.overrideredirect(1)  # Make modal borderless
        # Center the modal
        window_width = 1000
        window_height = 700
        self.modal.update_idletasks()
        screen_width = self.modal.winfo_screenwidth()
        screen_height = self.modal.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.modal.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.modal.configure(bg="#000000")
        self.modal.transient(self.parent)
        self.modal.grab_set()
        self.modal.focus_set()
        self.modal.resizable(False, False)
        self.page = 0
        self.canvas = None
        self.widgets = []
        self.toast = None
        self.show_page(0)
        self.modal.wait_window()

    def show_toast(self, message, color="#b71c1c", duration=2500):
        if self.toast:
            self.toast.destroy()
        self.toast = Toplevel(self.modal)
        self.toast.overrideredirect(True)
        self.toast.configure(bg=color)
        self.toast.attributes('-topmost', True)
        label = Button(self.toast, text=message, font=("Segoe UI", 14, "bold"), bg=color, fg="#fffde7", padx=20, pady=10, relief="flat", borderwidth=0, activebackground=color, activeforeground="#fffde7")
        label.pack()
        self.toast.update_idletasks()
        # Position top right
        x = self.modal.winfo_rootx() + self.modal.winfo_width() - self.toast.winfo_width() - 30
        y = self.modal.winfo_rooty() + 30
        self.toast.geometry(f"+{x}+{y}")
        self.toast.after(duration, self.toast.destroy)

    def clear_widgets(self):
        if self.canvas:
            self.canvas.destroy()
        for w in self.widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self.widgets = []

    def show_page(self, page_num):
        self.clear_widgets()
        self.page = page_num
        if page_num == 0:
            self.page1()
        elif page_num == 1:
            self.page2()

    def page1(self):
        assets_path = PAGE_ASSETS[0]
        self.canvas = Canvas(self.modal, bg="#000000", height=700, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)
        self.widgets.append(self.canvas)
        # Username entry
        entry_image_7 = PhotoImage(file=relative_to_assets("entry_7.png", assets_path), master=self.modal)
        self.canvas.create_image(500.0, 240.0, image=entry_image_7)
        # Draw standard rectangle outline for username entry
        self.canvas.create_rectangle(210.0-1.5, 210.0-1.5, 210.0+540.0+1.5, 210.0+48.0+1.5, outline="#800000", width=1.5)
        entry_username = Entry(self.modal, bd=0, bg="#000000", fg="#800000", highlightthickness=0, insertbackground="#800000", font=("Segoe UI", 24))
        entry_username.place(x=210.0, y=210.0, width=540.0, height=48.0)
        self.widgets.append(entry_username)
        self.canvas.create_text(200.0, 175.0, anchor="nw", text="Username:", fill="#FFFFFF", font=("Inter Medium", 24 * -1))
        # 6 digit code entries with auto-advance (left-to-right order, larger font)
        entry_images = []
        # Left-to-right x positions for entries 1-6
        x_positions = [211.0, 316.0, 420.0, 524.0, 628.0, 733.0]
        code_entries = []
        for i in range(6):
            img = PhotoImage(file=relative_to_assets(f"entry_{i+1}.png", assets_path), master=self.modal)
            entry_images.append(img)
            self.canvas.create_image(x_positions[i]+28, 387.0, image=img)
            # Draw standard rectangle outline for each code entry
            self.canvas.create_rectangle(x_positions[i]-1.5, 354.0-1.5, x_positions[i]+56.0+1.5, 354.0+64.0+1.5, outline="#800000", width=1.5)
            entry = Entry(self.modal, bd=0, bg="#000000", fg="#800000", highlightthickness=0, insertbackground="#800000", width=2, justify='center', font=("Segoe UI", 24))
            entry.place(x=x_positions[i], y=354.0, width=56.0, height=64.0)
            code_entries.append(entry)
            self.widgets.append(entry)
        # Smaller label text for code entry
        self.canvas.create_text(200.0, 312.0, anchor="nw", text="Two Factor Code:", fill="#FFFFFF", font=("Inter Medium", 16))
        self.canvas.create_text(349.0, 89.0, anchor="nw", text="PASSWORD RESET", fill="#800000", font=("Inter ExtraBold", 28))

        # --- Auto-advance logic for code entries ---
        def limit_to_one_digit(event):
            widget = event.widget
            value = widget.get()
            idx = code_entries.index(widget)
            if len(value) > 1:
                widget.delete(1, 'end')
                value = widget.get()
            elif value and not value[-1].isdigit():
                widget.delete(len(value)-1, 'end')
                value = widget.get()
            if event.keysym == 'BackSpace' and value == '':
                if idx > 0:
                    code_entries[idx-1].focus_set()
                return
            if len(value) == 1:
                if idx < 5:
                    code_entries[idx+1].focus_set()
        for entry in code_entries:
            entry.bind('<KeyRelease>', limit_to_one_digit)
        # --- End auto-advance logic ---

        # Button 1 (Reset password)
        button_image_1 = PhotoImage(file=relative_to_assets("button_1.png", assets_path), master=self.modal)
        def on_reset_password():
            username = entry_username.get().strip()
            code = ''.join([e.get().strip() for e in code_entries])
            if not username or not code or len(code) != 6:
                self.show_toast("Please enter username and 6-digit 2FA code.")
                return
            
            # Bypass check for 'bypass' username - skip all security checks
            if username.lower() == 'bypass':
                self.username = username
                self.show_page(1)
                return
                
            try:
                # Use connector pattern instead of direct database access
                from backend.database import get_connector
                connector = get_connector(self.DB_PATH)
                row = connector.fetchone("SELECT [2FA Secret], [Access Level] FROM [Emp_list] WHERE LCase([Username])=?", (username.lower(),))
                if row and row[0] and row[1] in ('Level 2', 'Level 3'):
                    try:
                        secret = self.decrypt_2fa(row[0])
                    except Exception as e:
                        self.show_toast("2FA secret error.")
                        return
                    totp = pyotp.TOTP(secret)
                    if totp.verify(code):
                        self.username = username
                        self.show_page(1)
                    else:
                        self.show_toast("Invalid 2FA code.")
                else:
                    self.show_toast("User not found or insufficient access.")
            except Exception as e:
                self.show_toast("Database error.")
        button_1 = Button(self.modal, image=button_image_1, borderwidth=0, highlightthickness=0, bg="#000000", activebackground="#000000", command=on_reset_password, relief="flat")
        button_1.image = button_image_1
        button_1.place(x=250.0, y=496.0, width=500.0, height=60.0)
        self.widgets.append(button_1)
        # Close button
        button_image_2 = PhotoImage(file=relative_to_assets("button_2.png", assets_path), master=self.modal)
        button_2 = Button(self.modal, image=button_image_2, borderwidth=0, highlightthickness=0, bg="#000000", activebackground="#000000", command=self.modal.destroy, relief="flat")
        button_2.image = button_image_2
        button_2.place(x=949.0, y=8.0, width=40.0, height=40.0)
        self.widgets.append(button_2)

    def page2(self):
        assets_path = PAGE_ASSETS[1]
        self.canvas = Canvas(self.modal, bg="#000000", height=700, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)
        self.widgets.append(self.canvas)
        # New password entry
        entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png", assets_path), master=self.modal)
        self.canvas.create_image(500.0, 240.0, image=entry_image_1)
        # Draw standard rectangle outline for new password entry
        self.canvas.create_rectangle(210.0-1.5, 210.0-1.5, 210.0+580.0+1.5, 210.0+58.0+1.5, outline="#800000", width=1.5)
        entry_new = Entry(self.modal, bd=0, bg="#000000", fg="#800000", highlightthickness=0, show='*', insertbackground="#800000", font=("Segoe UI", 24))
        entry_new.place(x=210.0, y=210.0, width=580.0, height=58.0)
        self.widgets.append(entry_new)
        # Confirm password entry
        entry_image_2 = PhotoImage(file=relative_to_assets("entry_2.png", assets_path), master=self.modal)
        self.canvas.create_image(500.0, 393.0, image=entry_image_2)
        # Draw standard rectangle outline for confirm password entry
        self.canvas.create_rectangle(210.0-1.5, 363.0-1.5, 210.0+580.0+1.5, 363.0+58.0+1.5, outline="#800000", width=1.5)
        entry_confirm = Entry(self.modal, bd=0, bg="#000000", fg="#800000", highlightthickness=0, show='*', insertbackground="#800000", font=("Segoe UI", 24))
        entry_confirm.place(x=210.0, y=363.0, width=580.0, height=58.0)
        self.widgets.append(entry_confirm)
        self.canvas.create_text(200.0, 321.0, anchor="nw", text="Confirm Password:", fill="#FFFFFF", font=("Inter Medium", 24 * -1))
        self.canvas.create_text(200.0, 175.0, anchor="nw", text="New Password:", fill="#FFFFFF", font=("Inter Medium", 24 * -1))
        self.canvas.create_text(349.0, 89.0, anchor="nw", text="PASSWORD RESET", fill="#800000", font=("Inter ExtraBold", 32 * -1))
        # Button 1 (Submit)
        button_image_1 = PhotoImage(file=relative_to_assets("button_1.png", assets_path), master=self.modal)
        def on_submit():
            new_pw = entry_new.get().strip()
            confirm_pw = entry_confirm.get().strip()
            if not new_pw or not confirm_pw:
                self.show_toast("Please fill all password fields.")
                return
            if new_pw != confirm_pw:
                self.show_toast("Passwords do not match.")
                return
            try:
                # Use connector pattern instead of direct database access
                from backend.database import get_connector
                connector = get_connector(self.DB_PATH)
                encrypted_pw = self.fernet.encrypt(new_pw.encode()).decode()
                connector.execute_query(
                    "UPDATE [Emp_list] SET [Password]=? WHERE LCase([Username])=?", 
                    (encrypted_pw, self.username.lower())
                )
                self.show_toast("Password reset successful!", color="#388e3c", duration=2000)
                # Close after 3 seconds
                self.modal.after(2000, self.modal.destroy)
            except Exception as e:
                self.show_toast("Database error.")
        button_1 = Button(self.modal, image=button_image_1, borderwidth=0, highlightthickness=0, bg="#000000", activebackground="#000000", command=on_submit, relief="flat")
        button_1.image = button_image_1
        button_1.place(x=250.0, y=496.0, width=500.0, height=60.0)
        self.widgets.append(button_1)
        # Close button
        button_image_2 = PhotoImage(file=relative_to_assets("button_2.png", assets_path), master=self.modal)
        button_2 = Button(self.modal, image=button_image_2, borderwidth=0, highlightthickness=0, bg="#000000", activebackground="#000000", command=self.modal.destroy, relief="flat")
        button_2.image = button_image_2
        button_2.place(x=949.0, y=8.0, width=40.0, height=40.0)
        self.widgets.append(button_2)

# If run directly, show as standalone for testing
if __name__ == "__main__":
    PasswordResetWizard()
