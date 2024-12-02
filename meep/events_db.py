import sqlite3
from datetime import datetime

class Events:
    def __init__(self, db_name="data/user_events.db"):
        """Initialize the database connection and set up the events table."""
        try:
            self.connection = sqlite3.connect(db_name, check_same_thread=False)  
            self.cursor = self.connection.cursor()
            self.setup_database()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def setup_database(self):
        """Set up the events table if it doesn't already exist."""
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error setting up database: {e}")

    def add_event(self, user, description, date, time):
        """Add a new event to the database."""
        try:
            self.cursor.execute("""
            INSERT INTO events (user, description, date, time)
            VALUES (?, ?, ?, ?)
            """, (user, description, date, time))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error adding event: {e}")

    def get_upcoming_events(self, user, current_date, current_time):
        """
        Retrieve upcoming events for the user, ordered by date and time.
        
        Events are fetched if their date is later than the current date
        or if the date is the same but the time is later than the current time.
        """
        try:
            self.cursor.execute("""
            SELECT description, date, time FROM events
            WHERE user = ? AND (date > ? OR (date = ? AND time > ?))
            ORDER BY date, time
            """, (user, current_date, current_date, current_time))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving upcoming events: {e}")
            return []

    def delete_past_events(self):
        """Remove events that have already occurred from the database."""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")
            self.cursor.execute("""
            DELETE FROM events
            WHERE date < ? OR (date = ? AND time < ?)
            """, (current_date, current_date, current_time))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error deleting past events: {e}")


    def get_past_events(self, user):
        """Retrieve events that have already occurred for the given user."""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")
            self.cursor.execute("""
                SELECT description, date, time 
                FROM events
                WHERE user = ? AND (date < ? OR (date = ? AND time < ?))
                ORDER BY date DESC, time DESC
            """, (user, current_date, current_date, current_time))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving past events: {e}")
            return []


    def close(self):
        """Close the database connection."""
        try:
            self.connection.close()
        except sqlite3.Error as e:
            print(f"Error closing database: {e}")