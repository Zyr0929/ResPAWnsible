import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'respawnsible.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.executescript('''
    CREATE TABLE IF NOT EXISTS Playrooms (id INTEGER PRIMARY KEY, name TEXT);
    CREATE TABLE IF NOT EXISTS Pets (id INTEGER PRIMARY KEY, name TEXT, behavior TEXT);
    CREATE TABLE IF NOT EXISTS Bookings (
        id INTEGER PRIMARY KEY, 
        pet_id INTEGER, 
        room_id INTEGER,
        FOREIGN KEY(pet_id) REFERENCES Pets(id),
        FOREIGN KEY(room_id) REFERENCES Playrooms(id)
    );
''')

print("--- Register New Pet ---")
name = input("Enter Pet Name: ")
behavior = input("Enter Behavior Tag (e.g., Small-Dog Aggressive, Calm): ")

c.execute("INSERT INTO Pets (name, behavior) VALUES (?, ?)", (name, behavior))
conn.commit()

print(f"\nSuccess! {name} has been addede to the database.")
conn.close()