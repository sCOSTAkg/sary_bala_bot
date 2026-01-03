import json
import sys

file_path = "/Users/guest1/Downloads/Sary Bala Bot Logs.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    try:
        data = json.loads(content)
        # Assuming it's a list of log entries
        if isinstance(data, list):
            print(f"Loaded {len(data)} log entries.")
            errors = []
            for entry in data:
                # Adjust fields based on structure, usually 'message', 'level', etc.
                # If entry is a dict
                if isinstance(entry, dict):
                    msg = str(entry).lower()
                    if "error" in msg or "exception" in msg or "critical" in msg or "failed" in msg:
                        errors.append(entry)
                # If entry is string
                elif isinstance(entry, str):
                    if "error" in entry.lower():
                        errors.append(entry)
            
            print(f"Found {len(errors)} errors.")
            print("Last 5 errors:")
            for e in errors[-5:]:
                print(json.dumps(e, indent=2, ensure_ascii=False))
        else:
            print("JSON is not a list. Structure:", type(data))
            # recursive search or just print part of it?
            print(str(data)[:1000])

    except json.JSONDecodeError:
        print("File is not valid JSON. Showing last 2000 chars:")
        print(content[-2000:])

except Exception as e:
    print(f"Error reading file: {e}")
