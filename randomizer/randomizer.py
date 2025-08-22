# scripts/randomizer.py
import os
import re
import json
from random import choice, shuffle
import pandas as pd

# --- Configuration ---
# Corrected PROJECT_ROOT to point to the parent directory of this script's location.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -- Species Config --
USE_BST_RANDOMIZATION = True  # SET TO FALSE to use the original "fully random" species method.
# This script now prioritizes pokemon.csv. It will only fall back to base_stats.h if the CSV is not found.
CSV_STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pokemon.csv")
BASE_STATS_HEADER = os.path.join(PROJECT_ROOT, "src", "data", "pokemon", "base_stats.h") # Fallback only
BST_SIMILARITY_RANGE = 75     # The +/- range for what's considered a "similar" BST.

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
ABILITY_DATA_FILE = os.path.join(PROJECT_ROOT, "src", "data", "pokemon", "species_info.h")
PROTECTED_ABILITIES = [
    "ABILITY_NONE",
    "ABILITY_WONDER_GUARD", # Excluded to prevent unbeatable random Pokémon
]

# -- Item Config --
ITEM_JSON_FILE = os.path.join(PROJECT_ROOT, "src", "data", "items.json")
MANUAL_ITEM_FILES = [
    "src/field_specials.c",
    "src/script_menu.c",
    "src/daycare.c"
]
# Commands on the same line as an ITEM_ that will PREVENT randomization. Case-insensitive.
FORBIDDEN_ITEM_COMMANDS = [
    "addhiddenitem",
]
# Any other specific files you want to prevent from being item-randomized can be added here.
EXCLUDED_ITEM_FILES = []
ITEM_POOL_EXCLUSIONS = ["ITEM_NONE", "ITEM_BERRY_POUCH", "ITEM_TM_CASE"]
PROTECTED_ITEMS = ["ITEM_NONE"]


# --- Main Logic ---

def find_all_target_files(root_directory, filename):
    target_files = []
    for dirpath, _, filenames in os.walk(root_directory):
        if filename in filenames:
            target_files.append(os.path.join(dirpath, filename))
    return target_files

# --- Species Functions ---

def format_name_to_species_constant(name):
    """Converts a Pokémon name from the CSV to a SPECIES_CONSTANT format."""
    if "Nidoran♀" in name: return "SPECIES_NIDORAN_F"
    if "Nidoran♂" in name: return "SPECIES_NIDORAN_M"
    if "Farfetch'd" in name: return "SPECIES_FARFETCHD"
    if "Mr. Mime" in name: return "SPECIES_MR_MIME"
    if "Mime Jr." in name: return "SPECIES_MIME_JR"
    name = re.sub(r'(?<!^)(?<!\s)([A-Z])', r' \1', name)
    name = name.replace("Mega ", "MEGA_").replace("Primal ", "PRIMAL_").replace("Alolan ", "ALOLAN_").replace("Galarian ", "GALARIAN_")
    name = name.replace(" ", "_").replace("-", "_").replace(".", "").replace("'", "")
    return "SPECIES_" + name.upper()

def get_species_bst_map_from_csv():
    """Parses pokemon.csv to create a map of {species: BST}."""
    try:
        df = pd.read_csv(CSV_STATS_FILE)
    except FileNotFoundError:
        print(f"   [INFO] CSV file not found at {CSV_STATS_FILE}. Will try to fall back to base_stats.h.")
        return None
    valid_species = set(get_all_species())
    if not valid_species:
        print("   [ERROR] Could not read species from species.h. Cannot map BSTs.")
        return None
    bst_map = {}
    for _, row in df.iterrows():
        name, bst = row['Name'], row['Total']
        species_constant = format_name_to_species_constant(name)
        if species_constant in valid_species:
            bst_map[species_constant] = bst
    mapped_count, total_valid = len(bst_map), len(valid_species)
    print(f"Read BST from {os.path.basename(CSV_STATS_FILE)}. Matched {mapped_count}/{total_valid} species from your project.")
    if mapped_count < total_valid:
        print("   [INFO] Some species in your project might not be in the CSV or have non-standard names.")
    return bst_map

def get_species_bst_map_from_header():
    """Fallback function to parse base_stats.h if the CSV is not available."""
    bst_map = {}
    try:
        with open(BASE_STATS_HEADER, "r", encoding="utf-8") as f: content = f.read()
    except FileNotFoundError:
        print(f"   [ERROR] Base stats file not found at {BASE_STATS_HEADER}. Aborting BST randomization.")
        return None
    species_blocks = re.finditer(r"\[(SPECIES_\w+)\] =(.+?)\};", content, re.DOTALL)
    stat_names = ["baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense"]
    for block in species_blocks:
        species_name, stats_text = block.group(1), block.group(2)
        if species_name in POOL_EXCLUSIONS: continue
        total_bst, found_stats = 0, 0
        for stat in stat_names:
            match = re.search(rf"\.{stat}\s*=\s*(\d+)", stats_text)
            if match:
                total_bst += int(match.group(1))
                found_stats += 1
        if found_stats == len(stat_names): bst_map[species_name] = total_bst
    print(f"Found and calculated BST for {len(bst_map)} valid Pokémon species from {os.path.basename(BASE_STATS_HEADER)}.")
    return bst_map

def build_bst_swap_pools(bst_map, similarity_range):
    """Creates a dictionary mapping each species to a list of other species with a similar BST."""
    swap_pools = {}
    for species1, bst1 in bst_map.items():
        pool = [species2 for species2, bst2 in bst_map.items() if abs(bst1 - bst2) <= similarity_range]
        swap_pools[species1] = pool
    print(f"Built BST swap pools. For example, SPECIES_BULBASAUR ({bst_map.get('SPECIES_BULBASAUR', 0)}) has {len(swap_pools.get('SPECIES_BULBASAUR', []))} similar-BST partners.")
    return swap_pools

def get_all_species():
    """Gets all species from species.h. Now also used to validate names from the CSV."""
    species_list = []
    try:
        with open(SPECIES_HEADER, "r", encoding="utf-8") as f:
            species_pattern = re.compile(r"#define (SPECIES_\w+)\s")
            for line in f:
                match = species_pattern.match(line)
                if match and match.group(1) not in POOL_EXCLUSIONS:
                    species_list.append(match.group(1))
    except FileNotFoundError:
        print(f"   [ERROR] species.h not found at {SPECIES_HEADER}. This file is essential.")
        return []
    return species_list

def randomize_species_in_file(filepath, starter_map, bst_swap_pools=None, fallback_pool=None):
    encounter_pattern = re.compile(r"\bSPECIES_\w+\b")
    def replacement_logic(match):
        original_species = match.group(0)
        if original_species in starter_map: return starter_map[original_species]
        if original_species in PROTECTED_SPECIES: return original_species
        if bst_swap_pools:
            swap_pool = bst_swap_pools.get(original_species)
            if swap_pool: return choice(swap_pool)
            else: return original_species
        return choice(fallback_pool) if fallback_pool else original_species
    try:
        with open(filepath, "r", encoding="utf-8") as f: content = f.read()
        relative_path = os.path.relpath(filepath, PROJECT_ROOT)
        if "// RANDOMIZER_START" in content:
            print(f"-> Markers found in {relative_path}. Processing marked sections...")
            lines, new_lines, randomize_enabled = content.splitlines(True), [], False
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

# --- Ability & Item Functions ---

def get_all_abilities():
    ability_list = []
    try:
        with open(ABILITY_HEADER, "r", encoding="utf-8") as f:
            ability_pattern = re.compile(r"#define (ABILITY_\w+)\s")
            for line in f:
                match = ability_pattern.match(line)
                if match and match.group(1) not in PROTECTED_ABILITIES:
                    ability_list.append(match.group(1))
        print(f"Found {len(ability_list)} valid abilities to use for randomization.")
    except FileNotFoundError:
        print(f"   [ERROR] abilities.h not found at {ABILITY_HEADER}. Skipping ability randomization.")
    return ability_list

def randomize_abilities(filepath, ability_pool):
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

def get_all_items():
    """Parses the items.json file and returns a pool of REGULAR items only."""
    regular_pool = []
    try:
        with open(ITEM_JSON_FILE, "r", encoding="utf-8") as f:
            item_data = json.load(f)
    except FileNotFoundError:
        print(f"   [ERROR] Item data not found at {ITEM_JSON_FILE}. Aborting item randomization.")
        return []
    except json.JSONDecodeError:
        print(f"   [ERROR] Could not parse {ITEM_JSON_FILE}. It might be malformed. Aborting item randomization.")
        return []

    item_list = item_data.get("items", [])
    if not item_list:
        print(f"   [ERROR] Could not find the 'items' list in {os.path.basename(ITEM_JSON_FILE)}. Aborting.")
        return []

    for item in item_list:
        if not isinstance(item, dict): continue
        item_id = item.get("itemId")
        if not item_id or item_id in ITEM_POOL_EXCLUSIONS or item_id.startswith("ITEM_HM"):
            continue
        # CRITICAL CHANGE: Only add non-key items to the pool
        if item.get("pocket") != "POCKET_KEY_ITEMS":
            regular_pool.append(item_id)
            
    print(f"Found {len(regular_pool)} regular items to use in the shuffle pool.")
    return regular_pool

def apply_item_shuffle(filepath, item_map):
    """Replaces items in a file based on the pre-shuffled item_map."""
    relative_path = os.path.relpath(filepath, PROJECT_ROOT)
    print(f"-> Shuffling items in {relative_path}...")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            def line_replacer(match):
                original_item = match.group(0)
                if original_item in item_map and item_map[original_item]:
                    return item_map[original_item].pop(0)
                return original_item

            new_line = re.sub(r'\bITEM_\w+\b', line_replacer, line)
            new_lines.append(new_line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(new_lines))
            
    except FileNotFoundError: print(f"   [ERROR] File not found: {relative_path}. Skipping.")
    except Exception as e: print(f"   [ERROR] An unexpected error occurred with {relative_path}: {e}")

# --- Script Execution ---

if __name__ == "__main__":
    # --- Species Randomization ---
    starter_map, bst_swap_pools, fallback_pool = {}, None, []
    
    print("\n--- Initializing Species Randomization ---")
    if USE_BST_RANDOMIZATION:
        print("Mode: Similar BST")
        species_bst_map = get_species_bst_map_from_csv()
        if species_bst_map is None:
            species_bst_map = get_species_bst_map_from_header()
        
        if species_bst_map:
            bst_swap_pools = build_bst_swap_pools(species_bst_map, BST_SIMILARITY_RANGE)
            for starter in ORIGINAL_STARTERS:
                pool = bst_swap_pools.get(starter)
                if pool: starter_map[starter] = choice(pool)
                else: starter_map[starter] = starter
    
    if not starter_map:
        print("Mode: Fully Random")
        fallback_pool = get_all_species()
        if fallback_pool:
            starter_map = {starter: choice(fallback_pool) for starter in ORIGINAL_STARTERS}

    if starter_map:
        print("\n--- Generating Consistent Starter Map ---")
        for original, new in starter_map.items(): print(f"{original} -> {new}")
        print("------------------------------------")
        
        manual_files_full_path = [os.path.join(PROJECT_ROOT, path) for path in MANUAL_FILES_TO_RANDOMIZE]
        auto_discovered_files = find_all_target_files(PROJECT_ROOT, AUTO_TARGET_FILENAME)
        unique_files_to_process = sorted(list(set(manual_files_full_path + auto_discovered_files)))
        
        if unique_files_to_process:
            print(f"\nFound {len(unique_files_to_process)} total unique files to process for species randomization.")
            print("\n--- Starting Species Randomization ---")
            for file_path in unique_files_to_process:
                randomize_species_in_file(file_path, starter_map, bst_swap_pools, fallback_pool)
            print("------------------------------------")
        else:
            print("\nNo species files found to process.")

    # --- Ability Randomization ---
    all_abilities = get_all_abilities()
    if all_abilities:
        print("\n--- Starting Ability Randomization ---")
        randomize_abilities(ABILITY_DATA_FILE, all_abilities)
        print("------------------------------------")

    # --- Item SHUFFLE Randomization (Regular Items Only) ---
    regular_item_pool = get_all_items()
    if regular_item_pool:
        manual_item_files_full_path = [os.path.join(PROJECT_ROOT, path) for path in MANUAL_ITEM_FILES]
        auto_discovered_item_files = find_all_target_files(PROJECT_ROOT, AUTO_TARGET_FILENAME)
        
        unique_item_files = set(manual_item_files_full_path + auto_discovered_item_files)
        
        # --- DYNAMIC MART & DEPT STORE EXCLUSION ---
        excluded_files_full_path = {os.path.join(PROJECT_ROOT, path) for path in EXCLUDED_ITEM_FILES}
        maps_path = os.path.join(PROJECT_ROOT, 'data', 'maps')
        if os.path.isdir(maps_path):
            for dirpath, _, filenames in os.walk(maps_path):
                if ('mart' in dirpath.lower() or 'CeladonCity_DepartmentStore_' in dirpath) and AUTO_TARGET_FILENAME in filenames:
                    excluded_files_full_path.add(os.path.join(dirpath, AUTO_TARGET_FILENAME))

        final_item_files_to_process = sorted([f for f in unique_item_files if os.path.normpath(f) not in excluded_files_full_path])

        if final_item_files_to_process:
            print("\n--- Preparing for Item Shuffle (Regular Items Only) ---")
            
            # 1. GATHER all REGULAR item locations
            regular_locations = []
            item_pattern = re.compile(r"\bITEM_\w+\b")
            forbidden_lower = [cmd.lower() for cmd in FORBIDDEN_ITEM_COMMANDS]

            for file_path in final_item_files_to_process:
                with open(file_path, "r", encoding='utf-8') as f:
                    for line in f:
                        if any(cmd in line.lower() for cmd in forbidden_lower):
                            continue
                        
                        for match in item_pattern.finditer(line):
                            item = match.group(0)
                            if item in regular_item_pool:
                                regular_locations.append(item)

            print(f"Found {len(regular_locations)} regular item locations to shuffle.")

            # 2. CREATE the shuffled pool for replacement
            # This ensures a 1-to-1 swap of all found regular items
            shuffled_pool = regular_locations[:]
            shuffle(shuffled_pool)
            
            # 3. Create a map of {Original_Item: [List_Of_Shuffled_Items]}
            item_map = {}
            for i, original_item in enumerate(regular_locations):
                if original_item not in item_map:
                    item_map[original_item] = []
                item_map[original_item].append(shuffled_pool[i])

            # 4. Process the files, applying the shuffle map
            print("\n--- Starting Item Shuffling ---")
            for file_path in final_item_files_to_process:
                apply_item_shuffle(file_path, item_map)
            print("------------------------------------")
        else:
            print("\nNo item files found to process.")
    
    print("\nFull randomization complete! ✅")