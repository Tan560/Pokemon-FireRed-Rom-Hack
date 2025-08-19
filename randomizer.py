# scripts/randomizer.py
import os
import re
from random import choice

# --- Configuration ---
# Get the absolute path of the directory this script is in (which is the project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# List of files to randomize.
FILES_TO_RANDOMIZE = [
    "src/data/wild_encounters.h",
    "src/data/trainer_parties.h",
    "src/oak_speech.c",
    "src/data/ingame_trades.h",
    "src/field_specials.c"
]

EXCLUDED_SPECIES = [
    "SPECIES_NONE",
    "SPECIES_EGG",
]

SPECIES_HEADER = os.path.join(PROJECT_ROOT, "include", "constants", "species.h")

# --- Main Logic ---

def get_all_species():
    """Reads the species header file and returns a list of all valid species names."""
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

def randomize_species_in_file(filepath, species_list):
    """
    Randomizes species in a file. If RANDOMIZER_START/END markers exist, only processes
    those sections. Otherwise, processes the entire file.
    """
    
    encounter_pattern = re.compile(r"\bSPECIES_\w+\b")
    
    def replacement_logic(match):
        """This function decides what to replace each match with."""
        original_species = match.group(0)
        if original_species in EXCLUDED_SPECIES:
            return original_species
        else:
            return choice(species_list)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if "// RANDOMIZER_START" in content:
            # --- Marker-based Logic ---
            print(f"-> Markers found in {os.path.basename(filepath)}. Processing marked sections...")
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
            # --- Whole-file Logic ---
            print(f"-> No markers found in {os.path.basename(filepath)}. Processing entire file...")
            final_content = encounter_pattern.sub(replacement_logic, content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
            
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
            full_path = os.path.join(PROJECT_ROOT, relative_path)
            randomize_species_in_file(full_path, all_species)
        print("\nRandomization complete!")