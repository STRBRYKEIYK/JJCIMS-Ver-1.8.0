"""Image effects utilities for the JJCIMS application."""

from PIL import Image, ImageDraw


def create_scanline_effect(img, num_lines=35, line_opacity=0.25, glow_amount=1.0):
    """Create scanline interlacing effect on an image.

    Args:
        img: PIL Image object
        num_lines: Number of scanlines to create
        line_opacity: Opacity of the scanlines (0.0 to 1.0)
        glow_amount: Glow effect multiplier

    Returns:
        PIL Image with scanline effect applied
    """
    width, height = img.size
    scanline_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scanline_img)

    # Calculate spacing for scanlines
    line_spacing = height // num_lines

    # Draw scanlines
    for i in range(0, height, line_spacing):
        alpha = int(255 * line_opacity)
        draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha), width=1)

    # Blend scanlines with original image
    result = Image.alpha_composite(img, scanline_img)
    return result
