import tkinter as tk

def show_error(dashboard, error_message, retry_callback=None):
    """Display an enhanced error message with retry options."""
    error_window = tk.Toplevel(dashboard.root)
    error_window.title("Error")
    error_window.geometry("400x200")
    error_window.resizable(False, False)
    # Assume center_window is globally available or import as needed
    from gui.functions.admdash_f.admdash_imp import center_window
    center_window(error_window)
    error_window.configure(bg="#000000")

    tk.Label(
        error_window, text="⚠️ Error", font=("Arial", 16, "bold"), bg="#000000", fg="#ff6f00"
    ).pack(pady=10)
    tk.Label(
        error_window, text=error_message, font=("Arial", 12), bg="#000000", fg="#fffde7"
    ).pack(pady=10)

    if retry_callback:
        tk.Button(
            error_window, text="Retry", command=lambda: [retry_callback(), error_window.destroy()],
            font=("Arial", 12, "bold"), bg="#4CAF50", fg="white"
        ).pack(pady=10)

    tk.Button(
        error_window, text="Close", command=error_window.destroy,
        font=("Arial", 12, "bold"), bg="#F44336", fg="white"
    ).pack(pady=10)
