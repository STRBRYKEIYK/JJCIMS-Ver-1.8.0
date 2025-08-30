"""
Font utilities for JJCFPIS - PyInstaller compatible font loading
"""

from PIL import ImageFont
import os
import sys


def get_system_font(font_name, size):
    """
    Load a system font by name, works with both development and PyInstaller builds.
    
    Args:
        font_name (str): Font filename (e.g., "arial.ttf")
        size (int): Font size in pixels
        
    Returns:
        ImageFont: Loaded font object or None if not found
    """
    try:
        # Try to load font - PIL will search system font directories
        return ImageFont.truetype(font_name, size)
    except (OSError, IOError):
        return None


def get_bold_font(size=16):
    """
    Get the best available bold font for the system.
    
    Args:
        size (int): Font size in pixels
        
    Returns:
        ImageFont: Best available bold font
    """
    # List of fonts to try, in order of preference
    bold_fonts = [
        "seguibl.ttf",    # Segoe UI Black (Windows - extra bold)
        "segoeuib.ttf",   # Segoe UI Bold (Windows)
        "arial.ttf",      # Arial (Windows/cross-platform)
        "calibrib.ttf",   # Calibri Bold (Windows)
        "DejaVuSans-Bold.ttf",  # DejaVu Sans Bold (Linux)
        "Liberation Sans Bold.ttf",  # Liberation Sans Bold (Linux)
        "Helvetica-Bold.ttf",  # Helvetica Bold (macOS)
        "System Bold.ttf",     # System Bold (macOS)
    ]
    
    for font_name in bold_fonts:
        font = get_system_font(font_name, size)
        if font is not None:
            return font
    
    # If no bold font found, try regular fonts
    regular_fonts = [
        "segoeui.ttf",    # Segoe UI (Windows)
        "arial.ttf",      # Arial
        "calibri.ttf",    # Calibri
        "DejaVuSans.ttf", # DejaVu Sans (Linux)
        "Liberation Sans.ttf",  # Liberation Sans (Linux)
        "Helvetica.ttf",  # Helvetica (macOS)
    ]
    
    for font_name in regular_fonts:
        font = get_system_font(font_name, size)
        if font is not None:
            return font
    
    # Last resort - default font
    try:
        return ImageFont.load_default()
    except:
        # If even default font fails, return None
        return None


def get_font_info():
    """
    Get information about available fonts for debugging.
    
    Returns:
        dict: Dictionary with font availability information
    """
    fonts_to_check = [
        "seguibl.ttf", "segoeuib.ttf", "arial.ttf", "calibrib.ttf",
        "DejaVuSans-Bold.ttf", "Liberation Sans Bold.ttf",
        "Helvetica-Bold.ttf", "System Bold.ttf"
    ]
    
    available_fonts = {}
    for font_name in fonts_to_check:
        font = get_system_font(font_name, 12)  # Test with small size
        available_fonts[font_name] = font is not None
    
    return available_fonts


if __name__ == "__main__":
    # Test font loading
    print("=== Font Availability Test ===")
    font_info = get_font_info()
    for font_name, available in font_info.items():
        status = "✓" if available else "✗"
        print(f"{status} {font_name}")
    
    print("\n=== Testing Bold Font Loading ===")
    bold_font = get_bold_font(16)
    if bold_font:
        print("✓ Bold font loaded successfully")
    else:
        print("✗ No bold font available")
