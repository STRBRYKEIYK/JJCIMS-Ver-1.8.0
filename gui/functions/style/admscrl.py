from tkinter import ttk

def configure_custom_scrollbar():
    """Configure a custom scrollbar style with a centered line and rounded rectangle."""
    style = ttk.Style()
    style.theme_use("default")
    
    # Configure the vertical scrollbar style
    style.configure(
        "Custom.Vertical.TScrollbar",
        gripcount=0,
        background="#000000",  # Black background for the scrollbar
        darkcolor="#000000",
        lightcolor="#000000",
        troughcolor="#f0f0f0",  # Light gray for the trough
        bordercolor="#f0f0f0",  # Match the trough color to remove the frame
        arrowcolor="#000000",  # Black arrows
        relief="flat"  # Flat relief for a clean look
    )
    
    # Map the scrollbar behavior
    style.map(
        "Custom.Vertical.TScrollbar",
        background=[("active", "#000000")],  # Keep black when active
        relief=[("pressed", "flat"), ("!pressed", "flat")]
    )
    
    # Simplify the layout to use the default thumb
    style.layout(
        "Custom.Vertical.TScrollbar",
        [
            ("Vertical.Scrollbar.trough", {
                "children": [
                    ("Vertical.Scrollbar.thumb", {
                        "sticky": "nswe"
                    })
                ],
                "sticky": "ns"
            })
        ]
    )