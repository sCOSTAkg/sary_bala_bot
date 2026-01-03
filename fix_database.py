import base64
import os

db_path = "/Users/guest1/sary_bala_bot/sary_bala_bot/database.py"

with open(db_path, "r") as f:
    content = f.read().strip()

# Remove newlines if any within the base64 string
content = content.replace("\n", "").replace("\r", "").replace(" ", "")

# Add padding
missing_padding = len(content) % 4
if missing_padding:
    content += '=' * (4 - missing_padding)

if content.startswith("aW1wb3J0"): 
    try:
        decoded = base64.b64decode(content).decode("utf-8")
        print("Successfully decoded database.py")
        
        with open(db_path + ".bak", "w") as f:
            f.write(content) # Write cleaned base64
            
        with open(db_path, "w") as f:
            f.write(decoded)
        print("Wrote decoded content to database.py")
        print("First 100 chars:")
        print(decoded[:100])
        
    except Exception as e:
        print(f"Error decoding: {e}")
else:
    print("File does not start with 'import' (encoded)")
