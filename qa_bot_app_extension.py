import streamlit as st
import fitz  # PyMuPDF --> LC: to allow PDF imports
import openai
import magic  # For file type detection
from io import BytesIO

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    pdf_stream = BytesIO(pdf_file.read())  # Convert UploadedFile to BytesIO stream
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

# Chat Completion Message Object
def normalize_message(message):
    if isinstance(message, dict):
        return {k: message[k] for k in ['role', 'content'] if k in message and message[k] is not None}
    else:
        raise ValueError("Message is not a dictionary.")

# Function to add user prompt to message history
def add_user_prompt(messages, prompt):
    if isinstance(messages, dict):
        messages = [messages]
    messages.append({'role': 'user', 'content': prompt})
    return messages

# Function to maintain and update message history
def maintain_chatgpt_message_history(messages, history=None, history_window=20):
    if history is None:
        history = []

    if isinstance(messages, list):
        normalized_messages = [normalize_message(msg) for msg in messages]
    else:
        normalized_messages = [normalize_message(messages)]

    history.extend(normalized_messages)

    system_msg = None
    if history and 'role' in history[0] and history[0]['role'] == 'system':
        system_msg = history.pop(0)

    if len(history) > history_window:
        history = history[-history_window:]

    if system_msg:
        history.insert(0, system_msg)

    return history

# Function to get response from ChatGPT
def get_completion(message_history, model="gpt-3.5-turbo", temperature=0):
    response = client.chat.completions.create(
        model=model,
        messages=message_history,
        temperature=temperature,
    )
    return response.choices[0].message.content

# Open Sidebar for password input
password = st.sidebar.text_input("Enter your password", type="password")

# Initialize the OpenAI client conditionally
client = None

# Check if the correct password is entered
if password == st.secrets["access_password"]:  # Access the password from secrets
    client = openai
    client.api_key = st.secrets["openai_key"]
    st.sidebar.success("Password accepted!")
else:
    st.sidebar.error("Please enter the correct password to access the OpenAI API key.")

# Set Title:
st.title("📝 File Q&A with ChatGPT")

# Initialize message history in Streamlit session state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Upload the file:
uploaded_file = st.file_uploader("Upload an article", type=("txt", "md", "pdf"))

# Text input:
question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file
)

if uploaded_file and question:
    # Check if uploaded file is PDF using magic library
    mime_type = magic.Magic(mime=True)
    uploaded_file_type = mime_type.from_buffer(uploaded_file.read(1024))  # Check first 1024 bytes
    uploaded_file.seek(0)  # Reset file pointer after reading

    if "pdf" in uploaded_file_type:
        # Parsing the text:
        article = extract_text_from_pdf(uploaded_file)
    else:
        article = uploaded_file.read().decode()

    # Prompting:
    my_prompt = f"Here's an article: {article}\n\n{question}"

    # Add user prompt to message history
    st.session_state['message_history'] = add_user_prompt(st.session_state['message_history'], my_prompt)

    if client:
        try:
            # Get response from ChatGPT
            completion_content = get_completion(st.session_state['message_history'])

            # Update message history with response
            assistant_message = {'role': 'assistant', 'content': completion_content}
            st.session_state['message_history'] = maintain_chatgpt_message_history(messages=[assistant_message], history=st.session_state['message_history'])

            # Display the response
            st.write("### Answer")
            st.write(completion_content)

            # Display message history
            st.write("### Message History")
            for msg in st.session_state['message_history']:
                if msg['role'] == 'user':
                    st.write(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    st.write(f"Assistant: {msg['content']}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please add your OpenAI API key to continue.")
