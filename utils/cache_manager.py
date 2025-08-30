"""Cache manager for storing frequently used resources."""
from PIL import Image, ImageTk
import os
from typing import Dict, Any

class CacheManager:
    _instance = None
    _image_cache: Dict[str, ImageTk.PhotoImage] = {}
    _data_cache: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_image(cls, image_path: str) -> ImageTk.PhotoImage:
        """Get an image from cache or load it if not cached."""
        if image_path not in cls._image_cache:
            try:
                image = Image.open(image_path)
                photo = ImageTk.PhotoImage(image)
                cls._image_cache[image_path] = photo
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                return None
        return cls._image_cache[image_path]
    
    @classmethod
    def cache_data(cls, key: str, data: Any) -> None:
        """Cache arbitrary data with a key."""
        cls._data_cache[key] = data
    
    @classmethod
    def get_cached_data(cls, key: str) -> Any:
        """Retrieve cached data by key."""
        return cls._data_cache.get(key)
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached data."""
        cls._image_cache.clear()
        cls._data_cache.clear()
