import streamlit as st
import ollama
import PyPDF2
import chromadb
from auth import register_user, login_user, logout_user  # Import auth functions
from dataSearch import search_google
from dataResponse import getRelevantData

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

# Function to extract text from uploaded file
def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""

# Sidebar: Authentication
if not st.session_state.logged_in:
    st.sidebar.header("🔐 Authentication")
    auth_option = st.sidebar.radio("Login or Register", ["Login", "Register"])

    if auth_option == "Register":
        reg_username = st.sidebar.text_input("Username", key="reg_username")
        reg_email = st.sidebar.text_input("Email", key="reg_email")
        reg_password = st.sidebar.text_input("Password", type="password", key="reg_password")
        if st.sidebar.button("Register"):
            success, message = register_user(reg_username, reg_email, reg_password)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)

    elif auth_option == "Login":
        login_username = st.sidebar.text_input("Username", key="login_username")
        login_password = st.sidebar.text_input("Password", type="password", key="login_password")
        if st.sidebar.button("Login"):
            success, message = login_user(login_username, login_password)
            if success:
                st.sidebar.success(message)
                st.rerun()
            else:
                st.sidebar.error(message)
else:
    st.sidebar.header("🛠️ Tools")
    
    st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

    uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    if st.sidebar.button("Logout"):
        logout_user()
        st.sidebar.success("Logged out successfully!")
        st.rerun()

# Main Chatbot Section (Only After Login)
if st.session_state.logged_in:
    st.title("Llama3.2 Chatbot")
    st.write(f"Ask me anything, **{st.session_state.username}**!")

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

                    data_output = ollama.generate(
                        model="llama3.2",
                        prompt=f"Using this data:\n{relevant_data_text}.\nRespond to this prompt:\n{user_input}"
                    )
                    response = data_output['response']
                    st.markdown(response)

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

        else:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = ollama.generate(
                        model="llama3.2",
                        prompt=user_input
                    )["response"]
                    st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

else:
    st.warning("🔐 Please log in to use the chatbot.")
