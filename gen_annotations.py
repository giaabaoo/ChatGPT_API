import json
import re
import csv
import pdb

def process_explanation(explanation):
    summary = re.search(r'SUMMARY: (.*)\n', explanation).group(1)
    changepoints = re.findall(r'CHANGEPOINT \d+ \((.*?)\): (.*?)\n', explanation)
    changepoints_dict = {i: {'segment_id': segment_id, 'comment': comment} for i, (segment_id, comment) in enumerate(changepoints, start=1)}

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

def calculate_timestamp(text, full_text_msg):
    start_char = full_text_msg.index(text)
    return start_char

if __name__ == "__main__":
    with open('synCP_dials.json', 'r') as f:
        syn_dials = json.load(f)

    # Define the output file name and header
    output_file = 'augment_data/text_augment_annotations.csv'
    fieldnames = ['file_id', 'segment_id', 'start', 'end', 'type', 'duration' , 'changepoint_timestamp', 'msg', 'emotion','comments', 'summary']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for file_id, data in syn_dials.items():
            dialogue = data['dialogue']
            explanation = data['explanation']
            
            # Split the string by '\n'
            lines = [line.strip() for line in dialogue.split('\n')]

            # Extract the sentences that start with the segment ID and the speaker name
            sentences = [re.sub(r'\s*\[.*?\]\s*', '', line.split(': ')[1]) for line in lines if line.startswith('AUGMENT')]

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
                text = string.split(": ")[1].split(" [")[0]
                emotion = string.split("[")[1].split(",")[0]

                start = int(re.search(r'\d+', segment_id).group())
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
                    'emotion': emotion,
                    'comments': '',
                    'summary': summary
                }

                # Check if the segment is a changepoint and update the data accordingly
                if segment_id in positive_segment_ids:
                    index = positive_segment_ids.index(segment_id) + 1
                    changepoint = changepoints[index]


                    segment_data['comments'] = changepoint['comment']
                    segment_data['changepoint_timestamp'] = calculate_timestamp(text, full_text_msg)

                # Write the segment data to the output file
                writer.writerow(segment_data)

                print(f"Segment {segment_id} in file {file_id} written to {output_file}")

