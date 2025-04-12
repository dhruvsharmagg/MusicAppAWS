import json
from collections import defaultdict

# Load the full JSON data
with open("2025a1.json", "r") as f:
    data = json.load(f)
    songs = data["songs"]

# Dictionary to group songs by (title, artist)
duplicates = defaultdict(list)

for song in songs:
    key = (song["title"].strip().lower(), song["artist"].strip().lower())
    duplicates[key].append(song)

# Print duplicates with more than one entry
found = False
print("🔍 Checking for duplicate (title, artist) pairs...\n")

for (title, artist), entries in duplicates.items():
    if len(entries) > 1:
        found = True
        print(f"⚠️ Duplicate found: '{title.title()}' by {artist.title()} ({len(entries)} versions)")
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. Album: {entry['album']} | Year: {entry['year']} | Image: {entry['img_url']}")
        print()

if not found:
    print("✅ No duplicates found. You're good to go!")
