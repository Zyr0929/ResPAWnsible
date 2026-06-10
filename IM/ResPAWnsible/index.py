import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')
conn = sqlite3.connect(db_path)

c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

def get_or_create_behavior_tags():
    """Silently ensures default tags exist and returns them without terminal warnings."""
    # Added ORDER BY to keep the terminal menu perfectly sorted numerically
    c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG ORDER BY TagID ASC;")
    tags = c.fetchall()
    
    if not tags:
        defaults = [
            ("Calm / Friendly",), 
            ("Nervous / Fearful",), 
            ("Hyperactive / Playful",), 
            ("Aggressive / Territorial",),
            ("Requires Solo Room",)
        ]
        c.executemany("INSERT INTO BEHAVIOR_TAG (Behavior) VALUES (?);", defaults)
        conn.commit()
        c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG ORDER BY TagID ASC;")
        tags = c.fetchall()
    return tags

print("PET REGISTRATION")

try:
    print("Owner Information")
    first_name = input("Enter Owner First Name: ").strip()
    last_name = input("Enter Owner Last Name: ").strip()
    phone_number = input("Enter Owner Phone Number: ").strip()
    
    c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (first_name, last_name))
    owner_id = c.lastrowid 
    c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, phone_number))
    
    print("\nPet Information")
    pet_name = input("Enter Pet Name: ").strip()
    weight = float(input("Enter Pet Weight (lbs): "))
    
    # breed
    breed_type = input("Enter Species & Breed (e.g., Dog - Golden Retriever, Cat - Siamese): ").strip()
    
    c.execute("INSERT INTO PET (OwnerID, Name, Weight_lbs) VALUES (?, ?, ?);", (owner_id, pet_name, weight))
    pet_id = c.lastrowid  
    c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, breed_type))
    
    print("\nAssign Behavior Tag")
    available_tags = get_or_create_behavior_tags()
    
    valid_ids = []
    for tag_id, behavior_name in available_tags:
        print(f" [{tag_id}] {behavior_name}")
        valid_ids.append(tag_id)
        
    while True:
        try:
            selected_tag_id = int(input("\nSelect a Behavior Tag ID from the options above: "))
            if selected_tag_id in valid_ids:
                break
            else:
                print(f"Invalid choice. Please pick from: {valid_ids}")
        except ValueError:
            print("Please enter a valid integer ID number.")
    
    c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", (pet_id, selected_tag_id))
    
    conn.commit()
    print(f"Registered {pet_name} ({breed_type}) successfully!")

except Exception as e:
    print(f"\nSomething went wrong: {e}")
    conn.rollback()
finally:
    conn.close()