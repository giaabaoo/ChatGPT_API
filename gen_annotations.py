import json
import re
import csv
from googletrans import Translator
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
    # Create an instance of the Translator class
    translator = Translator()

    # Translate the text to English
    translated_text = translator.translate(text, src='zh-cn', dest='en').text
    

    # Returns the translated text
    return translated_text

if __name__ == "__main__":
    with open('synCP_dials.json', 'r') as f:
        syn_dials = json.load(f)

    # Define the output file name and header
    output_file = 'augment_data_zh/text_augment_annotations.csv'
    fieldnames = ['file_id', 'segment_id', 'start', 'end', 'type', 'duration' , 'changepoint_timestamp', 'msg', 'translation', 'impact_scalar', 'emotion','comments', 'summary']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for file_id, data in syn_dials.items():
            dialogue = data['dialogue']
            explanation = data['explanation']
            
            # Split the string by '\n'
            lines = [line.strip() for line in dialogue.split('\n')]

            # Extract the sentences that start with the segment ID and the speaker name
            sentences = [re.sub(r'\s*\[.*?\]\s*', '', line.split(': ')[1]) for line in dialogue.split('\n') if line.startswith('A')]
                
            # Join the sentences into a single string
            full_text_msg = ' '.join(sentences)

            # Process the explanation
            explanation_data = process_explanation(explanation)
            summary = explanation_data['summary']
            changepoints = explanation_data['changepoints']

            # Extract the segments from the dialogue
            segments = re.findall(r'(\S+_\d+ \| \d+:.*?)\n', dialogue)
            num_segments = len(segments)
            
            positive_segment_ids = [cp['segment_id'] for cp in changepoints.values()]

            for i, segment in enumerate(segments, start=1):
                # Extract the relevant information from the segment
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

                
                # Check if the segment is a changepoint and update the data accordingly
                if segment_id in positive_segment_ids:
                    index = positive_segment_ids.index(segment_id) + 1
                    changepoint = changepoints[index]
                    
                    segment_data['comments'] = changepoint['comment']
                    segment_data['impact_scalar'] = changepoint['impact_scalar']
                    segment_data['changepoint_timestamp'] = start

                # Write the segment data to the output file
                writer.writerow(segment_data)

                print(f"Segment {segment_id} in file {file_id} written to {output_file}")

