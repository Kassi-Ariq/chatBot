import streamlit as st
from langchain_ollama import OllamaLLM
import PyPDF2
import chromadb
from dataSearch import search_google
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from callback import AlertCallback
from telegram_notification import telegramSendMessage
from langchain.memory import ConversationBufferMemory


client = MongoClient("mongodb+srv://Kassiyet:x8mWdUpxZoBOCdta@kassiyet.c2egr.mongodb.net/?retryWrites=true&w=majority&appName=Kassiyet")
db = client["chatbot_db"]
collection = db["saved_chats"]

chroma_client = chromadb.Client()

st.set_page_config(page_title="Chatbot", layout="wide")





# Initialize Short Term Memory
memory = ConversationBufferMemory()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running_chat" not in st.session_state:
    st.session_state.running_chat = ""  
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama3.2"




# Functions
def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""

def page_refresh():
    st.session_state.messages = [] 
    st.session_state.running_chat = ""
    st.session_state.uploaded_file = None
    st.session_state.use_web_search = False
    memory.clear()
    st.rerun() 

def saveInShortMem(message):
    for i in range(0, len(message) - 1, 2):  
            if (message[i]["role"] == "user" and 
                message[i + 1]["role"] == "assistant"):
                
                user_input = message[i]["content"]
                assistant_output = message[i + 1]["content"]
                memory.save_context({"input": user_input}, {"output": assistant_output})





# Sidebar
st.sidebar.header("Tools")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Llama 3.2", use_container_width=True):
        st.session_state.selected_model = "llama3.2"

with col2:
    if st.button("Gemma", use_container_width=True):
        st.session_state.selected_model = "gemma"

st.sidebar.write(f"Current model: {st.session_state.selected_model}")

ollama_llm = OllamaLLM(model=st.session_state.selected_model)

# Web Search Toggle
st.session_state.use_web_search = st.sidebar.checkbox("Web Search", value=False)

# File Upload
uploaded_file = st.sidebar.file_uploader("Upload a File", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

st.sidebar.divider()

# New Chat

if st.sidebar.button("New Chat"):
    page_refresh()

    
# Save Chat Button
st.sidebar.subheader("Save chat")
chat_title = st.sidebar.text_input("Enter a name for this chat:", value=st.session_state.running_chat)
save_button = st.sidebar.button("Save Chat")
if save_button:
    if chat_title:
        chat_data = {
            "title": chat_title,
            "messages": st.session_state.messages
        }

        # If a chat is already open, update it
        if st.session_state.running_chat:  
            collection.update_one(
                {"title": st.session_state.running_chat},  
                {"$set": chat_data}
            )
            st.sidebar.success(f"Chat '{chat_title}' updated in MongoDB!")
        
        # Otherwise, save as a new chat
        else: 
            collection.insert_one(chat_data)
            st.sidebar.success(f"Chat '{chat_title}' saved to MongoDB!")

        # Update the session state to reflect the saved chat title
        st.session_state.running_chat = chat_title

# Display Saved Chats
st.sidebar.subheader("Saved Chats")

# Fetch saved chats from MongoDB
saved_chats = collection.find({}, {"_id": 0}) 






# Create chains
emergency_prompt = PromptTemplate.from_template(
    "Does this message indicate an emergency? Reply with only 'YES' or 'NO'. Message: {message}"
)
swear_prompt = PromptTemplate.from_template(
    "Does this message contain any offensive or inappropriate language? Reply with only 'YES' or 'NO'. Message: {message}"
)
search_prompt = PromptTemplate.from_template(
    "Based on the previous conversation:\n{previousConversation}\n"
    "and the user's question:\n{question}\n"
    "Generate a short and effective Google search query. "
    "Reply with only query result"
)

emergency_chain = emergency_prompt | ollama_llm
swear_chain = swear_prompt | ollama_llm

search_query_chain = (
    RunnablePassthrough.assign(query=lambda x: x["question"])
    | search_prompt
    | ollama_llm
)

parallel_chain = RunnableParallel(
    emergency=emergency_chain, 
    swear=swear_chain
)







for chat in saved_chats:
    chat_title = chat["title"]
    if st.sidebar.button(chat_title):
        st.session_state.messages = chat["messages"]    
        saveInShortMem(st.session_state.messages)
        st.session_state.running_chat = chat_title
        st.rerun()


# Main Chatbot Section
st.title("Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask me anything..."):

    #save previous messages into short memory
    saveInShortMem(st.session_state.messages)


    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    response = ""

    if st.session_state.use_web_search:
        with st.chat_message("assistant"):
            with st.spinner("Searching the web..."):
                past_memory = memory.load_memory_variables({})["history"]
                if past_memory:
                    input_data = {
                        "previousConversation": past_memory,
                        "question": user_input
                    }
                    search_query = search_query_chain.invoke(input_data)
                    print(search_query)
                    web_results = search_google(search_query)
                    data = web_results[0] if web_results else "No relevant results found."
                    prompt = f"Previous conversation:\n{past_memory}\n\nUsing this data:\n{data}.\nRespond to this prompt:\n{search_query}"
                else:
                    web_results = search_google(user_input)
                    data = web_results[0] if web_results else "No relevant results found."
                    prompt = f"Using this data:\n{data}.\nRespond to this prompt:\n{user_input}"

                response = ollama_llm.invoke(prompt)
                st.markdown(response)


    elif st.session_state.uploaded_file:
        with st.chat_message("assistant"):
            with st.spinner("Processing file..."):
                file_text = extract_text(st.session_state.uploaded_file)
                if file_text:
                    past_memory = memory.load_memory_variables({})["history"]
                    if past_memory:
                        prompt = f"Previous conversation:\n{past_memory}\n\nUsing this document:\n{file_text}\nAnswer this:\n{user_input}"
                    else:
                        prompt = f"Using this document:\n{file_text}\nAnswer this:\n{user_input}"
                    response = ollama_llm.invoke(prompt)
                else:
                    response = "Could not extract text from the file."
                st.markdown(response)

    
    else:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing message..."):

                callback = AlertCallback()

                # Run both checks in parallel
                detection_results = parallel_chain.invoke(
                    {"message": user_input},
                    config={"callbacks": [callback]}
                )
                emergency_result = detection_results["emergency"].strip().upper()
                swear_result = detection_results["swear"].strip().upper()

                callback_result = callback.get_result()
                if callback_result:
                    response = callback_result
                    notifcation_result = callback.get_notification_result()
                    telegramSendMessage(notifcation_result)
                else:
                    past_memory = memory.load_memory_variables({})["history"]
                    if past_memory:
                        prompt = f"Previous conversation:\n{past_memory}\n\nUser: {user_input}"
                    else:
                        prompt = f"User: {user_input}"
                    response = ollama_llm.invoke(prompt)

                st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()