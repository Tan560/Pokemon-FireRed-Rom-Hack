# scripts/randomizer.py
import os
import re
from random import choice

# --- Configuration ---
# Get the absolute path of the directory this script is in (which is the project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# List of files to randomize. Add the relative paths of any other files you want to process here.
# For example, you might add "src/data/trainers.c" to randomize trainer parties.
FILES_TO_RANDOMIZE = [
    "src/data/wild_encounters.h",
    "src/data/trainer_parties.h",
    "src/field_specials.c"
]

SPECIES_HEADER = os.path.join(PROJECT_ROOT, "include", "constants", "species.h")

# --- Main Logic ---

def get_all_species():
    """Reads the species header file and returns a list of all valid species names."""
    species_list = []
    # This regex captures species names like "SPECIES_BULBASAUR"
    species_pattern = re.compile(r"#define (SPECIES_\w+)\s")
    
    with open(SPECIES_HEADER, "r", encoding="utf-8") as f:
        for line in f:
            match = species_pattern.match(line)
            if match:
                species_name = match.group(1)
                # Exclude placeholder/egg species
                if species_name not in ["SPECIES_NONE", "SPECIES_EGG"]:
                    species_list.append(species_name)
    
    print(f"Found {len(species_list)} valid Pokémon species.")
    return species_list

def randomize_species_in_file(filepath, species_list):
    """Reads a single file and replaces every SPECIES_ constant with a random one."""
    
    # This regex is the key. It finds any "SPECIES_" constant.
    encounter_pattern = re.compile(r"SPECIES_\w+")
    
    print(f"-> Randomizing file: {os.path.basename(filepath)}...")
    
    try:
        # Read the original content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Perform the replacement
        # The lambda function `lambda m: choice(species_list)` is called for every match `m`.
        new_content = encounter_pattern.sub(lambda m: choice(species_list), content)
        
        # Write the modified content back to the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
            
    except FileNotFoundError:
        print(f"   [ERROR] File not found: {filepath}. Skipping.")
    except Exception as e:
        print(f"   [ERROR] An unexpected error occurred with {filepath}: {e}")


# --- Script Execution ---

if __name__ == "__main__":
    
    all_species = get_all_species()
    if all_species:
        print("\nStarting randomization process...")
        for relative_path in FILES_TO_RANDOMIZE:
            # Construct the full path for each file
            full_path = os.path.join(PROJECT_ROOT, relative_path)
            randomize_species_in_file(full_path, all_species)
        print("\nRandomization complete!")