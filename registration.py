import streamlit as st
import pymongo
import bcrypt
import ollama
import PyPDF2
from pymongo import MongoClient
from dataSearch import search_google
from dataResponse import getRelevantData
import chromadb

# MongoDB Connection
MONGO_URI = "mongodb+srv://Kassiyet:x8mWdUpxZoBOCdta@kassiyet.c2egr.mongodb.net/?retryWrites=true&w=majority&appName=Kassiyet"  # Replace with your actual MongoDB URI
client = MongoClient(MONGO_URI)
db = client["chatbotDB"]  # Database name
users_collection = db["users"]  # Collection for user data

chroma_client = chromadb.Client()

st.set_page_config(page_title="Chatbot", layout="wide")

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# Hash password function
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Verify password function
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

# Function to extract text from uploaded file
def extract_text(file):
    if file.type == "text/plain":  # Handle TXT files
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":  # Handle PDF files
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    return ""

# Sidebar: Authentication


if not st.session_state.logged_in:
    st.sidebar.header("🔐 Authentication")
    auth_option = st.sidebar.radio("Login or Register", ["Login", "Register"])

    # Register Page
    if auth_option == "Register":
        reg_username = st.sidebar.text_input("Username", key="reg_username")
        reg_email = st.sidebar.text_input("Email", key="reg_email")
        reg_password = st.sidebar.text_input("Password", type="password", key="reg_password")
        reg_button = st.sidebar.button("Register")

        if reg_button:
            if reg_username and reg_email and reg_password:
                # Check if user exists
                existing_user = users_collection.find_one({"username": reg_username})
                if existing_user:
                    st.sidebar.error("Username already exists. Choose another.")
                else:
                    hashed_pw = hash_password(reg_password)
                    users_collection.insert_one({"username": reg_username, "email": reg_email, "password": hashed_pw})
                    st.sidebar.success("Account created! Please log in.")
            else:
                st.sidebar.warning("All fields are required.")

    # Login Page
    elif auth_option == "Login":
        login_username = st.sidebar.text_input("Username", key="login_username")
        login_password = st.sidebar.text_input("Password", type="password", key="login_password")
        login_button = st.sidebar.button("Login")

        if login_button:
            user = users_collection.find_one({"username": login_username})
            if user and verify_password(login_password, user["password"]):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.sidebar.success(f"Welcome, {login_username}!")
                st.rerun()  # Rerun to update UI
            else:
                st.sidebar.error("Invalid username or password.")

else:
    # Show Tools & Logout Button after Login
    st.sidebar.header("🛠️ Tools")
    
    # Web search toggle
    st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

    # File upload option
    uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    # Logout Button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.messages = []  # Clear chat history
        st.session_state.uploaded_file = None
        st.sidebar.success("Logged out successfully!")
        st.rerun()

# Main Chatbot Section (Only After Login)
if st.session_state.logged_in:
    st.title("Llama3.2 Chatbot")
    st.write(f"Ask me anything, **{st.session_state.username}**!")

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
                    relevant_data = getRelevantData(chroma_client, data, user_input)
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

else:
    st.warning("🔐 Please log in to use the chatbot.")


