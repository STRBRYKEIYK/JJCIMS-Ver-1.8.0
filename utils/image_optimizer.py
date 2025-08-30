"""Utility for optimizing images to reduce memory usage."""
from PIL import Image
import os
from config.performance_config import MAX_IMAGE_SIZE, IMAGE_QUALITY, OPTIMIZE_IMAGES

class ImageOptimizer:
    @staticmethod
    def optimize_image(image_path):
        """Optimize an image for low-end systems."""
        if not OPTIMIZE_IMAGES:
            return Image.open(image_path)

        try:
            # Open the image
            img = Image.open(image_path)
            
            # Convert RGBA to RGB if necessary (reduces memory usage)
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg

            # Resize if larger than maximum size while maintaining aspect ratio
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Create an optimized version in memory
            optimized_img = img.copy()
            
            # Force cleanup of original image
            img.close()
            
            return optimized_img
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")
            return None

    @staticmethod
    def optimize_icon(icon_path):
        """Optimize an icon for low-end systems."""
        if not OPTIMIZE_IMAGES:
            return Image.open(icon_path)

        try:
            img = Image.open(icon_path)
            # Icons are typically small, so we just ensure they're in the right format
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            return img
        except Exception as e:
            print(f"Error optimizing icon {icon_path}: {e}")
            return None
