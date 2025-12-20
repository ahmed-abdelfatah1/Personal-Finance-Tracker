"""Database Singleton - Ensures only one SQLite database connection exists."""


class DatabaseSingleton:
    """
    Singleton class for managing the database connection.
    
    Ensures only one database connection instance exists throughout
    the application lifecycle, preventing unnecessary connection creation.
    
    This pattern ensures that:
    - Only one SQLite connection pool is created
    - All database operations use the same connection instance
    - Prevents creating thousands of unnecessary connections
    """
    
    _instance = None
    _db = None
    
    def __new__(cls):
        """Ensure only one instance of DatabaseSingleton is created."""
        if cls._instance is None:
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_db(cls):
        """
        Get the singleton database instance.
        
        Returns:
            The SQLAlchemy database instance (singleton)
            
        Raises:
            RuntimeError: If database instance has not been initialized
        """
        if cls._db is None:
            raise RuntimeError(
                "Database instance not initialized. "
                "Call DatabaseSingleton.set_db() first."
            )
        return cls._db
    
    @classmethod
    def set_db(cls, db_instance):
        """
        Set the database instance (called during app initialization).
        
        This should be called once when the Flask app is created,
        typically in extensions.py when creating the SQLAlchemy instance.
        
        Args:
            db_instance: The SQLAlchemy database instance to use
        """
        if cls._db is not None and cls._db is not db_instance:
            raise RuntimeError(
                "Database instance already set. "
                "Cannot change database instance after initialization."
            )
        cls._db = db_instance
    
    @classmethod
    def is_initialized(cls):
        """Check if the database singleton has been initialized."""
        return cls._db is not None
    
    @classmethod
    def reset(cls):
        """
        Reset the singleton instance (useful for testing only).
        
        WARNING: This method should only be used in test environments.
        Resetting the database singleton in production can cause issues.
        """
        cls._instance = None
        cls._db = None

