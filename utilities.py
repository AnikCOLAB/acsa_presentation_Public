import streamlit as st
import json

def first_match(sentence1, sentence2, count):
    # Split sentences into words
    words1 = sentence1.split()
    words2 = sentence2.split()
    
    # Take only the first six
    first_six_1 = words1[:count]
    first_six_2 = words2[:count]
    
    # Compare
    return first_six_1 == first_six_2


def load_conversation_data(uploaded_file=None, history=None):
    """Load and parse JSON conversation data"""
    if uploaded_file:
        content = uploaded_file.read()
        data = json.loads(content)
    else:
        if history == "Gemini":
            file_path = "gemini_history.json"
        elif history == "OpenAI":
            file_path = "openai_history.json"

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def extract_conversations(data):
    """Extract user questions and model responses from conversation data for a single model"""
    openai_conversations = []
    gemini_conversations = []
    
    openai_data, gemini_data = data
    current_question = None
    for message in openai_data:
        if message["role"] == "user" and message["content"].strip():
            current_question = message["content"]
        elif message["role"] == "assistant" and current_question:
            openai_conversations.append({
                "question": current_question,
                "response": message["content"]
            })
            current_question = None
                

    current_question = None
    for message in gemini_data:
        if message["role"] == "user":
            for part in message["parts"]:
                if part["text"] and part["text"].strip():
                    current_question = part["text"]
        elif message["role"] == "model" and current_question:
            for part in message["parts"]:
                if part["text"]:
                    gemini_conversations.append({
                        "question": current_question,
                        "response": part["text"]
                    })
                    current_question = None
                    break
    
    conversations = []
    for each_openai in openai_conversations:
        running_question = each_openai["question"]
        for each_gemini in gemini_conversations:
            if first_match(each_gemini["question"], running_question, 10):
                conversations.append({
                    "question": running_question,
                    "GPT": each_openai["response"],
                    "Gemini": each_gemini["response"]
                })
                continue
    
    with open("llm_conversation.json", "w") as json_file:
        json.dump(conversations, json_file, indent=4)
    return conversations


def get_response(question, llm):
    with open("llm_conversation.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for each in data:
        question_match = first_match(question, each["question"], 10)
        if question_match:
            return each[llm]