import streamlit as st
from langchain_ollama import OllamaLLM
import PyPDF2
import chromadb
from dataSearch import search_google
from dataResponse import getRelevantData
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb+srv://Kassiyet:x8mWdUpxZoBOCdta@kassiyet.c2egr.mongodb.net/?retryWrites=true&w=majority&appName=Kassiyet")
db = client["chatbot_db"]
collection = db["saved_chats"]

# Initialize AI and Database Clients
chroma_client = chromadb.Client()
ollama_llm = OllamaLLM(model="llama3.2")

# Initialize Conversation Memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

# Streamlit Config
st.set_page_config(page_title="Chatbot", layout="wide")


# Create chains
emergency_prompt = PromptTemplate.from_template(
    "Does this message indicate an emergency? Reply with only 'YES' or 'NO'. Message: {message}"
)
swear_prompt = PromptTemplate.from_template(
    "Does this message contain any offensive or inappropriate language? Reply with only 'YES' or 'NO'. Message: {message}"
)
emergency_chain = emergency_prompt | ollama_llm
swear_chain = swear_prompt | ollama_llm

parallel_chain = RunnableParallel(
    emergency=emergency_chain, 
    swear=swear_chain
)


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running_chat" not in st.session_state:
    st.session_state.running_chat = ""
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# Function to Extract Text from Files
def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""


st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

st.sidebar.divider()

# New Chat Function
def page_refresh():
    st.session_state.messages = []
    st.session_state.running_chat = ""
    st.session_state.uploaded_file = None
    st.session_state.use_web_search = False
    st.session_state.memory.clear()
    st.rerun()

if st.sidebar.button("New Chat"):
    page_refresh()

# Save Chat Button
st.sidebar.subheader("Save chat")
chat_title = st.sidebar.text_input("Enter a name for this chat:", value=st.session_state.running_chat)

    if chat_title:
        chat_data = {"title": chat_title, "messages": st.session_state.messages}
        if st.session_state.running_chat:
            collection.update_one({"title": st.session_state.running_chat}, {"$set": chat_data})
            st.sidebar.success(f"Chat '{chat_title}' updated in MongoDB!")
        else:
            collection.insert_one(chat_data)
            st.sidebar.success(f"Chat '{chat_title}' saved to MongoDB!")
        st.session_state.running_chat = chat_title

# Display Saved Chats

for chat in saved_chats:
    if st.sidebar.button(chat["title"]):
        st.session_state.messages = chat["messages"]
        st.session_state.running_chat = chat["title"]
        st.session_state.memory.clear()
        st.rerun()

# Main Chat Section
st.title("Chatbot")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Handling
if user_input := st.chat_input("Ask me anything..."):

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()