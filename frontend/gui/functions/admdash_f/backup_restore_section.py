# BackupRestoreFrame: Embeddable Frame for Backup/Restore with Tab-like Switching
# Default is Backup. Button_4 switches between Backup and Restore views.

from pathlib import Path
from tkinter import Canvas, Button, PhotoImage, Entry, Frame, filedialog
import os
import shutil
from datetime import datetime
import re
from backend.database import get_db_path


class BackupRestoreSection(Frame):
    def __init__(self, parent, assets_backup, assets_restore, *args, **kwargs):
        super().__init__(parent, bg="#000000", width=1377, height=1080, *args, **kwargs)
        self.assets_backup = Path(assets_backup)
        self.assets_restore = Path(assets_restore)
        self.width = 1377
        self.height = 1080
        # Remove pack_propagate and pack, use place to center
        # self.pack_propagate(False)
        self.backup_canvas = None
        self.restore_canvas = None
        self._backup_images = []
        self._restore_images = []
        self.folder_path_backup = None
        self.folder_path_restore = None
        # Placement of this frame should be handled by the parent, not here.
        # Path to persist last backup/restore times
        import os

        self.status_file = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../../config/backup_restore_status.json"
            )
        )
        self.last_backup_time = None
        self.last_restore_time = None
        self._load_status()
        self.show_backup()

    def _load_status(self):
        import os
        import json

        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.last_backup_time = data.get("last_backup_time")
                self.last_restore_time = data.get("last_restore_time")
            except Exception:
                self.last_backup_time = None
                self.last_restore_time = None

    def _save_status(self):
        import os
        import json

        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "last_backup_time": self.last_backup_time,
                        "last_restore_time": self.last_restore_time,
                    },
                    f,
                )
        except Exception:
            pass

    def relative_to_assets_backup(self, path: str) -> Path:
        return self.assets_backup / Path(path)

    def relative_to_assets_restore(self, path: str) -> Path:
        return self.assets_restore / Path(path)

    def show_backup(self):
        if self.restore_canvas:
            self.restore_canvas.place_forget()
        if self.backup_canvas:
            self.backup_canvas.place(x=0, y=0)
            return
        c = Canvas(
            self,
            bg="#000000",
            width=self.width,
            height=self.height,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        c.place(x=0, y=0)

        # Image 1 - Main background/header
        img1 = PhotoImage(file=self.relative_to_assets_backup("image_1.png"))
        c.create_image(997.0, 116.0, image=img1)

        # Store the text ID for dynamic update - Last Backup text
        self.last_backup_text_id = c.create_text(
            785.0,
            93.0,
            anchor="nw",
            text=self.get_last_backup_text(),
            fill="#000000",
            font=("Inter MediumItalic", 24 * -1),
        )

        # Image 2 - Lower section
        img2 = PhotoImage(file=self.relative_to_assets_backup("image_2.png"))
        c.create_image(700.0, 445.0, image=img2)

        # Image 3 - Middle section
        img3 = PhotoImage(file=self.relative_to_assets_backup("image_3.png"))
        c.create_image(699.0, 343.0, image=img3)

        # Button 1 - Browse button
        btn_img1 = PhotoImage(file=self.relative_to_assets_backup("button_1.png"))
        Button(
            c,
            image=btn_img1,
            background="#000D1D",
            activebackground="#000D1D",
            borderwidth=0,
            highlightthickness=0,
            command=self.select_backup_folder,
            relief="flat",
        ).place(x=1056.0, y=558.0, width=74.93187713623047, height=57.44150161743164)

        # Entry field for folder path
        entry_img = PhotoImage(file=self.relative_to_assets_backup("entry_1.png"))
        c.create_image(666.0, 587.0, image=entry_img)
        self.entry_backup = Entry(
            c,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter Regular", 24),
            insertbackground="#FFFFFF",
            highlightthickness=0,
        )
        self.entry_backup.place(x=290.0, y=561.0, width=740.0, height=45.0)
        self.entry_backup.insert(
            0, self.folder_path_backup or "Select backup folder..."
        )

        # Button 2 - Backup Now button
        btn_img2 = PhotoImage(file=self.relative_to_assets_backup("button_2.png"))
        Button(
            c,
            image=btn_img2,
            background="#000D1D",
            activebackground="#000D1D",
            borderwidth=0,
            highlightthickness=0,
            command=self.backup_now,
            relief="flat",
        ).place(x=542.0, y=654.0, width=315.22344970703125, height=58.406524658203125)

        # Button 3 - Switch to Restore tab
        btn_img3 = PhotoImage(file=self.relative_to_assets_backup("button_3.png"))
        Button(
            c,
            image=btn_img3,
            background="#000000",
            activebackground="#000000",
            borderwidth=0,
            highlightthickness=0,
            command=self.show_restore,
            relief="flat",
        ).place(
            x=375.79473876953125,
            y=80.0,
            width=209.80926513671875,
            height=48.045494079589844,
        )

        # Image 4 - Tab indicator/icon
        img4 = PhotoImage(file=self.relative_to_assets_backup("image_4.png"))
        c.create_image(268.9854736328125, 103.0, image=img4)

        self.backup_canvas = c
        self._backup_images = [
            img1,
            img2,
            img3,
            img4,
            entry_img,
            btn_img1,
            btn_img2,
            btn_img3,
        ]
        # Update text in case it changed
        if hasattr(self, "last_backup_text_id"):
            self.backup_canvas.itemconfig(
                self.last_backup_text_id, text=self.get_last_backup_text()
            )

    def get_last_backup_text(self):
        if hasattr(self, "last_backup_time") and self.last_backup_time:
            return f"Last Backup: {self.last_backup_time}"
        else:
            return "Last Backup: N/A"

    def backup_now(self):
        # Get user-selected folder
        folder = self.folder_path_backup or self.entry_backup.get()
        if not folder or folder.strip() == "Select backup folder...":
            self.show_toast("Please select a backup folder first.", success=False)
            return
        if not os.path.isdir(folder):
            self.show_toast("Backup folder does not exist!", success=False)
            return
        # Ensure 'JJCIMS BACKUP' folder exists inside the selected folder
        backup_root = os.path.join(folder, "JJCIMS BACKUP")
        try:
            os.makedirs(backup_root, exist_ok=True)
        except Exception as e:
            self.show_toast(f"Failed to create backup root folder: {e}", success=False)
            return
        # Prepare timestamped subfolder inside 'JJCIMS BACKUP'
        now = datetime.now()
        folder_name = now.strftime("%d-%m-%Y %I-%M %p")
        backup_dir = os.path.join(backup_root, folder_name)
        try:
            os.makedirs(backup_dir, exist_ok=True)
            # Define source file (canonical database only)
            src_db = get_db_path()
            if os.path.exists(src_db):
                shutil.copy2(src_db, os.path.join(backup_dir, "JJCIMS.accdb"))
            else:
                self.show_toast("File not found: JJCIMS.accdb", success=False)
                return
            # Update last backup time and canvas text
            self.last_backup_time = now.strftime("%d/%m/%Y | %I:%M %p")
            self._save_status()
            if hasattr(self, "backup_canvas") and hasattr(self, "last_backup_text_id"):
                self.backup_canvas.itemconfig(
                    self.last_backup_text_id,
                    text=f"Last Backup: {self.last_backup_time}",
                )
            # Show two toasts: one for success, one for path (short)
            self.show_toast("Backup is Successful!", success=True)
            # Show only the folder name, not full path
            short_path = os.path.basename(backup_dir)
            self.after(
                1200,
                lambda: self.show_toast(
                    f"Saved in: {short_path}", success=True, duration=1800
                ),
            )
        except Exception as e:
            self.show_toast(f"Backup failed: {e}", success=False)

    def show_toast(self, message, success=True, duration=2500):
        # Toast notification in upper right with fade-in/fade-out
        import tkinter as tk

        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        # Calculate position: upper right of the parent window
        parent = self.winfo_toplevel()
        parent.update_idletasks()
        width = 400
        height = 54
        x = parent.winfo_x() + parent.winfo_width() - width - 20
        y = parent.winfo_y() + 40
        toast.geometry(f"{width}x{height}+{x}+{y}")
        bg = "#388e3c" if success else "#d32f2f"
        fg = "#fffde7"
        frame = tk.Frame(toast, bg=bg, bd=2, relief="ridge")
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=message,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            padx=18,
        )
        label.pack(fill="both", expand=True)

        # Fade in
        def fade_in(alpha=0):
            if alpha < 1.0:
                toast.attributes("-alpha", alpha)
                toast.after(20, lambda: fade_in(alpha + 0.08))
            else:
                toast.attributes("-alpha", 1.0)

        toast.attributes("-alpha", 0.0)
        fade_in()

        # Fade out after duration
        def fade_out(alpha=1.0):
            if alpha > 0:
                toast.attributes("-alpha", alpha)
                toast.after(20, lambda: fade_out(alpha - 0.08))
            else:
                toast.destroy()

        toast.after(duration, lambda: fade_out())

    def show_restore(self):
        if self.backup_canvas:
            self.backup_canvas.place_forget()
        if self.restore_canvas:
            self.restore_canvas.place(x=0, y=0)
            return
        c = Canvas(
            self,
            bg="#000000",
            width=self.width,
            height=self.height,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        c.place(x=0, y=0)

        # Image 1 - Main background/header
        img1 = PhotoImage(file=self.relative_to_assets_restore("image_1.png"))
        c.create_image(998.0, 120.0, image=img1)

        # Store the text ID for dynamic update - Last Restore text
        self.last_restore_text_id = c.create_text(
            785.0,
            93.0,
            anchor="nw",
            text=self.get_last_restore_text(),
            fill="#000000",
            font=("Inter MediumItalic", 24 * -1),
        )

        # Image 2 - Lower section
        img2 = PhotoImage(file=self.relative_to_assets_restore("image_2.png"))
        c.create_image(700.0, 445.0, image=img2)

        # Button 1 - Browse button
        btn_img1 = PhotoImage(file=self.relative_to_assets_restore("button_1.png"))
        Button(
            c,
            image=btn_img1,
            background="#1D0000",
            activebackground="#1D0000",
            borderwidth=0,
            highlightthickness=0,
            command=self.select_restore_folder,
            relief="flat",
        ).place(x=1056.0, y=558.0, width=75.0, height=57.30337142944336)

        # Entry field for folder path
        entry_img = PhotoImage(file=self.relative_to_assets_restore("entry_1.png"))
        c.create_image(666.0, 586.5, image=entry_img)
        self.entry_restore = Entry(
            c,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter Regular", 24),
            insertbackground="#FFFFFF",
            highlightthickness=0,
        )
        self.entry_restore.place(x=290.0, y=565.0, width=740.0, height=42.0)
        self.entry_restore.insert(
            0, self.folder_path_restore or "Select restore folder..."
        )

        # Button 2 - Restore Now button
        btn_img2 = PhotoImage(file=self.relative_to_assets_restore("button_2.png"))
        Button(
            c,
            image=btn_img2,
            background="#1D0000",
            activebackground="#1D0000",
            borderwidth=0,
            highlightthickness=0,
            command=self.restore_now,
            relief="flat",
        ).place(x=542.0, y=651.0, width=315.5105285644531, height=58.26612854003906)

        # Image 3 - Middle section
        img3 = PhotoImage(file=self.relative_to_assets_restore("image_3.png"))
        c.create_image(700.0, 357.0, image=img3)

        # Button 3 - Switch to Backup tab
        btn_img3 = PhotoImage(file=self.relative_to_assets_restore("button_3.png"))
        Button(
            c,
            image=btn_img3,
            background="#000000",
            activebackground="#000000",
            borderwidth=0,
            highlightthickness=0,
            command=self.show_backup,
            relief="flat",
        ).place(
            x=164.57522583007812,
            y=81.0,
            width=210.0545654296875,
            height=47.98387145996094,
        )

        # Image 4 - Tab indicator/icon
        img4 = PhotoImage(file=self.relative_to_assets_restore("image_4.png"))
        c.create_image(480.0, 104.0, image=img4)

        self.restore_canvas = c
        self._restore_images = [
            img1,
            img2,
            img3,
            img4,
            entry_img,
            btn_img1,
            btn_img2,
            btn_img3,
        ]
        # Update text in case it changed
        if hasattr(self, "last_restore_text_id"):
            self.restore_canvas.itemconfig(
                self.last_restore_text_id, text=self.get_last_restore_text()
            )

    def get_last_restore_text(self):
        if hasattr(self, "last_restore_time") and self.last_restore_time:
            return f"Last Restore: {self.last_restore_time}"
        else:
            return "Last Restore: N/A"

    def restore_now(self):
        # Get user-selected folder (should be a backup folder with date-time in name)
        folder = self.folder_path_restore or self.entry_restore.get()
        if not folder or folder.strip() == "Select restore folder...":
            self.show_toast("Please select a restore folder first.", success=False)
            return
        if not os.path.isdir(folder):
            self.show_toast("Restore folder does not exist!", success=False)
            return
        # Check if folder name matches date-time pattern (DD-MM-YYYY HH-MM AM/PM)
        folder_name = os.path.basename(folder)
        pattern = r"\d{2}-\d{2}-\d{4} \d{2}-\d{2} (AM|PM)"
        if not re.match(pattern, folder_name):
            self.show_toast("Invalid backup folder name!", success=False)
            return
        # Define destination files and their original locations
        # Restore canonical database (JJCIMS.accdb) only.
        try:
            src_db = os.path.join(folder, "JJCIMS.accdb")
            dest_db = get_db_path()
            if os.path.exists(src_db):
                shutil.copy2(src_db, dest_db)
            else:
                self.show_toast(
                    f"File not found: {os.path.basename(src_db)}", success=False
                )
                return
            # Update last restore time and canvas text
            now = None
            try:
                import datetime

                now = datetime.datetime.now()
            except Exception:
                pass
            if now:
                self.last_restore_time = now.strftime("%d/%m/%Y | %I:%M %p")
                self._save_status()
                if hasattr(self, "restore_canvas") and hasattr(
                    self, "last_restore_text_id"
                ):
                    self.restore_canvas.itemconfig(
                        self.last_restore_text_id,
                        text=f"Last Restore: {self.last_restore_time}",
                    )
            self.show_toast("Restore is Successful!", success=True)
            short_path = os.path.basename(folder)
            self.after(
                1200,
                lambda: self.show_toast(
                    f"Restored from: {short_path}", success=True, duration=1800
                ),
            )
        except Exception as e:
            self.show_toast(f"Restore failed: {e}", success=False)

    def select_backup_folder(self):
        folder = filedialog.askdirectory(title="Select Backup Folder")
        # Refocus settings window after dialog
        self.winfo_toplevel().lift()
        self.winfo_toplevel().focus_force()
        if folder:
            self.folder_path_backup = folder
            self.entry_backup.delete(0, "end")
            self.entry_backup.insert(0, folder)
            self.show_toast("Backup folder selected!", success=True, duration=1500)
        else:
            self.show_toast("No backup folder selected.", success=False, duration=1800)

    def select_restore_folder(self):
        folder = filedialog.askdirectory(title="Select Restore Folder")
        # Refocus settings window after dialog
        self.winfo_toplevel().lift()
        self.winfo_toplevel().focus_force()
        if folder:
            self.folder_path_restore = folder
            self.entry_restore.delete(0, "end")
            self.entry_restore.insert(0, folder)
            self.show_toast("Restore folder selected!", success=True, duration=1500)
        else:
            self.show_toast("No restore folder selected.", success=False, duration=1800)


# Usage Example:
# from backup_restore_frame import BackupRestoreFrame
# frame = BackupRestoreFrame(parent, assets_backup='path/to/bu_assets', assets_restore='path/to/r_assets')
# frame.pack(fill='both', expand=True)
