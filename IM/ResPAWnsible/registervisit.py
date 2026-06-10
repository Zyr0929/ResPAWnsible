import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

def get_pet_profile(pet_id):
    """Fetches target pet's core physical data, breed text, and behavior tag."""
    query = """
        SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType 
        FROM PET P
        LEFT JOIN BREED B ON P.PetID = B.PetID
        LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID
        LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
        WHERE P.PetID = ?;
    """
    c.execute(query, (pet_id,))
    return c.fetchone()

def get_active_room_occupants(room_id):
    """Fetches profiles of all animals currently active inside the chosen room."""
    query = """
        SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType 
        FROM VISIT V
        JOIN PET P ON V.PetID = P.PetID
        LEFT JOIN BREED B ON P.PetID = B.PetID
        LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID
        LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
        WHERE V.RoomID = ? AND (V.EndTime IS NULL OR V.EndTime = '');
    """
    c.execute(query, (room_id,))
    return c.fetchall()

def parse_species(breed_string):
    """Extracts a general classification category from the text input."""
    lowered = str(breed_string).lower()
    if "cat" in lowered or "feline" in lowered:
        return "Cat"
    if "bird" in lowered or "parrot" in lowered:
        return "Bird"
    return "Dog" # Default safe assumption

print("SAFE ROOM VISITATION CHECK")

try:
    # target pet
    pet_id = int(input("Enter Pet ID checking in: "))
    pet_profile = get_pet_profile(pet_id)
    
    if not pet_profile:
        print("[ERROR] That Pet ID doesn't exist in the system.")
        exit()
        
    pet_name, pet_weight, pet_behavior, breed_type = pet_profile
    pet_species = parse_species(breed_type)
    pet_size = "Small" if pet_weight < 30 else "Large"
    
    print(f"-> Target Animal: {pet_name} [{pet_species} | Size: {pet_size} | Tag: {pet_behavior}]")

    # rooms 
    print("\n--- Current Playroom Capacities ---")
    c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
    rooms = c.fetchall()
    for r_id, r_name, r_cap in rooms:
        c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID = ? AND (EndTime IS NULL OR EndTime = '');", (r_id,))
        current_count = c.fetchone()[0]
        print(f" [{r_id}] {r_name} (Occupancy: {current_count}/{r_cap})")

    room_id = int(input("\nSelect target Playroom ID: "))
    occupants = get_active_room_occupants(room_id)
    
    # safety stuff
    is_safe = True
    reason = ""

    if occupants:
        for occ_name, occ_weight, occ_behavior, occ_breed in occupants:
            occ_species = parse_species(occ_breed)
            occ_size = "Small" if occ_weight < 30 else "Large"
            
            # isolation needs
            if "Requires Solo Room" in [str(pet_behavior), str(occ_behavior)]:
                is_safe = False
                reason = "This room is occupied, and one of these pets requires a private space."
                break
                
            # species segregation
            if pet_species != occ_species:
                is_safe = False
                reason = f"Cannot place a {pet_species} ({pet_name}) with a {occ_species} ({occ_name})."
                break
            
            # aggression and size rules
            if pet_species == "Dog":
                # don't mix aggressive and calm pets
                if "Aggressive" in str(pet_behavior) and "Calm" in str(occ_behavior):
                    is_safe = False
                    reason = f"{pet_name} is Aggressive, but {occ_name} is Calm."
                    break
                if "Calm" in str(pet_behavior) and "Aggressive" in str(occ_behavior):
                    is_safe = False
                    reason = f"This playroom already contains {occ_name} who is flagged Aggressive."
                    break
                
                # aggression marker
                if "Aggressive" in str(pet_behavior) or "Aggressive" in str(occ_behavior):
                    if pet_size != occ_size:
                        is_safe = False
                        reason = f"Size/Aggression Mismatch! Cannot combine {pet_size} and {occ_size} dogs under active aggression markers."
                        break

    if not is_safe:
        print(f"\nCHECK-IN DENIED: {reason}")
    else:
        print(f"\nSafety checks passed for {pet_name}!")
        print("\n[Allowed Visit Types: 1 = Reservation, 2 = Walk-in]")
        visit_choice = input("Select Visit Type (1 or 2): ").strip()

        if visit_choice == "1":
            visit_type = "Reservation"
        else:
            visit_type = "Walk-in"

        current_date = datetime.now().strftime("%Y-%m-%d")
        start_time = datetime.now().strftime("%H:%M:%S")

        c.execute("""
            INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, EndTime, Notes)
            VALUES (?, ?, ?, ?, ?, NULL, 'Validated clear via systematic safety matrix rules.');
        """, (pet_id, room_id, visit_type, current_date, start_time))

        conn.commit()
        print(f"Success! {pet_name} has been securely tracked into Room {room_id} at {start_time}.")

except Exception as e:
    print(f"\nOperational Failure: {e}")
    conn.rollback()
finally:
    conn.close()