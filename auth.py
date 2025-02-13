import streamlit as st
import pymongo
import bcrypt
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://Kassiyet:x8mWdUpxZoBOCdta@kassiyet.c2egr.mongodb.net/?retryWrites=true&w=majority&appName=Kassiyet"
client = MongoClient(MONGO_URI)
db = client["chatbotDB"]
users_collection = db["users"]

# Hash password function
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Verify password function
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

# Register User
def register_user(username, email, password):
    if users_collection.find_one({"username": username}):
        return False, "Username already exists. Choose another."
    hashed_pw = hash_password(password)
    users_collection.insert_one({"username": username, "email": email, "password": hashed_pw})
    return True, "Account created successfully! Please log in."

# Login User
def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and verify_password(password, user["password"]):
        st.session_state.logged_in = True
        st.session_state.username = username
        return True, f"Welcome, {username}!"
    return False, "Invalid username or password."

# Logout User
def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.messages = []  # Clear chat history
    st.session_state.uploaded_file = None
