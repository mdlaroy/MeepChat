import sqlite3

class Preferences:
    def __init__(self, db_name="data/user_preferences.db"):
        """Initialize the database connection and set up the preferences table."""
        try:
            self.connection = sqlite3.connect(db_name, check_same_thread=False)  
            self.cursor = self.connection.cursor()
            self.setup_database()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def setup_database(self):
        """Set up the preferences table if it doesn't already exist."""
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                preference_type TEXT NOT NULL,
                value TEXT NOT NULL
            )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error setting up database: {e}")

    def add_preference(self, user, preference_type, value):
        """Add a new preference for the user."""
        try:
            print(f"Attempting to add preference: user={user}, type={preference_type}, value={value}")
            self.cursor.execute("""
            INSERT INTO preferences (user, preference_type, value)
            VALUES (?, ?, ?)
            """, (user, preference_type, value))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error adding preference: {e}")

    def get_preferences(self, user, preference_type=None):
        """Retrieve preferences for the user. Optionally filter by type."""
        try:
            if preference_type:
                self.cursor.execute("""
                SELECT value FROM preferences
                WHERE user = ? AND preference_type = ?
                """, (user, preference_type))
            else:
                self.cursor.execute("""
                SELECT preference_type, value FROM preferences
                WHERE user = ?
                """, (user,))
            result = self.cursor.fetchall()
            print(f"Retrieved preferences for {user}: {result}")  # Debug output
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving preferences: {e}")
            return []

        



    def delete_preference(self, user, preference_type, value):
        """Delete a specific preference for the user."""
        try:
            self.cursor.execute("""
            DELETE FROM preferences
            WHERE user = ? AND preference_type = ? AND value = ?
            """, (user, preference_type, value))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error deleting preference: {e}")

    def close(self):
        """Close the database connection."""
        try:
            self.connection.close()
        except sqlite3.Error as e:
            print(f"Error closing database: {e}")
