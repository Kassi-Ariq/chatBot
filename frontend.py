import streamlit as st
import ollama
from dataSearch import search_google
from dataResponse import getRelevantData
import chromadb
import PyPDF2

client = chromadb.Client()

st.set_page_config(page_title="Llama3.2 Chatbot with Web Search", layout="wide")

# Initialize chat history & toggle state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

st.sidebar.header("🛠️ Tools")

# Web search toggle
st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

# File upload option
uploaded_file = st.sidebar.file_uploader("File Upload", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

# Function to extract text from uploaded file
def extract_text(file):
    if file.type == "text/plain":  # Handle TXT files
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":  # Handle PDF files
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    return ""

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    response = ""

    # If web search is enabled, fetch data from the internet
    if st.session_state.use_web_search:
        with st.chat_message("assistant"):
            with st.spinner("Searching the web..."):
                web_results = search_google(user_input)
                data = web_results[0] if web_results else "No relevant results found."
                relevant_data = getRelevantData(client, data, user_input)
                relevant_data_text = "\n".join(relevant_data)

                data_output = ollama.generate(
                    model="llama3.2",
                    prompt=f"Using this data:\n{relevant_data_text}.\nRespond to this prompt:\n{user_input}"
                )
                response = data_output['response']
                st.markdown(response)

    # If a file is uploaded, use its text for answering
    elif st.session_state.uploaded_file:
        with st.chat_message("assistant"):
            with st.spinner("Processing file..."):
                file_text = extract_text(st.session_state.uploaded_file)
                if file_text:
                    data_output = ollama.generate(
                        model="llama3.2",
                        prompt=f"Using this document:\n{file_text}\nAnswer this:\n{user_input}"
                    )
                    response = data_output['response']
                else:
                    response = "Could not extract text from the file."
                st.markdown(response)

    # Otherwise, use the chatbot normally
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ollama.generate(
                    model="llama3.2",
                    prompt=user_input
                )["response"]
                st.markdown(response)

    # Store response in chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Force rerun to display new messages correctly
    st.rerun()
