import streamlit as st
import ollama
from dataSearch import search_google
from dataResponse import getRelevantData

st.set_page_config(page_title="Llama3.2 Chatbot with Web Search", layout="wide")

# Initialize chat history & toggle state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False

# Web search toggle
st.session_state.use_web_search = st.checkbox("Enable Web Search", value=False)

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Default response variable (prevents NameError)
    response = ""

    # If web search is enabled, fetch data from the internet
    if st.session_state.use_web_search:
        with st.chat_message("assistant"):
            with st.spinner("Searching the web..."):
                web_results = search_google(user_input)  # Fetch web results
                data = web_results[0] if web_results else "No relevant results found."
                relevant_data = getRelevantData(data, user_input)
                relevant_data_text = "\n".join(relevant_data)

                data_output = ollama.generate(
                    model="llama3.2",
                    prompt=f"Using this data:\n{relevant_data_text}.\nRespond to this prompt:\n{user_input}"
                )
                response = data_output['response']  # Ensure response is always assigned
                st.markdown(response)

    else:  # Otherwise, use the chatbot (Llama3.2)
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
