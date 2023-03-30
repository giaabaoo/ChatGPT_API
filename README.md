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
```

# **Second prompt**

```python
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
```

# Repeat this process with additional knowledge and precise formulation of changepoints