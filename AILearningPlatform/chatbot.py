"""
Chatbot module for the e-learning platform.
Integrates with OpenAI to answer course-related questions.
If no API key is provided, falls back to predefined responses.
"""
import os
import logging
import random
import datetime
import pandas as pd
from extensions import db
from models import ChatMessage

# Define path for FAQ CSV, assuming it's in a 'data' subdirectory relative to this file's parent directory
# AILearningPlatform/data/faq.csv
FAQ_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'faq.csv')
faq_data = None

def load_faq_data():
    """Loads FAQ data from a CSV file into a pandas DataFrame."""
    global faq_data
    try:
        faq_data = pd.read_csv(FAQ_CSV_PATH)
        # Convert keywords to lowercase and into a list of strings for easier matching
        if 'Keywords' in faq_data.columns:
            faq_data['Keywords'] = faq_data['Keywords'].fillna('').astype(str).str.lower().apply(lambda x: [kw.strip() for kw in x.split(',') if kw.strip()])
        else:
            logging.warning(f"'Keywords' column not found in {FAQ_CSV_PATH}. FAQ keyword matching will be limited.")
            faq_data['Keywords'] = [[] for _ in range(len(faq_data))] # Add empty list if no keywords column
        logging.info(f"FAQ data loaded successfully from {FAQ_CSV_PATH}. Rows: {len(faq_data)}")
    except FileNotFoundError:
        logging.warning(f"FAQ CSV file not found at {FAQ_CSV_PATH}. Chatbot will rely on generic fallbacks.")
        faq_data = None # Ensure it's None if file not found
    except Exception as e:
        logging.error(f"Error loading FAQ CSV from {FAQ_CSV_PATH}: {e}")
        faq_data = None

# Load FAQ data when the module is imported
load_faq_data()

# Define the bot's persona and knowledge context
system_prompt = """
You are Learnify, an educational assistant for an e-learning platform. Your role is to help students with:
1. Course-related questions about programming, data science, machine learning, and web development
2. Clarifying concepts they find difficult
3. Providing hints for exercises without giving away complete solutions
4. Suggesting additional learning resources

Maintain a supportive, encouraging tone. If you don't know the answer, be honest and suggest alternatives.
Keep your responses concise but thorough, focusing on accuracy and educational value.
"""

# Check if OpenAI API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
has_api_key = OPENAI_API_KEY is not None and OPENAI_API_KEY != "your-api-key"

if has_api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI client initialized successfully")
    except ImportError:
        has_api_key = False
        logging.error("OpenAI module not available")
    except Exception as e:
        has_api_key = False
        logging.error(f"Error initializing OpenAI client: {str(e)}")

# Fallback responses for when OpenAI is not available
fallback_responses = [
    "Python is a high-level, interpreted programming language known for its readability and simplicity. It's great for beginners and also powerful enough for professional applications.",
    "HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser, while CSS (Cascading Style Sheets) describes how HTML elements should be displayed.",
    "Data Science combines multiple fields including statistics, scientific methods, and data analysis to extract value from data. Python is one of the most popular languages for data science.",
    "Machine Learning is a subset of AI that enables computers to learn from data and improve without explicit programming. Common algorithms include linear regression, decision trees, and neural networks.",
    "JavaScript is a programming language that allows you to implement complex features on web pages. It's an essential part of web applications and runs on the client-side in the browser.",
    "SQL (Structured Query Language) is used to communicate with and manipulate databases. Common commands include SELECT, INSERT, UPDATE, and DELETE.",
    "An API (Application Programming Interface) allows different software applications to communicate with each other. RESTful APIs are commonly used in web development.",
    "Git is a distributed version control system for tracking changes in source code during software development. GitHub is a platform that hosts Git repositories.",
    "Object-Oriented Programming (OOP) is a programming paradigm based on the concept of 'objects', which can contain data and code. The main principles are encapsulation, inheritance, and polymorphism.",
    "To improve your programming skills, practice regularly with coding challenges, contribute to open-source projects, and work on personal projects that interest you."
]

def get_chatbot_response(username, user_message, course_context=None):
    """
    Get a response from the AI chatbot.
    
    Args:
        username: The username of the user
        user_message: The message from the user
        course_context: Optional course context to help the AI understand the question
        
    Returns:
        The AI's response as a string
    """
    # We don't log the message here as it's now handled in the route function
    
    # If OpenAI API is available, use it
    if has_api_key:
        try:
            # Prepare the messages for the API
            from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
            from openai import OpenAI
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add course context if available
            if course_context:
                course_info = f"""
                The user is currently studying the course: {course_context['title']}
                Course level: {course_context['level']}
                Course description: {course_context['description']}
                """
                messages.append({"role": "system", "content": course_info})
            
            # Add the user's message
            messages.append({"role": "user", "content": user_message})
            
            try:
                # Get response from OpenAI
                # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                client = OpenAI(api_key=OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-4o",  # Using the latest model
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7,
                )
            except Exception as e:
                logging.error(f"Error with OpenAI API: {str(e)}")
                raise
            
            # Extract the response content
            bot_response = response.choices[0].message.content
            
            return bot_response
        
        except Exception as e:
            logging.error(f"Error getting chatbot response: {str(e)}")
            # Fall through to use fallback responses
    
    # If no API key or there was an error, use fallback responses
    user_message_lower = user_message.lower()

    # 1. Try FAQ CSV Fallback
    if faq_data is not None and not faq_data.empty:
        user_keywords = set(user_message_lower.split())
        best_match_score = 0
        best_response = None

        for index, row in faq_data.iterrows():
            if not row['Keywords']: # Skip if no keywords for this FAQ entry
                continue
            
            faq_keywords = set(row['Keywords'])
            common_keywords = user_keywords.intersection(faq_keywords)
            
            if len(common_keywords) > best_match_score:
                best_match_score = len(common_keywords)
                best_response = row['Answer']
        
        if best_match_score > 0 and best_response: # Require at least one keyword match
            logging.info(f"Found relevant answer in FAQ CSV for user message: '{user_message}'")
            # Personalize if it's a greeting
            if any(greet in user_message_lower for greet in ['hi', 'hello', 'hey']):
                 return f"Hello {username}! I found this in our FAQ that might help: {best_response}"
            return best_response

    # 2. If no FAQ match, try existing fallback_responses logic
    logging.info("No suitable FAQ match found, trying generic fallbacks.")
    selected_fallback_response = None
    if 'python' in user_message_lower:
        selected_fallback_response = fallback_responses[0]
    elif 'html' in user_message_lower or 'css' in user_message_lower:
        selected_fallback_response = fallback_responses[1]
    elif 'data' in user_message_lower or 'science' in user_message_lower:
        selected_fallback_response = fallback_responses[2]
    elif 'machine' in user_message_lower or 'learning' in user_message_lower or 'ai' in user_message_lower:
        selected_fallback_response = fallback_responses[3]
    elif 'javascript' in user_message_lower or 'js' in user_message_lower:
        selected_fallback_response = fallback_responses[4]
    elif 'sql' in user_message_lower or 'database' in user_message_lower:
        selected_fallback_response = fallback_responses[5]
    elif 'api' in user_message_lower:
        selected_fallback_response = fallback_responses[6]
    elif 'git' in user_message_lower or 'github' in user_message_lower:
        selected_fallback_response = fallback_responses[7]
    elif 'object' in user_message_lower or 'class' in user_message_lower or 'oop' in user_message_lower:
        selected_fallback_response = fallback_responses[8]
    else:
        # Default to a random response from the original list if no specific keyword match
        selected_fallback_response = random.choice(fallback_responses)
    
    bot_response = selected_fallback_response

    # Add a personalized greeting to the selected fallback if applicable
    if 'hi' in user_message_lower or 'hello' in user_message_lower or 'hey' in user_message_lower:
        bot_response = f"Hello! I hope you're having a good day. Here's something you might find interesting: {bot_response}"
    
    # Add a note about API key if asked about the chatbot functionality
    if 'not working' in user_message_lower or 'api key' in user_message_lower or 'openai' in user_message_lower:
        bot_response = "I'm currently running in demo mode without an OpenAI API key. To enable full AI functionality, an admin needs to add a valid OpenAI API key to the system."
    
    # If asking about a specific course (matching course context)
    if course_context and course_context.get('title', '').lower() in user_message_lower:
        bot_response = f"Regarding the {course_context['title']} course ({course_context['level']} level): {bot_response}"
    
    return bot_response
