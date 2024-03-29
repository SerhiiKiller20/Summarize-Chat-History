from dotenv import load_dotenv
import os
import openai
import tiktoken
import time
import json
import sys
from datetime import datetime, timedelta
from app.Models.ChatLog_Model import find_messages_by_id, add_new_message, Message, find_summary_by_id, save_summary_in_db
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def answer_question(msg: str):
    final = ""
    log_id = "goldrace"
    saved_messages = find_messages_by_id(log_id)
    
    messages = [{'role': message.role, 'content': message.content}
                for message in saved_messages]
    
    history_summary = find_summary_by_id(log_id)
    # print("history: ", history_summarization)
    instructor = f"""
        You will act as a kind assistant.
        Below is the summarization of conversation between you and user.
        Based on it, please continue talking with user.
        ----------------------------------
        chat history summarization:
        {history_summary}
    """
    
    
    history_summary = f"""
        Summary of chat so far:
        {history_summary}
        
        ****************************************
        
    """
    yield history_summary
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            max_tokens=3000,
            messages=[
                {'role': 'system', 'content': instructor},
                {'role': 'user', 'content': msg}
            ],
            stream=True
        )
        for chunk in response:
            if 'content' in chunk.choices[0].delta:
                string = chunk.choices[0].delta.content
                yield string
                final += string
    except Exception as e:
        print(e)
        
    # ------------------------------------ summarization part ------------------------------------
    
    chat_history = ""
    for message in saved_messages:
        chat_history += f"\n{message.role}: {message.content}"
    chat_history += f"\n user: {msg}"
    chat_history += f"\n assistant: {final}"
    
    instructor = """
        You will act as a conversation summarizer.
        Summarize the entire conversation provided below, focusing on capturing the key points, questions, answers, main topics, decisions made, and any action items or conclusions reached.
        The summary should maintain the context, intent, and overall sentiment of the dialogue, condensing the essence of the discussion into a concise format.
        Aim for the summary to be approximately 10% of the original conversation's length, ensuring that critical details are preserved for continuity and that it serves as a standalone context for seamlessly continuing the conversation.
        Provide the summary in a structured and clear manner, highlighting essential points and developments to facilitate an understanding of the conversation's progression.
    """
    summary = ""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            max_tokens=3000,
            messages=[
                {'role': 'system', 'content': instructor},
                {'role': 'user', 'content': chat_history}
            ],
            stream=False
        )
        summary = response.choices[0].message.content
        print("summarization: ", summary)
    except Exception as e:
        print(e)
    
    save_summary_in_db(logId=log_id, summary=summary)
    add_new_message(logId=log_id, msg=Message(content=msg, role="user"))
    add_new_message(logId=log_id, msg=Message(content=final, role="assistant"))