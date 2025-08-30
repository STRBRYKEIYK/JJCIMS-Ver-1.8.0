"""Configuration for performance optimization."""

# Memory optimization
ENABLE_GARBAGE_COLLECTION = True
GC_THRESHOLD = 700  # Number of objects before triggering garbage collection

# Image optimization
OPTIMIZE_IMAGES = True
MAX_IMAGE_SIZE = (800, 800)  # Maximum dimensions for loaded images
IMAGE_QUALITY = 85  # JPEG quality for optimized images

# UI performance
ENABLE_ANIMATIONS = False  # Disable animations on low-end systems
ENABLE_SHADOWS = False    # Disable shadows on low-end systems
ENABLE_TRANSPARENCY = False  # Disable transparency effects on low-end systems

# Database optimization
DB_CONNECTION_TIMEOUT = 5  # Seconds
DB_CONNECTION_POOLING = True
MAX_DB_CONNECTIONS = 3

# Window loading
LAZY_LOAD_WINDOWS = True  # Enable lazy loading of windows
PRELOAD_CRITICAL = False  # Disable preloading even critical windows
