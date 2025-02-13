import streamlit as st
from langchain_ollama import OllamaLLM
import PyPDF2
import chromadb
from dataSearch import search_google
from dataResponse import getRelevantData
from pymongo import MongoClient

client = MongoClient("mongodb+srv://Kassiyet:x8mWdUpxZoBOCdta@kassiyet.c2egr.mongodb.net/?retryWrites=true&w=majority&appName=Kassiyet")
db = client["chatbot_db"]
collection = db["saved_chats"]


chroma_client = chromadb.Client()
ollama_llm = OllamaLLM(model="llama3.2")

st.set_page_config(page_title="Chatbot", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running_chat" not in st.session_state:
    st.session_state.running_chat = ""  
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

# Web Search Toggle
st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

# File Upload
uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

st.sidebar.divider()

# New Chat
def page_refresh():
    st.session_state.messages = [] 
    st.session_state.running_chat = ""
    st.session_state.uploaded_file = None
    st.session_state.use_web_search = False
    st.rerun() 

if st.sidebar.button("New Chat"):
    page_refresh()

    
# Save Chat Button
st.sidebar.subheader("Save chat")
chat_title = st.sidebar.text_input("Enter a name for this chat:", value=st.session_state.running_chat)
save_button = st.sidebar.button("💾 Save Chat")
if save_button:
    if chat_title:
        chat_data = {
            "title": chat_title,
            "messages": st.session_state.messages
        }

        # If a chat is already open, update it
        if st.session_state.running_chat:  
            collection.update_one(
                {"title": st.session_state.running_chat},  # Find existing chat by title
                {"$set": chat_data}  # Update the messages
            )
            st.sidebar.success(f"Chat '{chat_title}' updated in MongoDB!")
        
        # Otherwise, save as a new chat
        else: 
            collection.insert_one(chat_data)
            st.sidebar.success(f"Chat '{chat_title}' saved to MongoDB!")

        # Update the session state to reflect the saved chat title
        st.session_state.running_chat = chat_title

# Display Saved Chats
st.sidebar.subheader("📂 Saved Chats")

# Fetch saved chats from MongoDB
saved_chats = collection.find({}, {"_id": 0})  # Exclude MongoDB ID field

for chat in saved_chats:
    chat_title = chat["title"]
    if st.sidebar.button(chat_title):
        st.session_state.messages = chat["messages"]
        st.session_state.running_chat = chat_title
        st.rerun()


# Main Chatbot Section
st.title("Chatbot")

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
