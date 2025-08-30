import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk

class CheckboxTreeview(ttk.Treeview):
    def __init__(self, master=None, **kw):
        # Force show both tree and headings so #0 column is visible for the image
        kw['show'] = 'tree headings'
        super().__init__(master, **kw)
        # Load and resize icons to 16x16
        selected_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "selected.png"
        deselected_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "deselected.png"
        self.selected_icon = ImageTk.PhotoImage(Image.open(selected_path).resize((25, 25), Image.LANCZOS))
        self.deselected_icon = ImageTk.PhotoImage(Image.open(deselected_path).resize((25, 25), Image.LANCZOS))
        self._checked_items = set()
        self._image_refs = {}  # Prevent garbage collection
        self._is_destroyed = False  # Track if widget has been destroyed
        self.bind("<Button-1>", self._on_click)
        self.bind("<Destroy>", self._on_destroy)  # Bind to destruction event
        self._setup_checkbox_column()
        
    def _on_destroy(self, event=None):
        """Handle widget destruction properly"""
        if event and event.widget == self:
            self._is_destroyed = True
            # Clear references that might cause callbacks to occur
            self.unbind_all("<Button-1>")
            self._checked_items.clear()
            self._image_refs.clear()

    def _setup_checkbox_column(self):
        # The #0 column is always present in treeview, so just set its width and heading
        self.heading("#0", text="", anchor="center")
        self.column("#0", width=50, anchor="center", stretch=False)

    def insert(self, parent, index, iid=None, **kw):
        if self._is_destroyed:
            return None
            
        try:
            values = kw.get("values", ())
            checked = False
            # If image is explicitly set to '', do not show checkbox
            if "image" in kw and kw["image"] == "":
                icon = None
                kw.pop("image")
            else:
                if "checked" in kw:
                    checked = kw.pop("checked")
                icon = self.selected_icon if checked else self.deselected_icon
            # Store image reference to prevent garbage collection
            if iid is None:
                iid = f"item_{id(values)}_{len(self._image_refs)}"
            if icon:
                self._image_refs[iid] = icon
                kw["image"] = icon  # This will display in the #0 column
            kw["text"] = ""    # No text in the #0 column
            kw["values"] = tuple(values)
            item_id = super().insert(parent, index, iid=iid, **kw)
            if checked and icon:
                self._checked_items.add(item_id)
            return item_id
        except tk.TclError:
            # Widget might have been destroyed during operation
            self._is_destroyed = True
            return None

    def _on_click(self, event):
        if self._is_destroyed:
            return 'break'
            
        try:
            region = self.identify("region", event.x, event.y)
            if region == "tree":
                row_id = self.identify_row(event.y)
                if row_id:
                    self.toggle_checkbox(row_id)
                    return 'break'
        except tk.TclError:
            # Widget might have been destroyed during click event
            self._is_destroyed = True
            return 'break'

    def toggle_checkbox(self, item):
        if self._is_destroyed:
            return
            
        try:
            if item in self._checked_items:
                self._checked_items.remove(item)
                self._image_refs[item] = self.deselected_icon
                self.item(item, image=self.deselected_icon)
            else:
                self._checked_items.add(item)
                self._image_refs[item] = self.selected_icon
                self.item(item, image=self.selected_icon)
            self.event_generate("<<CheckboxToggled>>", data=item)
        except tk.TclError:
            # Widget might have been destroyed during operation
            self._is_destroyed = True

    def is_checked(self, item):
        if self._is_destroyed:
            return False
        return item in self._checked_items

    def set_checked(self, item, checked=True):
        """Set the checked state of an item."""
        if self._is_destroyed:
            return
            
        try:
            if checked and item not in self._checked_items:
                self._checked_items.add(item)
                self._image_refs[item] = self.selected_icon
                self.item(item, image=self.selected_icon)
            elif not checked and item in self._checked_items:
                self._checked_items.remove(item)
                self._image_refs[item] = self.deselected_icon
                self.item(item, image=self.deselected_icon)
        except tk.TclError:
            # Widget might have been destroyed during operation
            self._is_destroyed = True

    def clear_checked_items(self):
        """Clear all checked items when table is refreshed."""
        if self._is_destroyed:
            return
            
        if hasattr(self, '_checked_items'):
            self._checked_items.clear()

    def get_checked(self):
        if self._is_destroyed:
            return []
            
        try:
            # Filter out items that no longer exist
            existing_items = set(self.get_children())
            self._checked_items = self._checked_items.intersection(existing_items)
            return list(self._checked_items)
        except tk.TclError:
            self._is_destroyed = True
            return []
            
    # Override original methods to handle widget destruction gracefully
    def yview(self, *args):
        if self._is_destroyed:
            return
        try:
            return super().yview(*args)
        except tk.TclError:
            self._is_destroyed = True
            return None
            
    def xview(self, *args):
        if self._is_destroyed:
            return
        try:
            return super().xview(*args)
        except tk.TclError:
            self._is_destroyed = True
            return None
