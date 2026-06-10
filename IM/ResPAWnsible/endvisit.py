import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

def get_active_visits():
    """Fetches all pets currently checked into a room (EndTime is empty)."""
    query = """
        SELECT V.VisitID, P.Name, R.RoomName, V.VisitType, V.StartTime
        FROM VISIT V
        JOIN PET P ON V.PetID = P.PetID
        JOIN PLAYROOM R ON V.RoomID = R.RoomID
        WHERE V.EndTime IS NULL OR V.EndTime = '';
    """
    c.execute(query)
    return c.fetchall()

print("PET PLAYROOM CHECK-OUT")

try:
    active_visits = get_active_visits()
    
    if not active_visits:
        print("All playrooms are completely empty!")
        exit()
        
    print("Active Animals in Playrooms")
    valid_visit_ids = []
    for v_id, pet_name, room_name, v_type, start_time in active_visits:
        print(f" [VisitID: {v_id}] {pet_name} -> inside {room_name} ({v_type} | Started: {start_time})")
        valid_visit_ids.append(v_id)
        
    while True:
        try:
            target_visit_id = int(input("\nEnter the VisitID to Check-Out: "))
            if target_visit_id in valid_visit_ids:
                break
            else:
                print(f"Invalid choice. Choose from active options: {valid_visit_ids}")
        except ValueError:
            print("Please enter a valid integer number.")

    checkout_notes = input("Enter departure notes: ").strip()
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # visit record updates
    c.execute("""
        UPDATE VISIT
        SET EndTime = ?, Notes = ?
        WHERE VisitID = ?;
    """, (current_time, checkout_notes, target_visit_id))
    
    conn.commit()
    print(f"\nVisitID {target_visit_id} closed out at {current_time}.")

except Exception as e:
    print(f"\nCheck-out failed: {e}")
    conn.rollback()
finally:
    conn.close()