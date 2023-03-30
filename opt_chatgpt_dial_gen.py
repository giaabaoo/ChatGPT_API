import openai
import pandas as pd
import json
import argparse
import os
import pdb
from tqdm import tqdm
import re
import concurrent.futures

MAX_WORKERS = 4

def extract_string_results(string):
    regex_pattern = r'^(.*?) \| (.*?): (.*?) \[(.*?), (\d+)\]$'
    matches = re.findall(regex_pattern, string, flags=re.MULTILINE)

    if not matches:
        pdb.set_trace()
        return "None", "None", "None", "none", 0

    match = matches[0]
    return match[0], match[1], match[2], match[3], int(match[4])

def process_dialogue(dialogue):
    lines = dialogue.split('\n')
    return [dict(zip(['segment_id', 'speaker', 'sentence_text', 'emotion', 'CP_label'], extract_string_results(line))) for line in lines]

def process_explanation(explanation):
    summary = re.search(r'SUMMARY: (.*)\n', explanation).group(1)
    changepoints = re.findall(r'CHANGEPOINT \d+ \((.*?)\): (.*?)\n', explanation)
    changepoints_dict = {i: {'segment_id': segment_id, 'comment': comment} for i, (segment_id, comment) in enumerate(changepoints, start=1)}

    return {"summary": summary, "changepoints": changepoints_dict}

language = ['English']
emotions = ["fear", "anger", "joy", "sadness", "disgust","surprise", "trust", "anticipation","neutral"]

def generate_dialogue_and_explanation_async(k, api_key, model_engine):
    openai.api_key = api_key

    definition_text = f"A changepoint in a conversation is when there's \
    a shift in the topic, speaker, tone, or energy, which can lead to a change \
    in social norms or emotions. This shift can temporarily or permanently \
    affect the conversation's outcome, relationship, goals, emotions, and flow, \
    either positively or negatively in a significant way."
    
    first_prompt = f"With this definition \"{definition_text}\" \n \
    Generate a dialogue with up to 20 turns of text messages between two people \
    (family, friends, acquaintances) about a topic (on a discussion forum or SMS app) \
    (can be the start of conversation or the middle of conversation). \
    For each line, annotate STRICTLY at the end the emotion of the line with the emotions \
    from this list {emotions} (use emotions from this list only) \
    and label 1 for CP and label 0 for non-CP. It should \
    have the document name {k} and the increasing id the sentence with the format xxxx \
    and the speaker id (a random number) in that conversation. \
    For example: \n \
    M010009BC_0005 | 137903: I've just broken up with my gf. [sadness, 1]. \n \
    M010009BC_0006 | 256348: Wow really?? I'm so sorry to hear that... [surprise, 0]. "

    dic = {'role': 'user', 'content': first_prompt}
    completion = openai.ChatCompletion.create(model=model_engine, messages=[dic])
    dialogue = completion.choices[0].message['content']

    second_prompt = f"Follow this definition: \n {definition_text}. \
    Give me the summary of this conversation. And give explanation (evidence) of why \
    you think this each line in this dialogue contains a changepoint \
    (where there is the number 1 in the square brackets at the end of the line.) : \n {dialogue.strip()} \n \
    Consider the whole dialogue. If a point is not a significant changepoint, skip it and do not show me the output for that point. \
    The format should be like this: \n \
    SUMMARY: The conversation is about a man and a girl talking about their school projects. \n \
    CHANGEPOINT 1 (M010009BC_0005): There is a shift in the tone of the conversations. The girl is upset \
    because her mid-term grade is bad, it affects the overall mood significantly. \
    The inital tone is serious and professional. \n \
    CHANGEPOINT 2 (M010009BC_0010): There is a shift in the tone and topic of the conversations. \
    The man is cracking a very funny joke that clear the heaviness of the conversation. \
    This is a significant changepoint because most of the conversation is serious before this point."
    
    dic = {'role': 'user', 'content': second_prompt}
    completion = openai.ChatCompletion.create(model=model_engine, messages=[dic])
    explanation = completion.choices[0].message['content']

    return k, dialogue, explanation


def main(opt):
    if os.path.isfile(opt['syn_dials']):
        with open(opt['syn_dials'], 'r') as fp:
            syn_dials = json.load(fp)
    else:
        syn_dials = {}

    ctr = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_key = {}
        for i in tqdm(range(1, opt['num_samples'] + 1), total=opt['num_samples'], desc="Processing files", unit="file", ncols=100):
            if f'AUGMENT{i}' not in syn_dials.keys():
                future = executor.submit(
                    generate_dialogue_and_explanation_async,
                    f'AUGMENT{i}',
                    opt['api_key'],
                    opt['model_engine'],
                )
                future_to_key[future] = f'AUGMENT{i}'

        for future in tqdm(concurrent.futures.as_completed(future_to_key), total=len(future_to_key), desc="Processing futures", unit="future", ncols=100):
            k, dialogue, explanation = future.result()

            # processed_dialogue = process_dialogue(dialogue)
            # processed_explanation = process_explanation(explanation)

            syn_dials[k] = {
                'language': 'English',
                'dialogue': dialogue,
                'explanation': explanation,
                # 'processed_dialogue': processed_dialogue,
                # 'processed_explanation': processed_explanation,
            }

            with open('last_processed.txt', 'a+') as fp:
                fp.write(k + '\n')
            ctr += 1
            
            with open('synCP_dials.json', 'w') as fp:
                json.dump(syn_dials, fp)

            if ctr == opt['num_samples']:
                print(f'{ctr} samples generated ...')
                break

            


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key', type=str, help = 'Your OpenAI api key')
    parser.add_argument('--model_engine', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--syn_dials', type=str, default='synCP_dials.json', help = 'save/load generated dialogues')
    parser.add_argument('--num_samples', type=int, default=None, help='Number of elements in captions JSON to process')

    args = parser.parse_args()

    opt = vars(args)

    main(opt)

    print("done...")
