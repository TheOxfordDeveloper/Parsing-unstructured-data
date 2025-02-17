import re
import csv

# Define regex patterns 
year_name_pattern = re.compile(r"\b(\d{4})\s([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\b")
color_year_name_pattern = re.compile(r"([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*(gr|b|ch|ro|br|bl|wh|dkb/br)\s*,\s*\d{4}")
year_pattern = r'\b\d{4}\b'
starts_pattern = r'\b(\d+)\s*sts\b'
wins_pattern = r'\b(\d+)\s*wins\b'
earnings_pattern = r'(?<!\()\$\s?([\d,]+)(?!\))'
foals_pattern = r'(\d+)\s*foals'
rnrs_pattern = r'(\d+)\s*rnrs'
wnrs_pattern = r'(\d+)\s*wnrs'
sw_pattern = r'(\d+)\s*SW'
sex_pattern = r'\b([fgcmh])\b'
colour_pattern = r'\b(gr|b|ch|ro|br|bl|wh|dkb/br|dk b|blk|bay/br|dk|dk br|dkb)\b'
career_pattern = r'Ran (\d+) yrs'
sire1_pattern = re.compile(r"\d{4} [A-Za-z''\- ]+, [A-Za-z/]+ [cfg], ([A-Z][A-Za-z'' ]+)")
sire_pattern = re.compile(r"([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*(gr|b|ch|ro|br|bl|wh|dkb/br)\s*,\s*\d{4}\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)")
dam_pattern = re.compile(r"([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*(gr|b|ch|ro|br|bl|wh|dkb/br)\s*,\s*\d{4}\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)")
damsire_pattern = re.compile(r"([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*(gr|b|ch|ro|br|bl|wh|dkb/br)\s*,\s*\d{4}\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)\s*,\s*([A-Z][a-zA-Z]*('[a-zA-Z]+)?( [A-Z][a-zA-Z]*('[a-zA-Z]+)?)*)")

def split_stakes_wins(age_sw_text):
    """Split combined stakes wins into individual races."""
    results = []
    
    # Extract the age
    age_match = re.search(r'At (\d+)', age_sw_text)
    if not age_match:
        return results
    
    age = f"At {age_match.group(1)}"
    
    # Remove the "At X won" prefix to get just the race list
    races_text = age_sw_text.split('won ')[1]
    
    # Split by comma, but handle parentheses properly
    races = []
    current_race = ''
    paren_count = 0
    
    for char in races_text:
        if char == '(':
            paren_count += 1
            current_race += char
        elif char == ')':
            paren_count -= 1
            current_race += char
        elif char == ',' and paren_count == 0:
            races.append(current_race.strip())
            current_race = ''
        else:
            current_race += char
    
    if current_race:
        races.append(current_race.strip())
    
    # Create entries for each race
    for race in races:
        if race:  # Skip empty strings
            results.append((age, race.strip()))
    
    return results

def process_sw_stakes_wins(entries):
    """Process entries to create separate rows for each stakes win."""
    expanded_entries = []
    
    for entry in entries:
        has_stakes_wins = False
        
        # If there are stakes wins, create separate entries for each
        if entry.get("age_sw_stakes"):
            for age_sw_text in entry["age_sw_stakes"]:
                individual_wins = split_stakes_wins(age_sw_text)
                for age, stakes_win in individual_wins:
                    new_entry = entry.copy()
                    new_entry["Age of SW"] = age
                    new_entry["Stakes Win"] = stakes_win
                    del new_entry["age_sw_stakes"]
                    expanded_entries.append(new_entry)
                    has_stakes_wins = True
        
        # If no stakes wins, include the original entry
        if not has_stakes_wins:
            entry_copy = entry.copy()
            if "age_sw_stakes" in entry_copy:
                del entry_copy["age_sw_stakes"]
            expanded_entries.append(entry_copy)
    
    return expanded_entries

def find_previous_female(entries, current_index, max_lookback=15):
    """Find the most recent female in previous entries."""
    lookback_count = 0
    index = current_index - 1
    while index >= 0 and lookback_count < max_lookback:
        if entries[index].get("sex") == "f" and entries[index].get("name"):
            return entries[index].get("name")
        index -= 1
        lookback_count += 1
    return None

# Initialise variables
entries = []
current_entry = {
    "year": None, "colour": None, "sex": None, "starts": None, "wins": None, "earnings": None,
    "foals": None, "rnrs": None, "wnrs": None, "SW": None, "name": None, "sire": None, 
    "dam": None, "damsire": None, "career length": None, "age_sw_stakes": []
}
previous_sire = None
previous_but_one_sire = None  # To track the sire of the row before the previous one
previous_dam = None  # To track the dam of the previous row

# Read and process the file
with open('/Users/theoxforddeveloper/Desktop/Parsing_repo/removed_delimiter_data/Abadan_delimiter.txt', 'r', errors='replace') as file:
    file_content = file.read()
    lines_list = file_content.splitlines()

# Parse the lines
for i, line in enumerate(lines_list):
    # Check for a year (birth year)
    year_match = re.search(year_pattern, line)
    if year_match and (i == 0 or any(current_entry.values())):
        if any(current_entry.values()):
            entries.append(current_entry)
        current_entry = {
            "year": year_match.group(), "colour": None, "sex": None, "starts": None, "wins": None,
            "earnings": None, "foals": None, "rnrs": None, "wnrs": None, "SW": None, "name": None,
            "sire": None, "dam": None, "damsire": None, "career length": None, "age_sw_stakes": []
        }

    # Check for names after year
    name_after_year_match = re.search(year_name_pattern, line)
    if name_after_year_match:
        current_entry["name"] = name_after_year_match.group(2)

    # Check for names before colour and year
    name_before_colour_year_match = re.search(color_year_name_pattern, line)
    if name_before_colour_year_match:
        current_entry["name"] = name_before_colour_year_match.group(1)

    # Check for Dam
    dam_match = re.search(dam_pattern, line)
    if dam_match:
        current_entry["dam"] = dam_match.group(10)

    # Check for sex
    sex_match = re.search(sex_pattern, line)
    if sex_match:
        current_entry["sex"] = sex_match.group(1)

    # If no sex is found, default it to 'f'
    if current_entry["sex"] is None:
        current_entry["sex"] = "f"

    # Check for colour
    colour_match = re.search(colour_pattern, line)
    if colour_match:
        current_entry["colour"] = colour_match.group(1)

    # Check for starts
    starts_match = re.search(starts_pattern, line)
    if starts_match:
        current_entry["starts"] = starts_match.group(1)

    # Check for wins
    wins_match = re.search(wins_pattern, line)
    if wins_match:
        current_entry["wins"] = wins_match.group(1)

    # Check for earnings
    earnings_match = re.search(earnings_pattern, line)
    if earnings_match:
        earnings_value = earnings_match.group(1).replace(",", "")
        current_entry["earnings"] = earnings_value

    # Check for foals
    foals_match = re.search(foals_pattern, line)
    if foals_match:
        current_entry["foals"] = foals_match.group(1)

    # Check for rnrs
    rnrs_match = re.search(rnrs_pattern, line)
    if rnrs_match:
        current_entry["rnrs"] = rnrs_match.group(1)

    # Check for wnrs
    wnrs_match = re.search(wnrs_pattern, line)
    if wnrs_match:
        current_entry["wnrs"] = wnrs_match.group(1)

    # Check for SW
    sw_match = re.search(sw_pattern, line)
    if sw_match:
        current_entry["SW"] = sw_match.group(1)

    # Check for sire
    sire_match = re.search(sire1_pattern, line)
    if sire_match:
        current_entry["sire"] = sire_match.group(1)
        previous_but_one_sire = previous_sire  # Track the "previous but one" sire
        previous_sire = current_entry["sire"]
    else:
        sire_match2 = re.search(sire_pattern, line)
        if sire_match2:
            current_entry["sire"] = sire_match2.group(6)
            previous_but_one_sire = previous_sire  # Track the "previous but one" sire
            previous_sire = current_entry["sire"]

    # Check for damsire
    damsire_match = re.search(damsire_pattern, line)
    if damsire_match:
        current_entry["damsire"] = damsire_match.group(14)
    elif not current_entry["damsire"] and previous_but_one_sire:
        current_entry["damsire"] = previous_but_one_sire  # Populate with the "previous but one" row's sire


        # Check if the dam is the same as the previous row's dam
    if current_entry["dam"] == previous_dam:
        try:
            current_entry["damsire"] = previous_damsire  # Try to copy the damsire
        except NameError:
            pass  # If previous_damsire isn't defined, just skip it and continue

    # Update the previous row's dam and damsire for the next iteration
    previous_dam = current_entry["dam"]
    try:
        previous_damsire = current_entry.get("damsire")  # Safely get damsire value
    except:
        previous_damsire = None  # Set to None if there's any error


    # Check for career length
    career_match = re.search(career_pattern, line)
    if career_match:
        current_entry["career length"] = career_match.group(1)

    # Check for Age of SW and Stakes Win
    sw_stakes_matches = re.finditer(r'At \d+ won[^,]*(?:,\s*[^,]*)*(?=,\s*(?:At|$)|$)', line)
    for match in sw_stakes_matches:
        current_entry["age_sw_stakes"].append(match.group().strip())

    # Update the previous row's dam and damsire for the next iteration
    previous_dam = current_entry["dam"]
    previous_damsire = current_entry.get("damsire", None)

# Append the last entry
if any(current_entry.values()):
    entries.append(current_entry)

# Process dam inheritance
for i, entry in enumerate(entries):
    if not entry.get("dam"):
        previous_female = find_previous_female(entries, i)
        if previous_female:
            entry["dam"] = previous_female

# Process stakes wins
expanded_entries = process_sw_stakes_wins(entries)

# Print identified dams and damsires
print("\nIdentified Dams and Damsires:")
for entry in expanded_entries:
    print(f"Horse: {entry.get('name')}, Dam: {entry.get('dam')}, Damsire: {entry.get('damsire')}")

# Save to CSV
output_file = '/Users/theoxforddeveloper/Desktop/Parsing_repo/structured_csv_files/Abdan_csv.csv'
with open(output_file, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    # Write header
    csv_writer.writerow([
        "name", "year", "colour", "sex", "sire", "dam", "damsire", "starts", "wins", 
        "earnings", "foals", "rnrs", "wnrs", "SW", "career length", "Age of SW", "Stakes Win"
    ])
    # Write rows
    for entry in expanded_entries:
        csv_writer.writerow([
            entry.get("name"), entry.get("year"), entry.get("colour"), entry.get("sex"),
            entry.get("sire"), entry.get("dam"), entry.get("damsire"), entry.get("starts"),
            entry.get("wins"), entry.get("earnings"), entry.get("foals"), entry.get("rnrs"),
            entry.get("wnrs"), entry.get("SW"), entry.get("career length"),
            entry.get("Age of SW"), entry.get("Stakes Win")
        ])

print(f"\nData saved to {output_file}")