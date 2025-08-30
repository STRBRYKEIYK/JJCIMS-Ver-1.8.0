"""
Notification System for JJCFPIS
==============================
Provides toast-style notifications that appear at the top of the window.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys

# Add utils directory to path
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if utils_path not in sys.path:
    sys.path.append(utils_path)

try:
    from utils.image_effects import create_scanline_effect
except ImportError:
    print("Warning: image_effects module not found, notifications will work without scanlines")
    def create_scanline_effect(img, **kwargs):
        return img

class NotificationManager:
    """Manages toast-style notifications for the application"""
    
    def __init__(self, root_window):
        self.root = root_window
        self.active_notifications = []
        self.notification_y_offset = 10  # Distance from top of window
        
    def create_notification_image(self, title, body, width=450, height=140, type_="info"):
        """Create a notification image with title and body text, colored border by type"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 220))  # Semi-transparent black
        draw = ImageDraw.Draw(img)
        # Border color by type
        border_colors = {
            "info": (0, 120, 215, 255),      # Blue
            "success": (34, 139, 34, 255),   # Green
            "error": (200, 0, 0, 255),       # Red
            "warning": (255, 165, 0, 255),   # Orange
        }
        border_color = border_colors.get(type_, (255, 111, 0, 255))
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=3)
        # Load fonts
        try:
            title_font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"
            body_font_path = "C:\\Windows\\Fonts\\segoeui.ttf"
            title_font = ImageFont.truetype(title_font_path, 18)
            body_font = ImageFont.truetype(body_font_path, 13)
        except Exception:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        padding = 15
        title_y = padding
        # Title glow effect (by type)
        glow_colors = {
            "info": (0, 120, 215, 120),
            "success": (34, 139, 34, 120),
            "error": (200, 0, 0, 120),
            "warning": (255, 165, 0, 120),
        }
        glow_color = glow_colors.get(type_, (255, 111, 0, 120))
        for offset in range(2):
            draw.text((padding + offset, title_y), title, font=title_font, fill=glow_color)
            draw.text((padding - offset, title_y), title, font=title_font, fill=glow_color)
            draw.text((padding, title_y + offset), title, font=title_font, fill=glow_color)
            draw.text((padding, title_y - offset), title, font=title_font, fill=glow_color)
        # Main title text (by type)
        main_colors = {
            "info": (0, 120, 215, 255),
            "success": (34, 139, 34, 255),
            "error": (200, 0, 0, 255),
            "warning": (255, 165, 0, 255),
        }
        main_color = main_colors.get(type_, (255, 111, 0, 255))
        draw.text((padding, title_y), title, font=title_font, fill=main_color)
        # Draw body text
        body_lines = body.split('\n')
        body_y = title_y + 28
        for line in body_lines:
            line_x = padding
            for offset in range(1):
                draw.text((line_x + offset, body_y), line, font=body_font, fill=(200, 200, 200, 100))
                draw.text((line_x - offset, body_y), line, font=body_font, fill=(200, 200, 200, 100))
            draw.text((line_x, body_y), line, font=body_font, fill=(220, 220, 220, 255))
            body_y += 17
        img = create_scanline_effect(img, num_lines=25, line_opacity=0.3, glow_amount=1.2)
        return ImageTk.PhotoImage(img)
    
    def show_notification(self, title, body, duration=4000, type_="info"):
        """Show a toast notification at the top right of the window, with type (info/success/error/warning), slide in/out, stackable, queue if max stack reached."""
        try:
            if not hasattr(self, 'notification_queue'):
                self.notification_queue = []
            if not hasattr(self, 'max_stack'):
                self.max_stack = 3  # Max number of visible toasts
            # If too many, queue it
            self._cleanup_notifications()
            if len(self.active_notifications) >= self.max_stack:
                self.notification_queue.append((title, body, duration, type_))
                return
            notification = tk.Toplevel(self.root)
            notification.overrideredirect(True)
            notification.attributes('-topmost', True)
            notification.configure(bg='black')
            notification.attributes('-alpha', 0.0)
            notif_img = self.create_notification_image(title, body, type_=type_)
            label = tk.Label(notification, image=notif_img, bg='black')
            label.image = notif_img
            label.pack()
            notification.update_idletasks()
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_width = self.root.winfo_width()
            notif_width = notification.winfo_reqwidth()
            notif_height = notification.winfo_reqheight()
            notif_x = root_x + root_width - notif_width - 20
            # Stack notifications
            notif_y = root_y + self.notification_y_offset
            for existing_notif in self.active_notifications:
                if existing_notif.winfo_exists():
                    notif_y += notif_height + 10
            # Start off screen (slide in from top right)
            start_y = notif_y - 60
            notification.geometry(f"+{notif_x}+{start_y}")
            self.active_notifications.append(notification)
            self._slide_in(notification, notif_x, notif_y)
            self.root.after(duration, lambda: self._slide_out(notification, notif_x, notif_y))
        except Exception as e:
            print(f"Error showing notification: {e}")

    def _slide_in(self, notification, final_x, final_y, step=0):
        try:
            # Check if notification and root still exist
            if not self.root.winfo_exists() or not notification.winfo_exists():
                return
                
            # Animate from above to final_y
            current_y = notification.winfo_y()
            if current_y < final_y:
                new_y = min(current_y + 20, final_y)
                notification.geometry(f"+{final_x}+{new_y}")
                # attributes('-alpha') returns a float; update it safely
                try:
                    current_alpha = notification.attributes('-alpha')
                except Exception:
                    current_alpha = 0.0
                notification.attributes('-alpha', min(0.9, current_alpha + 0.1))
                
                # Store the timer ID with the notification for cleanup
                timer_id = notification.after(10, lambda: self._slide_in(notification, final_x, final_y, step+1))
                
                # Store reference to after ID for later cleanup
                if not hasattr(notification, '_after_ids'):
                    notification._after_ids = []
                notification._after_ids.append(timer_id)
            else:
                notification.geometry(f"+{final_x}+{final_y}")
                notification.attributes('-alpha', 0.9)
        except Exception as e:
            print(f"Error in slide_in: {e}")

    def _slide_out(self, notification, final_x, final_y):
        try:
            # Check if notification and root still exist
            if not self.root.winfo_exists() or not notification.winfo_exists():
                # Clean up this notification from active_notifications
                self._cleanup_notifications()
                return
                
            # Animate up and fade out
            current_y = notification.winfo_y()
            if current_y > final_y - 60:
                new_y = max(current_y - 20, final_y - 60)
                notification.geometry(f"+{final_x}+{new_y}")
                # attributes('-alpha') returns a float; update it safely
                try:
                    current_alpha = notification.attributes('-alpha')
                except Exception:
                    current_alpha = 0.9
                notification.attributes('-alpha', max(0.0, current_alpha - 0.1))
                
                # Store the timer ID with the notification for cleanup
                timer_id = notification.after(10, lambda: self._slide_out(notification, final_x, final_y))
                
                # Store reference to after ID for later cleanup
                if not hasattr(notification, '_after_ids'):
                    notification._after_ids = []
                notification._after_ids.append(timer_id)
            else:
                self._remove_notification(notification)
                # After removal, show next in queue if any
                if hasattr(self, 'notification_queue') and self.notification_queue:
                    next_args = self.notification_queue.pop(0)
                    self.show_notification(*next_args)
        except Exception as e:
            print(f"Error in slide_out: {e}")
            # Clean up in case of error
            self._cleanup_notifications()

    def _cleanup_notifications(self):
        """Remove destroyed notifications from active_notifications and cancel pending callbacks"""
        valid_notifications = []
        for n in self.active_notifications:
            if n.winfo_exists():
                valid_notifications.append(n)
            else:
                # Cancel any pending after callbacks
                if hasattr(n, '_after_ids'):
                    for after_id in n._after_ids:
                        try:
                            self.root.after_cancel(after_id)
                        except Exception:
                            pass
        self.active_notifications = valid_notifications
    
    def show_simple_notification(self, message, duration=3000, type_="info"):
        """Show a simple notification with just text (backward compatibility, with type)"""
        self.show_notification(message, "", duration, type_)
    
    def _fade_in(self, notification):
        """Fade in the notification"""
        try:
            # Make sure notification still exists
            if not notification.winfo_exists():
                return
                
            alpha = 0.1
            def fade_step():
                nonlocal alpha
                if notification.winfo_exists() and alpha < 0.9:
                    notification.attributes('-alpha', alpha)
                    alpha += 0.1
                    
                    # Store the timer ID with the notification for cleanup
                    timer_id = notification.after(50, fade_step)
                    
                    # Store reference to after ID for later cleanup
                    if not hasattr(notification, '_after_ids'):
                        notification._after_ids = []
                    notification._after_ids.append(timer_id)
                else:
                    if notification.winfo_exists():
                        notification.attributes('-alpha', 0.9)
            fade_step()
        except Exception as e:
            print(f"Error in fade_in: {e}")
    
    def _fade_out(self, notification):
        """Fade out the notification"""
        try:
            # Make sure notification still exists
            if not notification.winfo_exists():
                self._destroy_notification(notification)
                return
                
            alpha = 0.9
            def fade_step():
                nonlocal alpha
                if notification.winfo_exists() and alpha > 0:
                    notification.attributes('-alpha', alpha)
                    alpha -= 0.1
                    
                    # Store the timer ID with the notification for cleanup
                    timer_id = notification.after(50, fade_step)
                    
                    # Store reference to after ID for later cleanup
                    if not hasattr(notification, '_after_ids'):
                        notification._after_ids = []
                    notification._after_ids.append(timer_id)
                else:
                    self._destroy_notification(notification)
            fade_step()
        except Exception as e:
            print(f"Error in fade_out: {e}")
            self._destroy_notification(notification)
    
    def _remove_notification(self, notification):
        """Remove notification with fade out effect"""
        self._fade_out(notification)
    
    def _destroy_notification(self, notification):
        """Destroy the notification window and clean up resources"""
        try:
            # Cancel any pending after callbacks
            if hasattr(notification, '_after_ids'):
                for after_id in notification._after_ids:
                    try:
                        self.root.after_cancel(after_id)
                    except Exception:
                        pass
                
            # Remove from active notifications list
            if notification in self.active_notifications:
                self.active_notifications.remove(notification)
                
            # Destroy the window if it still exists
            if notification.winfo_exists():
                notification.destroy()
        except Exception as e:
            print(f"Error destroying notification: {e}")


# Global notification manager instance
_notification_manager = None

def init_notifications(root_window):
    """Initialize the notification system with the root window"""
    global _notification_manager
    _notification_manager = NotificationManager(root_window)

def show_notification(title, body="", duration=4000, type_="info"):
    """Show a notification with title and body (convenience function, with type)"""
    global _notification_manager
    if _notification_manager:
        _notification_manager.show_notification(title, body, duration, type_)
    else:
        print(f"Notification: {title} - {body}")

def show_simple_notification(message, duration=3000, type_="info"):
    """Show a simple notification with just text (convenience function, with type)"""
    global _notification_manager
    if _notification_manager:
        _notification_manager.show_simple_notification(message, duration, type_)
    else:
        print(f"Notification: {message}")
