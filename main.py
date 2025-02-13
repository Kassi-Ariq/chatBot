import streamlit as st
from langchain.llms import Ollama
import PyPDF2
import chromadb
from dataSearch import search_google
from dataResponse import getRelevantData

chroma_client = chromadb.Client()
ollama_llm = Ollama(model="llama3.2")

st.set_page_config(page_title="Chatbot", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# Function to extract text from uploaded file
def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""

# Sidebar
st.sidebar.header("🛠️ Tools")
st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)
uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file


# Main Chatbot Section
st.title("Llama3.2 Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    response = ""

    if st.session_state.use_web_search:
        with st.chat_message("assistant"):
            with st.spinner("Searching the web..."):
                web_results = search_google(user_input)
                data = web_results[0] if web_results else "No relevant results found."
                relevant_data = getRelevantData(chroma_client, data, user_input)
                relevant_data_text = "\n".join(relevant_data)
                response = ollama_llm.invoke(f"Using this data:\n{relevant_data_text}.\nRespond to this prompt:\n{user_input}")
                st.markdown(response)

    elif st.session_state.uploaded_file:
        with st.chat_message("assistant"):
            with st.spinner("Processing file..."):
                file_text = extract_text(st.session_state.uploaded_file)
                if file_text:
                    response = ollama_llm.invoke(f"Using this document:\n{file_text}\nAnswer this:\n{user_input}")
                else:
                    response = "Could not extract text from the file."
                st.markdown(response)
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ollama_llm.invoke(user_input)
                st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

