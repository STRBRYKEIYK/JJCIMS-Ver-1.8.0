"""
Window Icon Utility
===================
Provides functions to set consistent window icons across all GUI windows.
"""

import os
import tkinter as tk
from PIL import Image, ImageTk
import tempfile

def set_window_icon(window):
    """
    Set the JJCIMS icon for the window in both titlebar and taskbar.
    Uses the JJCIMS(2).ico file for consistent branding across all windows.
    
    Args:
        window: The tkinter window object (usually self.root)
    """
    try:
        # Get the path to the icon files - go up one level from utils to root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # utils directory
        app_root = os.path.dirname(current_dir)  # root directory (up one level)
        
        # Method 1: Use the JJCIMS(2).ico file (primary icon for all windows)
        ico_path = os.path.join(app_root, 'JJCIMS(2).ico')
        if os.path.exists(ico_path):
            try:
                window.iconbitmap(ico_path)
                print(f"Successfully set JJCIMS icon: {ico_path}")
                return  # Exit early if ICO works
            except Exception as e:
                print(f"Failed to set JJCIMS(2).ico icon: {e}")
        
        # Fallback: Try the icons folder for backward compatibility
        ico_path_fallback = os.path.join(app_root, 'icons', 'JJCFPIS.ico')
        if os.path.exists(ico_path_fallback):
            try:
                window.iconbitmap(ico_path_fallback)
                print(f"Successfully set icon using fallback: {ico_path_fallback}")
                return  # Exit early if ICO works
            except Exception as e:
                print(f"Failed to set fallback .ico icon: {e}")
        
        # Method 2: Fallback to PNG if ICO doesn't work
        png_path = os.path.join(app_root, 'assets', 'JJCIMS.png')
        if not os.path.exists(png_path):
            # Try other PNG locations as fallback
            png_path = os.path.join(app_root, 'assets', 'JJCFPIS.png')
        
        if os.path.exists(png_path):
            print(f"Falling back to PNG icon: {png_path}")
            
            # Load the PNG image
            icon_image = Image.open(png_path)
            original_size = icon_image.size
            print(f"Original PNG icon size: {original_size}")
            
            # Create a temporary ICO file with multiple sizes for better Windows taskbar integration
            with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as temp_ico:
                # Create multiple sizes for ICO format (Windows standard)
                icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                icon_images = []
                
                for size in icon_sizes:
                    resized = icon_image.resize(size, Image.Resampling.LANCZOS)
                    icon_images.append(resized)
                
                # Save as ICO with multiple sizes
                icon_images[0].save(temp_ico.name, format='ICO', sizes=icon_sizes)
                temp_ico_path = temp_ico.name
            
            # Try to set the temporary ICO file
            try:
                window.iconbitmap(temp_ico_path)
                print(f"Successfully set icon using temporary .ico file")
                
                # Store the temp file path for cleanup later
                if not hasattr(window, '_temp_ico_path'):
                    window._temp_ico_path = temp_ico_path
                return
                
            except Exception as e:
                print(f"Failed to set temporary .ico icon: {e}")
                # Clean up temp file if it failed
                try:
                    os.unlink(temp_ico_path)
                except:
                    pass
                
                # Final fallback to PhotoImage method
                print("Using final fallback PhotoImage method...")
                
                # Use largest possible sizes for PhotoImage method
                icon_1024 = icon_image  # Keep original quality
                icon_photo = ImageTk.PhotoImage(icon_1024)
                window.iconphoto(True, icon_photo)
                
                # Keep reference to prevent garbage collection
                if not hasattr(window, '_icon_refs'):
                    window._icon_refs = []
                window._icon_refs.append(icon_photo)
        
        else:
            print(f"Warning: No icon files found. Checked:")
            print(f"  ICO: {os.path.join(app_root, 'icons', 'JJCFPIS.ico')}")
            print(f"  ICO (old): {os.path.join(app_root, 'JJCFPIS.ico')}")
            print(f"  PNG: {png_path}")
            
    except Exception as e:
        print(f"Error setting window icon: {e}")

def set_window_icon_from_path(window, icon_path):
    """
    Set window icon from a specific path.
    Tries ICO format first, then falls back to other formats.
    
    Args:
        window: The tkinter window object
        icon_path: Path to the icon file
    """
    try:
        if os.path.exists(icon_path):
            # If it's already an ICO file, use it directly
            if icon_path.lower().endswith('.ico'):
                try:
                    window.iconbitmap(icon_path)
                    print(f"Successfully set icon using ICO file: {icon_path}")
                    return
                except Exception as e:
                    print(f"Failed to set ICO icon: {e}")
            
            # For other formats, convert to ICO
            icon_image = Image.open(icon_path)
            original_size = icon_image.size
            print(f"Original icon size: {original_size}")
            
            # Create a temporary ICO file
            with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as temp_ico:
                icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                icon_images = []
                
                for size in icon_sizes:
                    resized = icon_image.resize(size, Image.Resampling.LANCZOS)
                    icon_images.append(resized)
                
                # Save as ICO with multiple sizes
                icon_images[0].save(temp_ico.name, format='ICO', sizes=icon_sizes)
                temp_ico_path = temp_ico.name
            
            # Try to set the temporary ICO file
            try:
                window.iconbitmap(temp_ico_path)
                print(f"Successfully set icon using temporary ICO file")
                
                # Store the temp file path for cleanup later
                if not hasattr(window, '_temp_ico_path'):
                    window._temp_ico_path = temp_ico_path
                return
                
            except Exception as e:
                print(f"Failed to set temporary ICO icon: {e}")
                # Clean up temp file if it failed
                try:
                    os.unlink(temp_ico_path)
                except:
                    pass
                
                # Final fallback to PhotoImage
                print("Using fallback PhotoImage method...")
                icon_photo = ImageTk.PhotoImage(icon_image)
                window.iconphoto(True, icon_photo)
                
                # Keep reference to prevent garbage collection
                if not hasattr(window, '_icon_refs'):
                    window._icon_refs = []
                window._icon_refs.append(icon_photo)
            
        else:
            print(f"Warning: Icon file not found at {icon_path}")
            
    except Exception as e:
        print(f"Error setting window icon from path: {e}")
