import os
import pymongo
import asyncio
from telegram import Bot
from pymongo import MongoClient
import random
import math

# Read environment variables
mongo_uri = os.getenv('MONGO_URI')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Default channel
DEFAULT_CHANNEL = os.getenv('DEFAULT_CHANNEL')

# Initialize MongoDB client and Telegram bot
client = MongoClient(mongo_uri)
bot = Bot(token=BOT_TOKEN)

def fetch_collections(database_name):
    db = client[database_name]
    return db.list_collection_names()

def fetch_questions_from_collection(database_name, collection_name, num_questions):
    db = client[database_name]
    collection = db[collection_name]
    questions = collection.aggregate([{ '$sample': { 'size': num_questions } }])
    return list(questions)

def get_correct_option_index(answer_key):
    option_mapping = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
    return option_mapping.get(answer_key.lower(), None)

async def send_quiz_to_channel(question, options, correct_option_index, explanation):
    question_text = f"{question}\n[@CurrentAdda]"
    
    # Use "@Currentadda" if explanation is not available or is NaN
    if explanation is None or (isinstance(explanation, float) and math.isnan(explanation)):
        explanation = "@CurrentAdda"
    
    try:
        await bot.send_poll(
            chat_id=DEFAULT_CHANNEL,
            question=question_text,
            options=options,
            type='quiz',
            correct_option_id=correct_option_index,
            explanation=explanation,
            is_anonymous=True,
            allows_multiple_answers=False,
        )
        print(f"Quiz sent successfully: {question}")
    except Exception as e:
        print(f"Error sending quiz: {e}")

async def main():
    print("Fetching collections from the database 'MasterQuestions'...")
    await asyncio.sleep(1)  # Delay before fetching collections
    collections = fetch_collections('MasterQuestions')
    
    if not collections:
        print("No collections found in the database.")
        return
    
    await asyncio.sleep(1)  # Delay before selecting collection
    selected_collection = random.choice(collections)
    print(f"Selected collection: {selected_collection}")
    
    num_questions = 10
    print(f"Fetching {num_questions} random questions from collection '{selected_collection}'...")
    await asyncio.sleep(1)  # Delay before fetching questions
    questions = fetch_questions_from_collection('MasterQuestions', selected_collection, num_questions)
    
    for question in questions:
        question_text = question.get('Question', 'No question text')
        options = [question.get('Option A', 'No option'), question.get('Option B', 'No option'), 
                   question.get('Option C', 'No option'), question.get('Option D', 'No option')]
        correct_option_index = get_correct_option_index(question.get('Answer', 'a'))
        explanation = question.get('Explanation', None)
        
        if correct_option_index is not None:
            await send_quiz_to_channel(question_text, options, correct_option_index, explanation)
            await asyncio.sleep(1)  # Delay between sending each question
        else:
            print(f"Skipping question due to invalid answer format: {question}")

if __name__ == "__main__":
    asyncio.run(main())
