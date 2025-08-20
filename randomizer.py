# scripts/randomizer.py
import os
import re
from random import choice

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# -- Species Config --
MANUAL_FILES_TO_RANDOMIZE = [
    "src/data/wild_encounters.h",
    "src/data/trainer_parties.h",
    "src/oak_speech.c",
    "src/data/ingame_trades.h",
    "src/field_specials.c"
]
AUTO_TARGET_FILENAME = "scripts.inc"
POOL_EXCLUSIONS = [ "SPECIES_NONE", "SPECIES_EGG", "SPECIES_UNOWN" ]
for i in range(ord('B'), ord('Z') + 1):
    POOL_EXCLUSIONS.append(f"SPECIES_OLD_UNOWN_{chr(i)}")
    POOL_EXCLUSIONS.append(f"SPECIES_UNOWN_{chr(i)}")
POOL_EXCLUSIONS.append("SPECIES_UNOWN_EMARK")
POOL_EXCLUSIONS.append("SPECIES_UNOWN_QMARK")
PROTECTED_SPECIES = [ "SPECIES_NONE", "SPECIES_EGG" ]
ORIGINAL_STARTERS = [ "SPECIES_BULBASAUR", "SPECIES_CHARMANDER", "SPECIES_SQUIRTLE" ]
SPECIES_HEADER = os.path.join(PROJECT_ROOT, "include", "constants", "species.h")

# -- Ability Config --
ABILITY_HEADER = os.path.join(PROJECT_ROOT, "include", "constants", "abilities.h")
# This path has been corrected to point to the file you provided.
ABILITY_DATA_FILE = os.path.join(PROJECT_ROOT, "src", "data", "pokemon", "species_info.h")

PROTECTED_ABILITIES = [
    "ABILITY_NONE",
    "ABILITY_WONDER_GUARD", # Excluded to prevent unbeatable random Pokémon
]

# --- Main Logic ---

def find_all_target_files(root_directory, filename):
    target_files = []
    for dirpath, _, filenames in os.walk(root_directory):
        if filename in filenames:
            target_files.append(os.path.join(dirpath, filename))
    return target_files

def get_all_species():
    species_list = []
    species_pattern = re.compile(r"#define (SPECIES_\w+)\s")
    with open(SPECIES_HEADER, "r", encoding="utf-8") as f:
        for line in f:
            match = species_pattern.match(line)
            if match and match.group(1) not in POOL_EXCLUSIONS:
                species_list.append(match.group(1))
    print(f"Found {len(species_list)} valid Pokémon species to use for randomization.")
    return species_list

def randomize_species_in_file(filepath, species_list, starter_map):
    encounter_pattern = re.compile(r"\bSPECIES_\w+\b")
    def replacement_logic(match):
        original_species = match.group(0)
        if original_species in starter_map: return starter_map[original_species]
        if original_species in PROTECTED_SPECIES: return original_species
        return choice(species_list)
    try:
        with open(filepath, "r", encoding="utf-8") as f: content = f.read()
        relative_path = os.path.relpath(filepath, PROJECT_ROOT)
        if "// RANDOMIZER_START" in content:
            print(f"-> Markers found in {relative_path}. Processing marked sections...")
            lines, new_lines, randomize_enabled = content.splitlines(keepends=True), [], False
            for line in lines:
                if "// RANDOMIZER_START" in line: randomize_enabled = True
                elif "// RANDOMIZER_END" in line: randomize_enabled = False
                new_lines.append(encounter_pattern.sub(replacement_logic, line) if randomize_enabled and "// RANDOMIZER_START" not in line else line)
            final_content = "".join(new_lines)
        else:
            print(f"-> No markers found in {relative_path}. Processing entire file...")
            final_content = encounter_pattern.sub(replacement_logic, content)
        with open(filepath, "w", encoding="utf-8") as f: f.write(final_content)
    except FileNotFoundError: print(f"   [ERROR] File not found: {relative_path}. Skipping.")
    except Exception as e: print(f"   [ERROR] An unexpected error occurred with {relative_path}: {e}")

# --- New Ability Functions ---

def get_all_abilities():
    """Reads abilities.h and returns a list of all valid abilities for randomization."""
    ability_list = []
    ability_pattern = re.compile(r"#define (ABILITY_\w+)\s")
    with open(ABILITY_HEADER, "r", encoding="utf-8") as f:
        for line in f:
            match = ability_pattern.match(line)
            if match and match.group(1) not in PROTECTED_ABILITIES:
                ability_list.append(match.group(1))
    print(f"Found {len(ability_list)} valid abilities to use for randomization.")
    return ability_list

def randomize_abilities(filepath, ability_pool):
    """Reads the species_info.h file and randomizes the abilities for each Pokémon."""
    print(f"-> Randomizing abilities in {os.path.basename(filepath)}...")
    ability_pattern = re.compile(r"\bABILITY_\w+\b")
    def replacement_logic(match):
        original_ability = match.group(0)
        if original_ability in PROTECTED_ABILITIES: return original_ability
        return choice(ability_pool)
    try:
        with open(filepath, "r", encoding="utf-8") as f: content = f.read()
        final_content = ability_pattern.sub(replacement_logic, content)
        with open(filepath, "w", encoding="utf-8") as f: f.write(final_content)
    except FileNotFoundError: print(f"   [ERROR] File not found: {filepath}. Skipping.")
    except Exception as e: print(f"   [ERROR] An unexpected error occurred with {filepath}: {e}")

# --- Script Execution ---

if __name__ == "__main__":
    # --- Species Randomization ---
    all_species = get_all_species()
    if all_species:
        print("\n--- Generating Consistent Starter Map ---")
        starter_map = {starter: choice(all_species) for starter in ORIGINAL_STARTERS}
        for original, new in starter_map.items(): print(f"{original} -> {new}")
        print("------------------------------------")
        manual_files_full_path = [os.path.join(PROJECT_ROOT, path) for path in MANUAL_FILES_TO_RANDOMIZE]
        auto_discovered_files = find_all_target_files(PROJECT_ROOT, AUTO_TARGET_FILENAME)
        unique_files_to_process = sorted(list(set(manual_files_full_path + auto_discovered_files)))
        if unique_files_to_process:
            print(f"\nFound {len(unique_files_to_process)} total unique files to process for species randomization.")
            print("\n--- Starting Species Randomization ---")
            for file_path in unique_files_to_process:
                randomize_species_in_file(file_path, all_species, starter_map)
            print("------------------------------------")
        else:
            print("\nNo species files found to process.")

    # --- Ability Randomization ---
    all_abilities = get_all_abilities()
    if all_abilities:
        print("\n--- Starting Ability Randomization ---")
        randomize_abilities(ABILITY_DATA_FILE, all_abilities)
        print("------------------------------------")
    
    print("\nFull randomization complete!")