# ChatGPT_API
Code for generating conversations using ChatGPT prompts
# Augmentation process
# First prompt

### ********************DEFINITION********************

```python
definition_text = f"A changepoint in a conversation is when there's \
    a shift in the topic, speaker, tone, or energy, which can lead to a change \
    in social norms or emotions. This shift can temporarily or permanently \
    affect the conversation's outcome, relationship, goals, emotions, and flow, \
    either positively or negatively in a significant way."
```

### **PROMPT**

```python
first_prompt = f"With this definition \"{definition_text}\" \n \
    Generate a dialogue in \"{language}\" language with up to 20 turns of text messages between two people \
    (family, friends, acquaintances) about a topic (on a discussion forum or SMS app) \
    (can be the start of conversation or in the middle of conversation). \
    For each line, annotate STRICTLY at the end the emotion of the line with the emotions \
    from this list {emotions} (use emotions from this list only) \
    and label 1 for CP and label 0 for non-CP. There should be at most 3 lines with label=1 so \
    choose the line with changepoints carefully by stricly follow the definition.\
    It should have the document name {k} and the increasing id the sentence with the format xxxx \
    and the speaker id (a random number) in that conversation. \
    For example: \
    AUGMENT1_0005 | 137903: 我刚刚和我的女朋友分手了。 [sadness, 1]. \n \
    AUGMENT1_0006 | 256348: 哇塞！真的么？？ 听到这个我很难过... [surprise, 0]. "
```

# **Second prompt**

```python
second_prompt = f"Follow this definition: \n {definition_text}. \
    Give me the summary of this conversation. And give explanation (evidence) of why \
    you think this each line in this dialogue contains a changepoint \
    (where there is the number 1 in the square brackets at the end of the line.) : \n {dialogue.strip()} \n \
    Consider the whole dialogue. If a point is not a significant changepoint, skip it and do not show me the output for that point. \
    Also, add an impact scalar for each changepoint to determine the importance of the point in the whole conversation. Impact scalars \
    are integers from 1 to 5 (1 is the most negative, 5 is the most positive) \
    The format should be like this: \n \
    SUMMARY: The conversation is about a man and a girl talking about their school projects. \n \
    CHANGEPOINT 1 (AUGMENT1_0005) (impact_scalar=1): There is a shift in the tone of the conversations. The girl is upset \
    because her mid-term grade is bad, it affects the overall mood significantly. \
    The inital tone is serious and professional. \n \
    CHANGEPOINT 2 (AUGMENT1_0010) (impact_scalar=5) There is a shift in the tone and topic of the conversations. \
    The man is cracking a very funny joke that clear the heaviness of the conversation. \
    This is a significant changepoint because most of the conversation is serious before this point."
    
```

# Repeat this process with additional knowledge and precise formulation of changepoints