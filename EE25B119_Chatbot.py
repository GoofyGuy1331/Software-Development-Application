#importing all the required modules

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

#defining the chatbots personality
CHATBOT_PERSONALITY = os.environ.get(
    "CHATBOT_PERSONALITY",
    "You are a friendly and helpful assistant responding to a user on a messaging app. Be conversational and concise."
)

app = Flask(__name__)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", convert_system_message_to_human=True)

prompt = ChatPromptTemplate.from_messages([
    ("system", CHATBOT_PERSONALITY),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}")
])

chain = prompt | model | StrOutputParser()

#history/memory
message_store = {}  # In-memory message store
user_states = {}    # In-memory user state store

#different modes
MODE_TEXTS = [
    "Explain as if you were my tutor",
    "Help me as if you were my best buddy",
    "Explain with detailed explanations and with steps",
    ""
]


#function to get the history of the interactions between the user and the chatbot
def get_session_history(session_id: str) -> ChatMessageHistory:
    """Gets the chat history for a given session_id."""
    if session_id not in message_store:
        message_store[session_id] = ChatMessageHistory()
    return message_store[session_id]

conversational_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['POST'])
def webhook():
    user_number = request.values.get('From', '')
    incoming_msg_text = request.values.get('Body', '').strip().lower()

    resp = MessagingResponse()

    #initializing user states
    if user_number not in user_states:
        user_states[user_number] = {
            "in_configure_mode": False,
            "extra_input": MODE_TEXTS[3]  # Default to Normal Mode
        }

    #changing configuration modes
    if incoming_msg_text == 'configure' and not user_states[user_number]["in_configure_mode"]:
        user_states[user_number]["in_configure_mode"] = True
        resp.message("Sure. Here are the possible Configurations:\n1) Tutor\n2) Personal Buddy\n3) Detailed Explanation Mode\n4) Normal Mode\nKindly send only the number of the corresponding setting to change to that setting.")
        return str(resp)

    if user_states[user_number]["in_configure_mode"]:
        try:
            mode_choice = int(incoming_msg_text)
            if 1 <= mode_choice <= len(MODE_TEXTS):
                user_states[user_number]["extra_input"] = MODE_TEXTS[mode_choice - 1]
                user_states[user_number]["in_configure_mode"] = False
                bot_response_text = f"Setting changed. You are now in mode {mode_choice}."
            else:
                bot_response_text = "Invalid number. Please choose a number from the list."
        except ValueError:
            bot_response_text = "Invalid input. Please send only the number corresponding to the setting you want."
        
        resp.message(bot_response_text)
        return str(resp)

    # Test code for handling images and audio
    num_media = int(request.values.get('NumMedia', 0))
    user_input = []

    if num_media > 0:
        media_url = request.values.get('MediaUrl0', '')
        content_type = request.values.get('MediaContentType0', '')

        if 'image' in content_type:
            prompt_text = incoming_msg_text if incoming_msg_text else "Describe this image for me."
            user_input = [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": media_url}
            ]
        elif 'audio' in content_type:
            resp.message("I received your voice note! I'm still learning to understand audio, but I'll be able to soon.")
            return str(resp)
        else:
            resp.message("I see you sent something, but I can only process text and images right now.")
            return str(resp)
    else:
        if not incoming_msg_text:
            resp.message("Hello! I'm here to help. Please send me a question or an image. Type 'configure' to change settings.")
            return str(resp)
        user_input = incoming_msg_text

    #Input for the AI model
    try:
        current_extra_input = user_states[user_number]["extra_input"] + " and ensure your response does not exceed 300 words."
        final_input_for_chain = user_input

        if current_extra_input:
            if isinstance(user_input, list):  # image + text
                original_text = user_input[0]['text']
                user_input[0]['text'] = f"Instruction: {current_extra_input}\nUser question: {original_text}"
                final_input_for_chain = user_input
            else:  # text-only
                final_input_for_chain = f"Instruction: {current_extra_input}\nUser question: {user_input}"

        #Calling gemini via LangChain
        bot_response_text = conversational_chain.invoke(
            {"input": final_input_for_chain},
            config={"configurable": {"session_id": user_number}}
        )

        MAX_WORDS = 300
        words = str(bot_response_text).split()
        if len(words) > MAX_WORDS:
            print(f"Trimming response from {len(words)} words to {MAX_WORDS}")
            bot_response_text = ' '.join(words[:MAX_WORDS]) + "..."

    except Exception as e:
        print(f"Error invoking LangChain chain: {e}")
        bot_response_text = "I'm sorry, I'm having a little trouble thinking right now. Please try again in a moment."

    if not bot_response_text or not str(bot_response_text).strip():
        print("AI Response was empty or invalid. Sending fallback message.")
        bot_response_text = "I received your message, but I'm having trouble formulating a response. Could you please try rephrasing it?"

    resp.message(bot_response_text)
    return str(resp)

#Running the Program
if __name__ == '__main__':
    app.run(port=5000, debug=True)