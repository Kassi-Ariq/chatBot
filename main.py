import ollama
import streamlit as st
from dataSearch import search_google
from dataResponse import getRelevantData


st.title("Data Search Chatbot")

query = st.text_input("Ask me anything:")


if query:
    
    #provide text data
    data = search_google(query)
    text_data = data[0]
    relevent_data = getRelevantData(text_data, query)
    relevant_data_text = "\n".join(relevent_data)

    data_output = ollama.generate(
        model="llama3.2",
        prompt=f"Using this data:\n{relevant_data_text}.\nRespond to this prompt:\n{query}"
    )

    container1 = st.container(border=True)
    container1.write("Chatbot response:")
    container1.write(data_output["response"])
