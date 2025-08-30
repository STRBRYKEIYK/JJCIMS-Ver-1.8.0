import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont, ImageFilter
import os
import sys
import threading
import time
import math
from backend.utils.image_effects import create_scanline_effect
from backend.utils.window_icon import set_window_icon
# Sound imports removed


class LoadingScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JJCFPIS")
        self.root.configure(bg="#000000")  # Pure black background
        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)  # Remove window decorations

        # Set window icon
        set_window_icon(self.root)

        # Center the window
        self.center_window()

        # Animation variables
        self.rotation_angle = 0
        self.animation_running = True
        self.current_logo = "windows"  # "windows" or "jjcfpis"
        self.logo_timer = 0
        self.fade_alpha = 255  # Start fully visible
        self.fade_direction = 1
        self.transition_phase = "showing"  # "showing", "fading_out", "fading_in"

        # Enhanced animation variables
        self.pulse_intensity = 0
        self.glow_radius = 0
        self.particle_positions = []
        self.progress_value = 0

        # Preloading variables
        self.preload_complete = False
        self.preload_progress = 0
        self.preload_status = "Initializing..."

        # Store after job IDs for cleanup
        self.after_jobs = []
        self.window_destroyed = False

        # Load and prepare images
        self.load_images()

        # Create UI elements
        self.create_ui()

        # Initialize logo displays
        self.initialize_logo_displays()

        # Start preloading in background
        self.start_preloading()

        # Start animations
        self.start_animations()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")

    def load_images(self):
        """Load and prepare all images"""
        try:
            from backend.utils.image_manager import ImageManager

            # Load Windows logo (winLogo.png) - bigger size
            win_logo_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "winLogo.png")
            )
            self.win_logo_original = Image.open(win_logo_path).convert("RGBA")
            self.win_logo_original = self.win_logo_original.resize(
                (500, 500), Image.Resampling.LANCZOS
            )

            # Load JJCFPIS logo - bigger size
            jjc_logo_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "JJCFPIS.png")
            )
            self.jjc_logo_original = Image.open(jjc_logo_path).convert("RGBA")
            self.jjc_logo_original = self.jjc_logo_original.resize(
                (600, 600), Image.Resampling.LANCZOS
            )

            # Store references in ImageManager
            self.image_manager = ImageManager()
            self.image_manager.load_image(win_logo_path, (500, 500))
            self.image_manager.load_image(jjc_logo_path, (600, 600))

        except Exception as e:
            print(f"Error loading images: {e}")
            # Create placeholder images if files not found - bigger sizes
            self.win_logo_original = Image.new("RGBA", (500, 500), (255, 111, 0, 255))
            self.jjc_logo_original = Image.new("RGBA", (600, 600), (255, 111, 0, 255))

    def create_loading_circle(self, size=160):
        """Create a stylized circular loading indicator with scanline interlacing"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        center = size // 2
        circle_width = 8
        radius = size // 2 - circle_width - 10

        # Create background circle
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            outline=(40, 40, 40, 120),
            width=2,
        )

        # Calculate progress arc based on loading progress
        progress_degrees = int((self.preload_progress / 100) * 360)

        # Draw progress arc
        if progress_degrees > 0:
            # Create a mask for the progress arc
            mask = Image.new("L", (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)

            # Draw the progress arc
            start_angle = -90  # Start from top
            end_angle = start_angle + progress_degrees

            # Draw filled arc
            mask_draw.pieslice(
                [center - radius, center - radius, center + radius, center + radius],
                start_angle,
                end_angle,
                fill=255,
            )

            # Create progress ring
            progress_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            progress_draw = ImageDraw.Draw(progress_img)

            # Outer glow for progress
            for i in range(5):
                alpha = max(0, 80 - i * 15)
                progress_draw.ellipse(
                    [
                        center - radius - i - 2,
                        center - radius - i - 2,
                        center + radius + i + 2,
                        center + radius + i + 2,
                    ],
                    outline=(255, 111, 0, alpha),
                    width=1,
                )

            # Main progress ring
            progress_draw.ellipse(
                [center - radius, center - radius, center + radius, center + radius],
                outline=(255, 111, 0, 255),
                width=circle_width,
            )

            # Inner progress ring
            inner_radius = radius - 12
            progress_draw.ellipse(
                [
                    center - inner_radius,
                    center - inner_radius,
                    center + inner_radius,
                    center + inner_radius,
                ],
                outline=(255, 150, 0, 180),
                width=3,
            )

            # Apply mask to show only progress portion
            progress_img.putalpha(mask)
            img.paste(progress_img, (0, 0), progress_img)

        # Apply scanline interlacing effect
        scanlined_circle = self.create_scanline_interlacing(
            img, num_lines=35, line_opacity=0.25
        )
        return scanlined_circle

    def create_scanline_interlacing(self, image, num_lines=35, line_opacity=0.25):
        """Create scanline interlacing effect on an image"""
        width, height = image.size
        scanline_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(scanline_img)

        # Calculate spacing for scanlines
        line_spacing = height // num_lines

        # Draw scanlines
        for i in range(0, height, line_spacing):
            alpha = int(255 * line_opacity)
            draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha), width=1)

        # Blend scanlines with original image
        result = Image.alpha_composite(image, scanline_img)
        return result

    def create_animated_text(self, text, font_size, y_offset=0):
        """Create clean, minimalist text with subtle glow - Black Mesa style"""
        # Create text image
        padding = 20
        temp_img = Image.new("RGBA", (1000, font_size + padding * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp_img)

        try:
            # Try platform-specific font paths
            import platform

            if platform.system() == "Windows":
                font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"  # Bold Segoe UI
            elif platform.system() == "Darwin":  # macOS
                font_path = (
                    "/System/Library/Fonts/SF-Pro-Display-Bold.otf"  # SF Pro Bold
                )
            else:  # Linux and others
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # DejaVu Sans Bold
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        # Get text size
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Create final image
        img = Image.new(
            "RGBA", (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0)
        )
        draw = ImageDraw.Draw(img)

        # Simple, clean glow effect - Black Mesa style
        glow_color = (255, 111, 0, 80)
        for offset in range(2):
            draw.text((padding + offset, padding), text, font=font, fill=glow_color)
            draw.text((padding - offset, padding), text, font=font, fill=glow_color)
            draw.text((padding, padding + offset), text, font=font, fill=glow_color)
            draw.text((padding, padding - offset), text, font=font, fill=glow_color)

        # Main text - clean and crisp
        draw.text((padding, padding), text, font=font, fill=(255, 111, 0, 255))

        # Minimal scanline effect for that retro feel
        img = create_scanline_effect(
            img, num_lines=20, line_opacity=0.1, glow_amount=1.2
        )

        return img  # Return PIL Image, not PhotoImage

    def create_ui(self):
        """Create the clean, minimalist loading screen UI - Black Mesa style"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg="#000000")
        self.main_frame.pack(expand=True, fill="both")

        # Center container for logo
        self.center_frame = tk.Frame(self.main_frame, bg="#000000")
        self.center_frame.place(relx=0.5, rely=0.4, anchor="center")

        # Single logo label (will switch between Windows and JJCFPIS)
        self.logo_label = tk.Label(self.center_frame, bg="#000000")
        self.logo_label.pack()

        # Loading circle container (below logo)
        circle_frame = tk.Frame(self.main_frame, bg="#000000")
        circle_frame.place(relx=0.5, rely=0.65, anchor="center")

        # Loading circle
        self.circle_label = tk.Label(circle_frame, bg="#000000")
        self.circle_label.pack()

        # Status text (bigger, clean)
        status_img = self.create_animated_text("Initializing...", 24)
        status_photo = ImageTk.PhotoImage(status_img)
        self.status_label = tk.Label(self.main_frame, image=status_photo, bg="#000000")
        self.status_label.image = status_photo
        self.status_label.place(relx=0.5, rely=0.75, anchor="center")

        # Copyright notice at bottom - bigger and clean
        copyright_img = self.create_animated_text(
            "© 2025 JJC Engineering Works and General Services | Made by KWF", 18
        )
        copyright_photo = ImageTk.PhotoImage(copyright_img)
        self.copyright_label = tk.Label(
            self.main_frame, image=copyright_photo, bg="#000000"
        )
        self.copyright_label.image = copyright_photo
        self.copyright_label.pack(side="bottom", pady=30)

    def initialize_logo_displays(self):
        """Initialize the logo displays with Windows logo first"""
        try:
            # Start with Windows logo
            self.current_logo_photo = ImageTk.PhotoImage(self.win_logo_original)
            self.logo_label.configure(image=self.current_logo_photo)

            # Initialize loading circle with bigger size
            circle_img = self.create_loading_circle(150)
            self.circle_photo = ImageTk.PhotoImage(circle_img)
            self.circle_label.configure(image=self.circle_photo)

        except Exception as e:
            print(f"Error initializing logo displays: {e}")

    def animate_logo_sequence(self):
        """Animate the logo sequence with proper fade in/out transitions (0.7s each)"""
        if not self.animation_running or self.window_destroyed:
            return

        self.logo_timer += 1

        # Timing at 60fps: 0-120 frames (2s showing Windows), 120-162 frames (0.7s fade out),
        # 162-204 frames (0.7s fade in JJCFPIS), 204-324 frames (2s showing JJCFPIS)

        if self.logo_timer == 120:  # Start fading out Windows logo after 2 seconds
            self.transition_phase = "fading_out"
            self.fade_direction = -1

        elif self.logo_timer == 162:  # Switch to JJCFPIS logo and start fading in
            self.current_logo = "jjcfpis"
            self.transition_phase = "fading_in"
            self.fade_alpha = 0  # Start invisible
            self.fade_direction = 1

        elif self.logo_timer == 204:  # Finished fading in, now showing
            self.transition_phase = "showing"

        # Handle fade transitions (0.7 seconds = 42 frames at 60fps)
        if self.transition_phase == "fading_out":
            self.fade_alpha -= 6  # Fade out speed (255/42 ≈ 6)
            if self.fade_alpha < 0:
                self.fade_alpha = 0
        elif self.transition_phase == "fading_in":
            self.fade_alpha += 6  # Fade in speed (255/42 ≈ 6)
            if self.fade_alpha > 255:
                self.fade_alpha = 255
        elif self.transition_phase == "showing":
            # Enhanced gentle brightness pulse while showing
            pulse_speed = 0.1
            self.fade_alpha = 220 + int(35 * math.sin(self.logo_timer * pulse_speed))

        # Apply fade to current logo with clean, elegant effects
        try:
            if self.current_logo == "windows":
                # Simple brightness adjustment
                enhancer = ImageEnhance.Brightness(self.win_logo_original)
                faded_logo = enhancer.enhance(self.fade_alpha / 255.0)

                self.current_logo_photo = ImageTk.PhotoImage(faded_logo)
            else:  # jjcfpis
                # Simple brightness adjustment
                enhancer = ImageEnhance.Brightness(self.jjc_logo_original)
                faded_logo = enhancer.enhance(self.fade_alpha / 255.0)

                # Add minimal scanline effect to JJCFPIS logo for that retro feel
                scanlined_logo = create_scanline_effect(
                    faded_logo, num_lines=40, line_opacity=0.12, glow_amount=1.2
                )

                self.current_logo_photo = ImageTk.PhotoImage(scanlined_logo)

            self.logo_label.configure(image=self.current_logo_photo)
        except Exception as e:
            print(f"Logo animation error: {e}")

        # Continue animation
        if self.animation_running and not self.window_destroyed:
            job_id = self.root.after(
                33, self.animate_logo_sequence
            )  # ~30fps for better performance
            self.after_jobs.append(job_id)

    def animate_loading_circle(self):
        """Animate the loading circle with smooth rotation at ~20fps"""
        if not self.animation_running or self.window_destroyed:
            return

        # Smooth rotation at approximately 20fps (50ms intervals)
        self.rotation_angle += 2  # Slower, smoother rotation (2 degrees per frame)
        if self.rotation_angle >= 360:
            self.rotation_angle = 0

        # Update pulse intensity for subtle effects
        self.pulse_intensity += 1

        try:
            # Create clean loading circle
            circle_img = self.create_loading_circle(150)

            # Apply smooth rotation
            rotated_circle = circle_img.rotate(
                -self.rotation_angle, resample=Image.Resampling.BILINEAR
            )

            self.circle_photo = ImageTk.PhotoImage(rotated_circle)
            self.circle_label.configure(image=self.circle_photo)

        except Exception as e:
            print(f"Circle animation error: {e}")

        # Continue animation at 20fps for smooth rotation (50ms intervals)
        if self.animation_running and not self.window_destroyed:
            job_id = self.root.after(50, self.animate_loading_circle)
            self.after_jobs.append(job_id)

    def update_progress_display(self):
        """Update status text - minimal and clean"""
        if not self.animation_running or self.window_destroyed:
            return

        try:
            # Update status text with bigger, clean font
            status_img = self.create_animated_text(self.preload_status, 24)
            status_photo = ImageTk.PhotoImage(status_img)
            self.status_label.configure(image=status_photo)
            self.status_label.image = status_photo

        except Exception as e:
            print(f"Progress update error: {e}")

        # Continue updating
        if self.animation_running and not self.window_destroyed:
            job_id = self.root.after(
                200, self.update_progress_display
            )  # Update every 200ms for smooth feel
            self.after_jobs.append(job_id)

    def start_animations(self):
        """Start all animations"""
        self.animate_logo_sequence()
        self.animate_loading_circle()
        self.update_progress_display()

    def stop_animations(self):
        """Stop all animations"""
        try:
            self.animation_running = False
            # Cancel all scheduled after jobs
            for job_id in self.after_jobs:
                try:
                    if hasattr(self, "root") and self.root and self.root.winfo_exists():
                        self.root.after_cancel(job_id)
                except Exception:
                    pass  # Job may have already completed
            self.after_jobs.clear()
        except Exception as e:
            print(f"Error stopping animations: {e}")

    def close(self):
        """Close the loading screen"""
        try:
            if not self.window_destroyed:
                self.window_destroyed = True
                self.stop_animations()

                # Ensure root window still exists before destroying
                if hasattr(self, "root") and self.root:
                    try:
                        if self.root.winfo_exists():
                            self.root.quit()  # Stop mainloop
                            self.root.destroy()
                    except Exception as e:
                        print(f"Error destroying loading screen: {e}")
        except Exception as e:
            print(f"Error in loading screen close: {e}")
            # Force cleanup
            try:
                if hasattr(self, "root") and self.root:
                    self.root.destroy()
            except:
                pass

    def show_for_duration(self, duration=12000):
        """Show loading screen for specified duration (in milliseconds) - 12.5 seconds total"""

        def close_after_delay():
            # Wait for preloading to complete or timeout
            max_wait_time = duration / 1000
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                if self.preload_complete:
                    break
                time.sleep(0.1)

            # Ensure minimum display time for smooth experience
            total_time = time.time() - start_time
            if total_time < (duration / 1000):
                time.sleep((duration / 1000) - total_time)

            if self.animation_running and not self.window_destroyed:
                try:
                    if hasattr(self, "root") and self.root and self.root.winfo_exists():
                        self.root.after(0, self.close)
                    else:
                        self.close()
                except Exception as e:
                    print(f"Error scheduling close: {e}")
                    self.close()

        # Start the close timer in a separate thread
        threading.Thread(target=close_after_delay, daemon=True).start()

    def run(self):
        """Run the loading screen"""
        self.root.mainloop()

    def start_preloading(self):
        """Start preloading all main windows in background"""

        def preload_windows():
            try:
                preload_steps = [
                    ("Loading Admin Dashboard...", self.preload_admin_dashboard, 1.5),
                    (
                        "Loading Employee Dashboard...",
                        self.preload_employee_dashboard,
                        1.5,
                    ),
                    (
                        "Loading Fabrication Window...",
                        self.preload_fabrication_window,
                        1.5,
                    ),
                    ("Loading Admin Login...", self.preload_admin_login, 1.5),
                    ("Loading Welcome Window...", self.preload_welcome_window, 1.5),
                    ("Finalizing Components...", self.finalize_preload, 2.0),
                ]

                total_steps = len(preload_steps)
                current_time = 0
                target_ready_time = 7.5  # "Ready!" should appear at 7.5 seconds

                for i, (status, preload_func, step_duration) in enumerate(
                    preload_steps
                ):
                    if not self.animation_running:
                        break

                    self.preload_status = status
                    self.preload_progress = int(
                        (current_time / target_ready_time) * 100
                    )

                    try:
                        preload_func()
                        time.sleep(step_duration)  # Use specific duration for each step
                        current_time += step_duration
                    except Exception as e:
                        print(f"Preload error for {status}: {e}")
                        time.sleep(0.2)
                        current_time += 0.2

                # Ensure we hit exactly 7.5 seconds before showing "Ready!"
                remaining_time = target_ready_time - current_time
                if remaining_time > 0:
                    time.sleep(remaining_time)

                self.preload_complete = True
                self.preload_status = "Ready!"
                self.preload_progress = 100

            except Exception as e:
                print(f"Preloading error: {e}")
                self.preload_complete = True

        # Start preloading in background thread
        threading.Thread(target=preload_windows, daemon=True).start()

    def preload_admin_dashboard(self):
        """Preload AdminDashboard class"""
        from gui.admin_dashboard import AdminDashboard
        # Just import the class, don't instantiate

    def preload_employee_dashboard(self):
        """Preload MainBrowser class"""
        from gui.employee_dashboard import MainBrowser
        # Just import the class, don't instantiate

    def preload_fabrication_window(self):
        """Preload fabricateWindow class"""
        # Fabricate window import removed (feature deprecated)
        # Just import the class, don't instantiate

    def preload_admin_login(self):
        """Preload AdminLogin class"""
        from gui.admin_login import AdminLogin
        # Just import the class, don't instantiate

    def preload_welcome_window(self):
        """Preload WelcomeWindow class"""
        from gui.employee_login import WelcomeWindow
        # Just import the class, don't instantiate

    def finalize_preload(self):
        """Finalize preloading process"""
        # Import additional modules that might be needed
        import pyodbc
        import openpyxl
        import cryptography
        import pyotp
        import qrcode

    # Removed cluttered functions for clean Black Mesa style:
    # - create_particle_effect (too busy)
    # - create_enhanced_loading_circle (replaced with clean version)
    # - create_progress_bar (removed loading bar)

    # Keep only the essential, clean functions that create the minimalist aesthetic
