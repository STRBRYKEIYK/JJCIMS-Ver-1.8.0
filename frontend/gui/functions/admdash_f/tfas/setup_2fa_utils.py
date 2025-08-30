
# Minimal utility to launch the tfa_su_wizard as a modal, borderless window from Admin login
def launch_2fa_setup_modal(parent, username, db_path, fernet_key_path, colors=None):
    """
    Launch the 2FA setup wizard as a modal, borderless window using tfa_su_wizard.
    - parent: Tkinter parent window
    - username: Username for whom to set up 2FA
    - db_path: Path to the Access database
    - fernet_key_path: Path to the Fernet key file
    - colors: Dict of color settings (optional)
    """
    from tkinter import Toplevel
    from gui.functions.admdash_f.tfas.tfa_su_wizard import MultiStep2FAWizard
    # Create a borderless modal window
    win = Toplevel(parent)
    win.overrideredirect(True)
    win.grab_set()  # Modal
    win.configure(bg=colors["bg"] if colors and "bg" in colors else "#000000")
    # Center the window (700x700)
    win.geometry(f"700x700+{win.winfo_screenwidth()//2-350}+{win.winfo_screenheight()//2-350}")
    # Launch the wizard in this window
    MultiStep2FAWizard(
        parent=win,
        username=username,
        db_path=db_path,
        fernet_key_path=fernet_key_path,
        popup=False,  # Use the provided window
        colors=colors or {"bg": "#000000", "header": "#800000"}
    )
    win.focus_set()
    win.wait_window()

# Backward compatibility: allow import as 'setup_2fa'
setup_2fa = launch_2fa_setup_modal
