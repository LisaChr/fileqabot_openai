import streamlit as st
import fitz  # PyMuPDF --> LC: to allow PDF imports
from openai import OpenAI

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

# Open Sidebar for password input
password = st.sidebar.text_input("Enter your password", type="password")

# Initialize the OpenAI client conditionally
client = None

# Check if the correct password is entered
if password == st.secrets["access_password"]:  # Access the password from secrets
    client = OpenAI(api_key=st.secrets["openai_key"])
    st.sidebar.success("Password accepted!")
else:
    st.sidebar.error("Please enter the correct password to access the OpenAI API key.")

# Set Title:
st.title("📝 File Q&A with ChatGPT")

# Upload the file:
uploaded_file = st.file_uploader("Upload an article", type=("txt", "md", "pdf"))

# Text input:
question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file
)

if uploaded_file and question:
    if client:
        # Parsing the text:
        if uploaded_file.type == "application/pdf":
            article = extract_text_from_pdf(uploaded_file)
        else:
            article = uploaded_file.read().decode()

        # Prompting:
        my_prompt = f"Here's an article: {article}\n\n{question}"

        # ChatGPT Connection and API call:
        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": my_prompt}
                ],
                max_tokens=2500 #LC: max answer length
            )

            # Display the response
            st.write("### Answer")
            st.write(completion.choices[0].message.content)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please add your OpenAI API key to continue.")
