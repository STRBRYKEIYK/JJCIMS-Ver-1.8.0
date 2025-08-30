class GlobalState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalState, cls).__new__(cls)
            cls._instance.current_user = None  # Initialize current_user
        return cls._instance

# Create a global instance
global_state = GlobalState()