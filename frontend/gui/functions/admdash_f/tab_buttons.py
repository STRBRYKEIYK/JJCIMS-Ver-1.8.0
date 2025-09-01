import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk
from backend.utils.font_utils import get_bold_font
from backend.database import get_db_path


def execute_access_queries():
    """Execute the Access database queries: Update Status and statssum"""
    try:
        # Get database path
        db_path = get_db_path()

        # Connect using connector pattern that abstracts database type
        from backend.database import get_connector
        connector = get_connector(db_path)
        
        # Execute Update Status query
        print("[DEBUG] Executing 'Update Status' query...")
        connector.execute_query("EXEC [Update Status]")
        print("[DEBUG] 'Update Status' query executed successfully")

        # Execute statssum query
        print("[DEBUG] Executing 'statssum' query...")
        connector.execute_query("EXEC statssum")
        print("[DEBUG] 'statssum' query executed successfully")

    except Exception as e:
        print(f"[ERROR] Failed to execute queries: {e}")
        # Try fallback SQL if queries fail
        try:
            print("[DEBUG] Attempting fallback SQL execution...")
            fallback_sql = """
            UPDATE ITEMSDB
            SET STATUS = IIf(BALANCE > 0 AND BALANCE <= [MIN STOCK], 'Low in Stock', IIf(BALANCE = 0, 'Out of Stock', 'In Stock'))
            WHERE BALANCE IS NOT NULL AND [MIN STOCK] IS NOT NULL;
            """
            connector = get_connector(get_db_path())  # Get a fresh connector
            connector.execute_query(fallback_sql)
            print("[DEBUG] Fallback SQL executed successfully")
        except Exception as fallback_error:
            print(f"[ERROR] Fallback SQL also failed: {fallback_error}")


def create_frame_outline(
    frame_widget, corner_radius=15, outline_color="#800000", outline_width=1
):
    frame_widget.update_idletasks()
    width = frame_widget.winfo_width()
    height = frame_widget.winfo_height()

    if width <= 1 or height <= 1:
        return None
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if outline_color.startswith("#"):
        outline_color = outline_color[1:]  # Remove leading '#'
    rgb_color = tuple(int(outline_color[i : i + 2], 16) for i in (0, 2, 4))
    outline_rgba = rgb_color + (255,)
    draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)],
        radius=corner_radius,
        outline=outline_rgba,
        width=outline_width,
    )
    return ImageTk.PhotoImage(img)


# ...


def create_tab_background_with_text(
    text,
    button_width,
    button_height,
    selected=True,
    is_leftmost=False,
    is_rightmost=False,
):
    """Create tab button with YouTube-like style but with black and orange colors"""
    # Create image with specified dimensions
    img = Image.new("RGBA", (button_width, button_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Modern tab styling - continuous tabs with edge rounding
    corner_radius = 8  # Radius for edges only

    if selected:
        # Selected: Black background with white bottom border
        bg_color = (24, 28, 31, 100)  # Black background
        border_color = (255, 255, 255, 255)  # White border
    else:
        # Unselected: Dark Maroon background, no border
        bg_color = (128, 0, 0, 128)  # Maroon for better contrast
        border_color = (0, 0, 0, 0)

    # Draw background with selective rounding
    if is_leftmost:
        # Left tab - only round left corners
        draw.rounded_rectangle(
            [(0, 0), (button_width - 1, button_height - 1)],
            radius=corner_radius,
            fill=bg_color,
            corners=(True, False, False, True),  # Top-left and bottom-left rounded
        )
    elif is_rightmost:
        # Right tab - only round right corners
        draw.rounded_rectangle(
            [(0, 0), (button_width - 1, button_height - 1)],
            radius=corner_radius,
            fill=bg_color,
            corners=(False, True, True, False),  # Top-right and bottom-right rounded
        )
    else:
        # Middle tabs - no rounding for continuous look
        draw.rectangle([(0, 0), (button_width - 1, button_height - 1)], fill=bg_color)

    # Add bottom border for selected tab (YouTube style)
    if selected and border_color:
        border_height = 3
        draw.rectangle(
            [(0, button_height - border_height), (button_width - 1, button_height - 1)],
            fill=border_color,
        )

    # Load font - larger, bold, and more visible size (PyInstaller compatible)
    font_size = 16  # Increased from 14 to 16 for bigger text
    font = get_bold_font(font_size)

    # If font loading failed, use default font
    if font is None:
        font = ImageFont.load_default()

    # Text color - dark red for both selected and unselected
    text_color = (255, 255, 255, 255)  # White text

    # Get text size and center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Center text horizontally and vertically
    text_x = (button_width - text_width) // 2
    text_y = (button_height - text_height) // 2

    # If text is too wide, try to break it into multiple lines
    if (
        text_width > button_width - 30
    ):  # More generous padding allowance (increased from 20)
        words = text.split()
        if len(words) > 1:
            # Try to split into two lines more intelligently
            if len(words) == 2:
                # For two words, put one on each line
                line1 = words[0]
                line2 = words[1]
            else:
                # For more words, try to balance line lengths
                mid_point = len(words) // 2
                line1 = " ".join(words[:mid_point])
                line2 = " ".join(words[mid_point:])

            # Get dimensions for two lines
            line1_bbox = draw.textbbox((0, 0), line1, font=font)
            line2_bbox = draw.textbbox((0, 0), line2, font=font)
            line1_width = line1_bbox[2] - line1_bbox[0]
            line2_width = line2_bbox[2] - line2_bbox[0]
            line_height = line1_bbox[3] - line1_bbox[1]

            # Center both lines
            line1_x = (button_width - line1_width) // 2
            line2_x = (button_width - line2_width) // 2
            total_text_height = (
                line_height * 2 + 5
            )  # Increased gap between lines for better spacing
            start_y = (button_height - total_text_height) // 2

            # Draw clean text without scanline effect to avoid corruption
            draw.text((line1_x, start_y), line1, font=font, fill=text_color)
            draw.text(
                (line2_x, start_y + line_height + 5), line2, font=font, fill=text_color
            )
        else:
            # Single word too long, try to use a smaller font or truncate
            if text_width > button_width - 10:
                # Try with a smaller font (but still bigger than before)
                smaller_font = get_bold_font(14)  # Get bold font at size 14

                # If smaller font loading failed, use the main font
                if smaller_font is None:
                    smaller_font = font

                smaller_bbox = draw.textbbox((0, 0), text, font=smaller_font)
                smaller_width = smaller_bbox[2] - smaller_bbox[0]
                smaller_height = smaller_bbox[3] - smaller_bbox[1]

                if smaller_width <= button_width - 10:
                    # Use the smaller font - draw directly without scanline effect
                    text_x = (button_width - smaller_width) // 2
                    text_y = (button_height - smaller_height) // 2
                    draw.text(
                        (text_x, text_y), text, font=smaller_font, fill=text_color
                    )
                else:
                    # Still too long, truncate with ellipsis - draw directly
                    truncated_text = text[:12] + "..."
                    draw.text(
                        (text_x, text_y), truncated_text, font=font, fill=text_color
                    )
            else:
                # Single word fits fine - draw directly
                draw.text((text_x, text_y), text, font=font, fill=text_color)
    else:
        # Text fits in one line - draw directly
        draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Return without scanline effect
    return ImageTk.PhotoImage(img)


def create_tab_buttons(dashboard, parent=None):
    """Create tab-like buttons with rounded corners and bigger size."""
    if parent is None:
        parent = dashboard.table_frame

    button_height = 55  # Increased height significantly for multi-line text
    button_width = 200  # Increased width further to accommodate longer text
    num_buttons = 5  # Total number of buttons
    total_button_width = button_width * num_buttons

    # Create a horizontal container for tabs and search bar
    tabs_and_search_frame = tk.Frame(parent, bg="#000000", height=button_height)
    tabs_and_search_frame.pack(
        side=tk.TOP, fill=tk.X
    )  # Removed pady for seamless spacing

    # Create tab frame (left side)
    tab_frame = tk.Frame(
        tabs_and_search_frame,
        bg="#000000",
        height=button_height,
        width=total_button_width,
    )
    tab_frame.pack(side=tk.LEFT, anchor=tk.W)
    tab_frame.pack_propagate(False)  # Prevent frame from resizing to fit contents

    # Store reference to the tabs and search frame for search bar positioning
    dashboard.tabs_and_search_frame = tabs_and_search_frame

    # Button dimensions - larger and uniform

    def update_tab_styles(selected_button):
        # Update each button with appropriate image
        buttons_info = [
            (view_materials_list_button, "Items List", True, False),
            (restock_list_button, "Restock List", False, False),
            (employee_logs_button, "Employee Logs", False, False),
            (admin_logs_button, "Admin Logs", False, True),
        ]
        for button, text, is_leftmost, is_rightmost in buttons_info:
            if button == selected_button:
                button_img = create_tab_background_with_text(
                    text,
                    button_width,
                    button_height,
                    selected=True,
                    is_leftmost=is_leftmost,
                    is_rightmost=is_rightmost,
                )
                button.configure(
                    bg="#000000", image=button_img, text="", activebackground="#000000"
                )
                if button_img:
                    button.image = button_img
            else:
                button_img = create_tab_background_with_text(
                    text,
                    button_width,
                    button_height,
                    selected=False,
                    is_leftmost=is_leftmost,
                    is_rightmost=is_rightmost,
                )
                button.configure(
                    bg="#000000", image=button_img, text="", activebackground="#000000"
                )
                if button_img:
                    button.image = button_img

    # Create initial button images
    materials_img = create_tab_background_with_text(
        "Items List",
        button_width,
        button_height,
        selected=True,
        is_leftmost=True,
        is_rightmost=False,
    )
    restock_img = create_tab_background_with_text(
        "Restock List",
        button_width,
        button_height,
        selected=False,
        is_leftmost=False,
        is_rightmost=False,
    )
    employee_logs_img = create_tab_background_with_text(
        "Employee Logs",
        button_width,
        button_height,
        selected=False,
        is_leftmost=False,
        is_rightmost=False,
    )
    admin_logs_img = create_tab_background_with_text(
        "Admin Logs",
        button_width,
        button_height,
        selected=False,
        is_leftmost=False,
        is_rightmost=True,
    )

    # Create buttons with larger size and no flashing - black backgrounds to match frame
    view_materials_list_button = tk.Button(
        tab_frame,
        image=materials_img,
        bg="#000000",
        width=button_width,
        height=button_height,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        activebackground="#000000",
        activeforeground="#000000",
        disabledforeground="#000000",
        command=lambda: [
            dashboard.view_items()
            if getattr(dashboard, "current_view", None) != "ITEMS_LIST"
            else None,
            dashboard.set_current_view("ITEMS_LIST"),
            update_tab_styles(view_materials_list_button),
            dashboard.show_main_buttons(),
            dashboard.show_export_buttons(),  # Always update export button visibility when switching tabs
            __import__(
                "gui.functions.admdash_f.ML.search_bar",
                fromlist=["update_search_bar_visibility"],
            ).update_search_bar_visibility(dashboard),
        ],
    )
    view_materials_list_button.image = materials_img
    view_materials_list_button.pack(side=tk.LEFT)

    restock_list_button = tk.Button(
        tab_frame,
        image=restock_img,
        bg="#000000",
        width=button_width,
        height=button_height,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        activebackground="#000000",  # Prevent color change on click
        activeforeground="#000000",  # Prevent color change on click
        disabledforeground="#000000",  # Prevent color change when disabled
        command=lambda: [
            dashboard.view_restock_list()
            if getattr(dashboard, "current_view", None) != "Restock List"
            else None,
            update_tab_styles(restock_list_button),
            dashboard.show_export_buttons(),  # Always update export button visibility when switching tabs
            __import__(
                "gui.functions.admdash_f.ML.search_bar",
                fromlist=["update_search_bar_visibility"],
            ).update_search_bar_visibility(dashboard),
        ],
    )
    restock_list_button.image = restock_img
    restock_list_button.pack(side=tk.LEFT)  # No fill for continuous look

    employee_logs_button = tk.Button(
        tab_frame,
        image=employee_logs_img,
        bg="#000000",
        width=button_width,
        height=button_height,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        activebackground="#000000",  # Prevent color change on click
        activeforeground="#000000",  # Prevent color change on click
        disabledforeground="#000000",  # Prevent color change when disabled
        command=lambda: [
            dashboard.view_logs(),
            dashboard.set_current_view("Employee Logs"),
            update_tab_styles(employee_logs_button),
            dashboard.hide_main_buttons(),
            dashboard.show_export_buttons(),
            # dashboard.hide_export_buttons(),  # Removed: no longer exists; export button visibility is managed by show_export_buttons only
            __import__(
                "gui.functions.admdash_f.ML.search_bar",
                fromlist=["update_search_bar_visibility"],
            ).update_search_bar_visibility(dashboard),
        ],
    )
    employee_logs_button.image = employee_logs_img
    employee_logs_button.pack(side=tk.LEFT)  # No fill for continuous look

    admin_logs_button = tk.Button(
        tab_frame,
        image=admin_logs_img,
        bg="#000000",
        width=button_width,
        height=button_height,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        activebackground="#000000",  # Prevent color change on click
        activeforeground="#000000",  # Prevent color change on click
        disabledforeground="#000000",  # Prevent color change when disabled
        command=lambda: [
            dashboard.view_admin_logs(),
            dashboard.set_current_view("Admin Logs"),
            update_tab_styles(admin_logs_button),
            dashboard.hide_main_buttons(),
            dashboard.show_export_buttons(),
            __import__(
                "gui.functions.admdash_f.ML.search_bar",
                fromlist=["update_search_bar_visibility"],
            ).update_search_bar_visibility(dashboard),
        ],
    )
    admin_logs_button.image = admin_logs_img
    admin_logs_button.pack(side=tk.LEFT)  # No fill for continuous look

    # Set initial tab style
    update_tab_styles(view_materials_list_button)
