import tkinter as tk
import webbrowser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os

# No scanline import needed
# Sound imports removed
from backend.utils.notification_manager import init_notifications, show_notification


def create_text_with_glow(text, font_size, is_bold=False):
    # Create a temporary image with black background
    padding = 20
    img = Image.new("RGBA", (1000, font_size + padding * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Regular Segoe UI
        if is_bold:
            font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"  # Bold Segoe UI
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        # Fallback to default
        font = ImageFont.load_default()

    # Get text size and position it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create new image with exact text size
    img = Image.new(
        "RGBA", (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0)
    )
    draw = ImageDraw.Draw(img)

    # Draw orange text with glow
    glow_color = (255, 111, 0, 100)  # Orange with alpha
    for offset in range(3):  # Glow effect
        draw.text((padding + offset, padding), text, font=font, fill=glow_color)
        draw.text((padding - offset, padding), text, font=font, fill=glow_color)
        draw.text((padding, padding + offset), text, font=font, fill=glow_color)
        draw.text((padding, padding - offset), text, font=font, fill=glow_color)

    # Main text
    draw.text(
        (padding, padding), text, font=font, fill=(255, 111, 0, 255)
    )  # Solid orange

    # Return without scanline effect
    return ImageTk.PhotoImage(img)


def create_about_section(parent, root_window=None):
    # Initialize notification system if root window is provided
    if root_window:
        try:
            init_notifications(root_window)
        except Exception as e:
            print(f"Failed to initialize notifications: {e}")

    # Easter egg callback functions
    def easter_egg_1_callback():
        """Called after info_1.wav finishes playing"""
        try:
            # Add delay before showing notification and playing second sound
            def delayed_notification_1():
                title = "Unrewarded Curiosity"
                body = """Log ID: 0027-EG-VT-NIL
Subject engaged in nonessential exploration and uncovered 
a concealed element. No reward dispensed. 
No acknowledgment necessary. 
Curiosity is not a substitute for value."""
                show_notification(title, body, duration=8000)
                # Sound removed
                # No sound for easter egg 1

            # Schedule notification and sound after 1 second delay
            parent.after(1000, delayed_notification_1)
        except Exception as e:
            print(f"Error in easter egg 1 callback: {e}")

    def easter_egg_2_callback():
        """Called after info_2.wav finishes playing"""
        try:
            # Add delay before showing notification and playing second sound
            def delayed_notification_2():
                title = "Unrewarded Curiosity #2"
                body = """Log ID: #EG-045-NOTED
Subject exhibited excessive exploratory behavior 
and located a non-essential embedded object.
No scientific data gained. No protocol breached. No reward issued."""
                show_notification(title, body, duration=8000)
                # Sound removed
                # No sound for easter egg 2

            # Schedule notification and sound after 1.5 second delay
            parent.after(1500, delayed_notification_2)
        except Exception as e:
            print(f"Error in easter egg 2 callback: {e}")

    # Page management
    current_page = tk.IntVar(value=1)
    total_pages = 2

    def show_page(page_num):
        current_page.set(page_num)
        # Hide all page frames
        page1_frame.pack_forget()
        page2_frame.pack_forget()

        # Show selected page
        if page_num == 1:
            page1_frame.pack(expand=True, fill="both", padx=50, pady=(30, 0))
        else:
            page2_frame.pack(expand=True, fill="both", padx=50, pady=(30, 0))

    def next_page():
        if current_page.get() < total_pages:
            show_page(current_page.get() + 1)

    def prev_page():
        if current_page.get() > 1:
            show_page(current_page.get() - 1)

    frame = tk.Frame(parent, bg="#000000")

    # Create page frames
    page1_frame = tk.Frame(frame, bg="#000000")
    page2_frame = tk.Frame(frame, bg="#000000")

    # Navigation buttons frame
    nav_frame = tk.Frame(frame, bg="#000000")
    nav_frame.pack(side="bottom", pady=20)

    prev_btn = tk.Button(
        nav_frame,
        text="<",
        command=prev_page,
        bg="#000000",
        fg="#fffde7",
        font=("Segoe UI", 12),
        width=3,
        relief="flat",
        borderwidth=0,
    )
    prev_btn.pack(side="left", padx=5)

    page_label = tk.Label(
        nav_frame,
        textvariable=current_page,
        bg="#000000",
        fg="#fffde7",
        font=("Segoe UI", 12),
    )
    page_label.pack(side="left", padx=10)

    next_btn = tk.Button(
        nav_frame,
        text=">",
        command=next_page,
        bg="#000000",
        fg="#fffde7",
        font=("Segoe UI", 12),
        width=3,
        relief="flat",
        borderwidth=0,
    )
    next_btn.pack(side="left", padx=5)

    # Page 1 content
    content_frame = tk.Frame(page1_frame, bg="#000000")
    content_frame.pack(expand=True)

    # Add the JJCIMS logo at the top
    try:
        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../assets/JJCIMS.png")
        )
        logo_img = Image.open(logo_path)
        # Increased logo size
        logo_width = 300  # Increased from 200 to 300
        aspect_ratio = logo_img.height / logo_img.width
        logo_height = int(logo_width * aspect_ratio)
        logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # Use logo without scanline effect
        logo_photo = ImageTk.PhotoImage(logo_img)

        logo_label = tk.Label(content_frame, image=logo_photo, bg="#000000")
        logo_label.image = logo_photo  # Keep a reference
        logo_label.pack(pady=(20, 30))  # Increased padding
    except Exception as e:
        print(f"Error loading logo: {e}")

    # Main title with scanline effect
    title_img = create_text_with_glow("JJC Inventory Management System", 32, True)
    title = tk.Label(content_frame, image=title_img, bg="#000000")
    title.image = title_img  # Keep a reference
    title.pack(pady=(0, 5))

    # Subtitle with scanline effect
    subtitle_img = create_text_with_glow("(JJCIMS)", 28, True)
    subtitle = tk.Label(content_frame, image=subtitle_img, bg="#000000")
    subtitle.image = subtitle_img  # Keep a reference
    subtitle.pack(pady=(0, 20))

    version = tk.Label(
        content_frame,
        text="Version: VER 1.6.0",
        font=("Segoe UI", 16),  # Increased from 12 to 16
        bg="#000000",
        fg="#fffde7",
    )
    version.pack(pady=5)

    company = tk.Label(
        content_frame,
        text="Made for the Company: JJC Engineering Works and General Services",
        font=("Segoe UI", 16),  # Increased from 12 to 16
        bg="#000000",
        fg="#fffde7",
    )
    company.pack(pady=5)

    # Developer info frame
    dev_frame = tk.Frame(content_frame, bg="#000000")
    dev_frame.pack(pady=(10, 2))

    tk.Label(
        dev_frame,
        text="Developed and Designed by: ",
        font=("Segoe UI", 16),  # Increased from 12 to 16
        bg="#000000",
        fg="#fffde7",
    ).pack(side=tk.LEFT)

    # Clickable developer name with link
    dev_link = tk.Label(
        dev_frame,
        text="Keith Wilhelm Felipe",
        font=("Segoe UI", 16, "underline"),  # Increased from 12 to 16
        bg="#000000",
        fg="#00bfff",
        cursor="hand2",
    )
    dev_link.pack(side=tk.LEFT)
    dev_link.bind(
        "<Button-1>", lambda e: webbrowser.open("https://www.instagram.com/just.kwf/")
    )

    # Aliases and contact
    contact_frame = tk.Frame(content_frame, bg="#000000")
    contact_frame.pack(pady=2)

    # Aliases with email
    aliases = tk.Label(
        contact_frame,
        text="Openwilheilmer | KWF",
        font=("Segoe UI", 12),
        bg="#000000",
        fg="#fffde7",
    )
    aliases.pack(side=tk.LEFT)

    tk.Label(
        contact_frame,
        text=" | Email: ",
        font=("Segoe UI", 12),
        bg="#000000",
        fg="#fffde7",
    ).pack(side=tk.LEFT)

    email_link = tk.Label(
        contact_frame,
        text="Keidesu02@gmail.com",
        font=("Segoe UI", 12, "underline"),
        bg="#000000",
        fg="#00bfff",
        cursor="hand2",
    )
    email_link.pack(side=tk.LEFT)
    email_link.bind(
        "<Button-1>",
        lambda e: webbrowser.open(
            "https://mail.google.com/mail/u/0/?fs=1&to=Keidesu02@gmail.com&su=Reaching%20Out%20from%20JJC%20FPIS&body=Hello%20there!%0A%0AI%20am%20reaching%20out%20regarding%20our%20JJC%20FPIS%20project.%20Let%20me%20know%20when%20you're%20available%20to%20discuss.%0A%0AThank%20you!&tf=cm"
        ),
    )

    # Hidden Easter egg - Replace © with tiny Lambda logo in copyright
    try:
        # Copyright frame to hold text and lambda logo
        copyright_frame = tk.Frame(content_frame, bg="#000000")
        copyright_frame.pack(pady=(30, 5))

        # Load tiny Lambda logo to replace © symbol
        lambda_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../assets/Lambda_logo.png")
        )
        lambda_img = Image.open(lambda_path)
        # Make it tiny to match copyright symbol size
        lambda_size = 10  # Very small to look like a copyright symbol
        lambda_img = lambda_img.resize(
            (lambda_size, lambda_size), Image.Resampling.LANCZOS
        )

        # Use logo without scanline effect
        lambda_photo = ImageTk.PhotoImage(lambda_img)

        # Lambda logo replacing the © symbol (clickable easter egg)
        lambda_copyright = tk.Label(
            copyright_frame, image=lambda_photo, bg="#000000", cursor="hand2"
        )
        lambda_copyright.image = lambda_photo  # Keep a reference
        lambda_copyright.pack(side="left")
        lambda_copyright.bind("<Button-1>", lambda e: easter_egg_1_callback())

        # Rest of copyright text
        copyright_text = tk.Label(
            copyright_frame,
            text=" 2025 JJC Engineering Works and General Services | KWF | Openwilheilmer",
            font=("Segoe UI", 10, "italic"),
            bg="#000000",
            fg="#555555",
        )
        copyright_text.pack(side="left")

    except Exception as e:
        print(f"Error creating hidden lambda easter egg: {e}")

    # Page 2 content
    content_frame2 = tk.Frame(page2_frame, bg="#000000")
    content_frame2.pack(expand=True)

    desc_title_img = create_text_with_glow("About the System", 32, True)
    desc_title = tk.Label(content_frame2, image=desc_title_img, bg="#000000")
    desc_title.image = desc_title_img  # Keep a reference
    desc_title.pack(pady=(0, 20))

    description = (
        "JJCIMS (JJC Inventory Management System) is a comprehensive platform designed for "
        "JJC Engineering Works and General Services to efficiently track, manage, and secure all inventory, "
        "parts, and fabrication processes with robust multi-user access."
    )
    desc_label = tk.Label(
        content_frame2,
        text=description,
        font=("Segoe UI", 16),  # Increased from 12 to 16
        bg="#000000",
        fg="#fffde7",
        wraplength=600,
        justify="center",
    )  # Increased wraplength
    desc_label.pack(pady=(0, 30))

    features_title_img = create_text_with_glow("Key Features", 28, True)
    features_title = tk.Label(content_frame2, image=features_title_img, bg="#000000")
    features_title.image = features_title_img  # Keep a reference
    features_title.pack(pady=(0, 10))

    features = [
        "• Secure admin and employee access levels",
        "• Inventory tracking",
        "• Fabrication process management",
        "• Parts and materials management",
        "• Two-factor authentication",
        "• Audit logging",
        "• Import/Export capabilities",
    ]

    # Display features with hidden lambda logo as bullet point
    try:
        # Load tiny lambda logo for bullet replacement
        lambda_bullet_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../assets/Lambda_logo.png")
        )
        lambda_bullet_img = Image.open(lambda_bullet_path)
        # Make it tiny to match bullet point size
        lambda_bullet_size = 8  # Small enough to look like a bullet
        lambda_bullet_img = lambda_bullet_img.resize(
            (lambda_bullet_size, lambda_bullet_size), Image.Resampling.LANCZOS
        )

        # Use logo without scanline effect
        lambda_bullet_photo = ImageTk.PhotoImage(lambda_bullet_img)

        for i, feature in enumerate(features):
            if i == 5:  # Replace bullet for "Audit logging" with lambda
                # Create frame for this feature line
                feature_frame = tk.Frame(content_frame2, bg="#000000")
                feature_frame.pack(pady=2)

                # Lambda logo as bullet (clickable easter egg)
                lambda_bullet = tk.Label(
                    feature_frame,
                    image=lambda_bullet_photo,
                    bg="#000000",
                    cursor="hand2",
                )
                lambda_bullet.image = lambda_bullet_photo  # Keep a reference
                lambda_bullet.pack(side="left", padx=(0, 5))
                lambda_bullet.bind("<Button-1>", lambda e: easter_egg_2_callback())

                # Feature text without bullet
                feature_text = tk.Label(
                    feature_frame,
                    text=feature[2:],
                    font=("Segoe UI", 12),  # Remove "• " from start
                    bg="#000000",
                    fg="#fffde7",
                )
                feature_text.pack(side="left")
            else:
                # Normal feature display
                feature_label = tk.Label(
                    content_frame2,
                    text=feature,
                    font=("Segoe UI", 12),
                    bg="#000000",
                    fg="#fffde7",
                )
                feature_label.pack(pady=2)
    except Exception as e:
        print(f"Error creating lambda bullet easter egg: {e}")
        # Fallback to normal features if lambda loading fails
        for feature in features:
            feature_label = tk.Label(
                content_frame2,
                text=feature,
                font=("Segoe UI", 12),
                bg="#000000",
                fg="#fffde7",
            )
            feature_label.pack(pady=2)

    # Show initial page
    show_page(1)

    return frame
