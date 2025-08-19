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
EXCLUDED_SPECIES = [
    "SPECIES_NONE",
    "SPECIES_EGG",
]

# The original Kanto starters that need to be consistently replaced
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
    species_list = []
    species_pattern = re.compile(r"#define (SPECIES_\w+)\s")
    with open(SPECIES_HEADER, "r", encoding="utf-8") as f:
        for line in f:
            match = species_pattern.match(line)
            if match:
                species_name = match.group(1)
                if species_name not in EXCLUDED_SPECIES:
                    species_list.append(species_name)
    print(f"Found {len(species_list)} valid Pokémon species to use for randomization.")
    return species_list

def randomize_species_in_file(filepath, species_list, starter_map):
    """Randomizes species, using the starter_map for consistency."""
    
    encounter_pattern = re.compile(r"\bSPECIES_\w+\b")
    
    def replacement_logic(match):
        original_species = match.group(0)
        # 1. Check if the found species is one of the original starters.
        if original_species in starter_map:
            return starter_map[original_species]
        
        # 2. If not a starter, check if it should be excluded entirely.
        if original_species in EXCLUDED_SPECIES:
            return original_species
            
        # 3. Otherwise, it's a normal species, so randomize it.
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
        # Create the consistent starter map ONE TIME before processing any files.
        print("\n--- Generating Consistent Starter Map ---")
        starter_map = {
            starter: choice(all_species) for starter in ORIGINAL_STARTERS
        }
        for original, new in starter_map.items():
            print(f"{original} -> {new}")
        print("------------------------------------")
        
        # Combine manual and auto-discovered file lists
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
                # Pass the consistent starter_map to the function
                randomize_species_in_file(file_path, all_species, starter_map)
            print("\nRandomization complete!")