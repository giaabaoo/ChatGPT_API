import json
import re
from pathlib import Path
import pdb
from tqdm import tqdm

if __name__ == "__main__":
    with open('synCP_dials.json', 'r') as f:
        syn_dials = json.load(f)

    folder_name = 'augment_data/text_augment'
    Path(folder_name).mkdir(parents=True, exist_ok=True)

    for file_name in tqdm(syn_dials.keys()):
            
        dialogue = syn_dials[file_name]["dialogue"]
        # Remove the square brackets, their contents, and the final period from the dialogue
        dialogue = re.sub(r'\[.*?\]', '', dialogue).rstrip('.').replace('AUGMENT', '\nAUGMENT').replace('\n\n', '\n')
        
        # Write the dialogue to a text file
        file_path = Path(folder_name) / f"{file_name}.txt"
        with open(file_path, 'w') as f:
            f.write(dialogue)
