from PIL import Image, ImageEnhance, ImageDraw, ImageTk

def create_scanline_effect(image, num_lines=50, line_opacity=0.3, glow_amount=1.2):
    """
    Apply a retro CRT scanline effect with glow to an image, respecting transparency.
    
    Args:
        image: PIL Image object
        num_lines: Number of scanlines to draw
        line_opacity: Opacity of the scanlines (0.0 to 1.0)
        glow_amount: Amount of glow effect (1.0 = normal brightness)
    
    Returns:
        PIL Image object with the effect applied, preserving original transparency
    """
    try:
        # Convert image to RGBA if it isn't already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Get the alpha channel safely
        if len(image.split()) >= 4:
            alpha = image.split()[3]
        else:
            # Create an alpha channel if it doesn't exist
            alpha = Image.new('L', image.size, 255)
        
        # Convert to RGB for processing
        rgb_image = image.convert('RGB')
        
        # Apply glow effect
        enhancer = ImageEnhance.Brightness(rgb_image)
        glowing_image = enhancer.enhance(glow_amount)
        
        # Convert back to RGBA
        glowing_image = glowing_image.convert('RGBA')
        
        # Create scanline overlay
        width, height = image.size
        if width <= 0 or height <= 0:
            return image  # Return original if invalid dimensions
            
        scanlines = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(scanlines)
        
        # Calculate line spacing (ensure at least 2 pixels to avoid broadcasting issues)
        line_spacing = max(2, height // max(1, num_lines))
        
        # Draw scanlines safely
        for y in range(0, height, line_spacing):
            if y < height:  # Ensure y is within bounds
                try:
                    draw.line(
                        [(0, y), (width, y)],
                        fill=(0, 0, 0, int(255 * min(line_opacity, 1.0)))
                    )
                except Exception:
                    continue  # Skip problematic lines
        
        # Apply scanlines to glowing image
        result = Image.alpha_composite(glowing_image, scanlines)
        
        # Restore original alpha channel
        r, g, b, _ = result.split()
        final = Image.merge('RGBA', (r, g, b, alpha))
        
        return final
    except Exception as e:
        print(f"Error creating scanline effect: {e}")
        return image  # Return original image if effect fails

def create_window_icon(image_path, size=1024):
    """
    Create a properly sized window icon for Windows systems, optimized for high DPI displays.
    Args:
        image_path (str): Path to the icon image
        size (int): Maximum size of the icon (default is 1024x1024 for high DPI displays)
    Returns:
        PhotoImage: The resized icon image
    """
    from PIL import Image, ImageTk
    try:
        icon = Image.open(image_path)
        # Create a new image with transparency
        icon = icon.convert('RGBA')
        
        # For best display in Windows, we'll create a high-resolution icon
        target_size = (size, size)
        
        # Calculate the new size while maintaining aspect ratio
        original_width, original_height = icon.size
        ratio = min(target_size[0]/original_width, target_size[1]/original_height)
        new_size = (int(original_width * ratio), int(original_height * ratio))
        
        # Create a square transparent background
        final_image = Image.new('RGBA', target_size, (0, 0, 0, 0))
        
        # Resize the icon using high-quality resampling
        resized_icon = icon.resize(new_size, Image.Resampling.LANCZOS)
        
        # Center the resized icon on the transparent background
        paste_x = (target_size[0] - new_size[0]) // 2
        paste_y = (target_size[1] - new_size[1]) // 2
        final_image.paste(resized_icon, (paste_x, paste_y), resized_icon)
        
        # Convert to PhotoImage at the maximum size for high DPI displays
        return ImageTk.PhotoImage(final_image)
    except Exception as e:
        print(f"Error creating window icon: {e}")
        return None

def create_text_with_scanlines(text, font_size=32, is_bold=False):
    """
    Create an image of text with CRT scanline effect and orange glow.
    Args:
        text (str): The text to render
        font_size (int): Font size to use
        is_bold (bool): Whether to use bold font
    Returns:
        PhotoImage: The processed image with text and scanline effect
    """
    from PIL import ImageFont
    
    # Calculate image size based on text
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Regular Segoe UI
        if is_bold:
            font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"  # Bold Segoe UI
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text size with padding
    padding = 20
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0] + padding * 2
    height = bbox[3] - bbox[1] + padding * 2

    # Create base image with black background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # Calculate text position
    text_x = padding
    text_y = padding

    # Draw orange glow effect
    glow_color = (255, 111, 0, 100)  # Orange with alpha
    for offset in range(3):
        draw.text((text_x + offset, text_y), text, font=font, fill=glow_color)
        draw.text((text_x - offset, text_y), text, font=font, fill=glow_color)
        draw.text((text_x, text_y + offset), text, font=font, fill=glow_color)
        draw.text((text_x, text_y - offset), text, font=font, fill=glow_color)
    
    # Draw main text in orange
    draw.text((text_x, text_y), text, font=font, fill=(255, 111, 0, 255))

    # Apply scanline effect
    img = create_scanline_effect(img, num_lines=30, line_opacity=0.2, glow_amount=1.3)
    
    return ImageTk.PhotoImage(img)

