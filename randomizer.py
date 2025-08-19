# scripts/randomizer.py
import os
import re
from random import choice

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

MANUAL_FILES_TO_RANDOMIZE = [
    "src/data/wild_encounters.h",
    "src/data/trainer_parties.h",
    "src/oak_speech.c",
    "src/data/ingame_trades.h",
    "src/field_specials.c"
]
AUTO_TARGET_FILENAME = "scripts.inc"

# Species that should NEVER be the RESULT of a randomization (e.g., a Pidgey can't become an Unown).
POOL_EXCLUSIONS = [
    "SPECIES_NONE",
    "SPECIES_EGG",
    "SPECIES_UNOWN",
]
for i in range(ord('B'), ord('Z') + 1):
    POOL_EXCLUSIONS.append(f"SPECIES_OLD_UNOWN_{chr(i)}")
    POOL_EXCLUSIONS.append(f"SPECIES_UNOWN_{chr(i)}")
POOL_EXCLUSIONS.append("SPECIES_UNOWN_EMARK")
POOL_EXCLUSIONS.append("SPECIES_UNOWN_QMARK")

# Species that should NEVER be CHANGED if found in a file. This is a much smaller, more critical list.
PROTECTED_SPECIES = [
    "SPECIES_NONE",
    "SPECIES_EGG",
]

ORIGINAL_STARTERS = [
    "SPECIES_BULBASAUR",
    "SPECIES_CHARMANDER",
    "SPECIES_SQUIRTLE"
]
SPECIES_HEADER = os.path.join(PROJECT_ROOT, "include", "constants", "species.h")

# --- Main Logic ---

def find_all_target_files(root_directory, filename):
    target_files = []
    for dirpath, _, filenames in os.walk(root_directory):
        if filename in filenames:
            full_path = os.path.join(dirpath, filename)
            target_files.append(full_path)
    return target_files

def get_all_species():
    """Reads the species header file and returns a list of all valid species names."""
    species_list = []
    species_pattern = re.compile(r"#define (SPECIES_\w+)\s")
    with open(SPECIES_HEADER, "r", encoding="utf-8") as f:
        for line in f:
            match = species_pattern.match(line)
            if match:
                species_name = match.group(1)
                # Use the broader POOL_EXCLUSIONS list here
                if species_name not in POOL_EXCLUSIONS:
                    species_list.append(species_name)
    print(f"Found {len(species_list)} valid Pokémon species to use for randomization.")
    return species_list

def randomize_species_in_file(filepath, species_list, starter_map):
    """Randomizes species, using the starter_map for consistency."""
    
    encounter_pattern = re.compile(r"\bSPECIES_\w+\b")
    
    def replacement_logic(match):
        original_species = match.group(0)
        if original_species in starter_map:
            return starter_map[original_species]
        
        # Use the smaller PROTECTED_SPECIES list here
        if original_species in PROTECTED_SPECIES:
            return original_species
            
        return choice(species_list)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        relative_path = os.path.relpath(filepath, PROJECT_ROOT)
        if "// RANDOMIZER_START" in content:
            print(f"-> Markers found in {relative_path}. Processing marked sections...")
            lines = content.splitlines(keepends=True)
            new_lines = []
            randomize_enabled = False
            for line in lines:
                if "// RANDOMIZER_START" in line:
                    randomize_enabled = True
                elif "// RANDOMIZER_END" in line:
                    randomize_enabled = False
                
                if randomize_enabled and "// RANDOMIZER_START" not in line:
                    new_lines.append(encounter_pattern.sub(replacement_logic, line))
                else:
                    new_lines.append(line)
            final_content = "".join(new_lines)
        else:
            print(f"-> No markers found in {relative_path}. Processing entire file...")
            final_content = encounter_pattern.sub(replacement_logic, content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
            
    except FileNotFoundError:
        print(f"   [ERROR] File not found: {relative_path}. Skipping.")
    except Exception as e:
        print(f"   [ERROR] An unexpected error occurred with {relative_path}: {e}")

# --- Script Execution ---

if __name__ == "__main__":
    
    all_species = get_all_species()
    if all_species:
        print("\n--- Generating Consistent Starter Map ---")
        starter_map = {
            starter: choice(all_species) for starter in ORIGINAL_STARTERS
        }
        for original, new in starter_map.items():
            print(f"{original} -> {new}")
        print("------------------------------------")
        
        manual_files_full_path = [os.path.join(PROJECT_ROOT, path) for path in MANUAL_FILES_TO_RANDOMIZE]
        auto_discovered_files = find_all_target_files(PROJECT_ROOT, AUTO_TARGET_FILENAME)
        combined_files = manual_files_full_path + auto_discovered_files
        unique_files_to_process = sorted(list(set(combined_files)))
        
        if not unique_files_to_process:
            print(f"\nNo files found to process. Nothing to do.")
        else:
            print(f"\nFound {len(unique_files_to_process)} total unique files to process.")
            print("\nStarting randomization process...")
            for file_path in unique_files_to_process:
                randomize_species_in_file(file_path, all_species, starter_map)
            print("\nRandomization complete!")