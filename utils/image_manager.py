"""Image manager to handle PhotoImage references and caching."""
from PIL import Image, ImageTk
import os

class ImageManager:
    _instance = None
    _images = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def load_image(cls, path, size=None):
        """Load an image and maintain its reference."""
        key = f"{path}_{size if size else 'original'}"
        if key not in cls._images:
            try:
                image = Image.open(path)
                if size:
                    image = image.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                cls._images[key] = photo
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                return None
        return cls._images[key]
    
    @classmethod
    def clear_cache(cls):
        """Clear the image cache."""
        cls._images.clear()
