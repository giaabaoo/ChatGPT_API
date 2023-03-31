import json
import re
import csv
from googletrans import Translator
from deep_translator import GoogleTranslator
import concurrent.futures
import os
import pandas as pd
import pdb

def process_explanation(explanation):
    summary = re.search(r'SUMMARY: (.*)\n', explanation).group(1)
    changepoints = re.findall(r'CHANGEPOINT \d+ \((.*?)\)\s*\((.*?)=(\d+)\): (.+)', explanation)
    changepoints_dict = {i+1: {'segment_id': segment_id, 'impact_scalar': int(impact_scalar), 'comment': comment} for i, (segment_id, field_name, impact_scalar, comment) in enumerate(changepoints)}

    return {"summary": summary, "changepoints": changepoints_dict}

def extract_string_results(string):
    regex_pattern = r'^(.*?) \| (.*?): (.*?) \[(.*?), (\d+)\]$'
    matches = re.findall(regex_pattern, string, flags=re.MULTILINE)

    if not matches:
        return "None", "None", "None", "none", 0

    match = matches[0]
    return match[0], match[1], match[2], match[3], int(match[4])

def process_dialogue(dialogue):
    lines = dialogue.split('\n')
    return [dict(zip(['segment_id', 'speaker', 'sentence_text', 'emotion', 'CP_label'], extract_string_results(line))) for line in lines]

def translate_text(text):
    translated_text = GoogleTranslator(source='auto', target='en').translate(text)

    # Returns the translated text
    return translated_text

def read_existing_segment_ids(filename):
    if not os.path.exists(filename):
        return set()

    with open(filename, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if set(reader.fieldnames) != set(fieldnames):
            # Header row doesn't match expected fields, so write a new header row
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            return set()

        # Read the segment IDs from the file
        existing_segment_ids = set()
        for row in reader:
            existing_segment_ids.add((row['file_id'], row['segment_id']))

    return existing_segment_ids


def process_file(file_id, data, output_file, existing_segment_ids):
    dialogue = data['dialogue']
    explanation = data['explanation']

    lines = [line.strip() for line in dialogue.split('\n')]
    sentences = [re.sub(r'\s*\[.*?\]\s*', '', line.split(': ')[1]) for line in dialogue.split('\n') if line.startswith('A')]
    full_text_msg = ' '.join(sentences)

    explanation_data = process_explanation(explanation)
    summary = explanation_data['summary']
    changepoints = explanation_data['changepoints']
    
    segments = re.findall(r'(\S+_\d+ \| \d+:.*?)\n', dialogue)
    
    
    positive_segment_ids = [cp['segment_id'] for cp in changepoints.values()]

    for i, segment in enumerate(segments, start=1):
        segment_id, string = segment.split(' | ')
        text = re.search(r':\s*(.+?)\s*\[', string).group(1)
        emotion = string.split("[")[1].split(",")[0]
        
        try:
            english_sentence = translate_text(text)
        except Exception as e:
            english_sentence = "Translation failed!"

        start = full_text_msg.find(text)
        end = start + len(text) - 1

        segment_data = {
            'file_id': file_id,
            'segment_id': segment_id,
            'start': start,
            'end': end,
            'type': 'text',
            'duration': len(text),
            'changepoint_timestamp': -1,
            'msg': text,
            'translation' : english_sentence,
            'impact_scalar' : 0,
            'emotion': emotion,
            'comments': '',
            'summary': summary
        }

        if segment_id in positive_segment_ids:
            index = positive_segment_ids.index(segment_id) + 1
            changepoint = changepoints[index]
            
            segment_data['comments'] = changepoint['comment']
            segment_data['impact_scalar'] = changepoint['impact_scalar']
            segment_data['changepoint_timestamp'] = start

        if (file_id, segment_id) in existing_segment_ids:
            print(f"Segment {segment_id} in file {file_id} already exists. Skipping...")
            continue

        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(segment_data)
            print(f"Segment {segment_id} in file {file_id} written to {output_file}")


if __name__ == "__main__":
    with open('synCP_dials.json', 'r') as f:
        syn_dials = json.load(f)

    output_file = 'augment_data_zh/text_augment_annotations.csv'
    fieldnames = ['file_id', 'segment_id', 'start', 'end', 'type', 'duration' , 'changepoint_timestamp', 'msg', 'translation', 'impact_scalar', 'emotion','comments', 'summary']

    existing_segment_ids = read_existing_segment_ids(output_file)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for file_id, data in syn_dials.items():
            futures.append(executor.submit(process_file, file_id, data, output_file, existing_segment_ids))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred while processing a file: {e}")


    # Read the CSV file
    df = pd.read_csv('augment_data_zh/text_augment_annotations.csv')

    # Sort by the 'segment_id' column
    df_sorted = df.sort_values(by=['segment_id'])

    # Save the sorted CSV file
    df_sorted.to_csv('augment_data_zh/text_augment_annotations.csv', index=False)