from datetime import datetime
import streamlit as st
import uuid
import requests
from PIL import Image  # For loading avatar images

# Backend URLs for Docker Compose networking
SAVE_CHAT_URL = "http://backend-service:5000/save_chat/"
DELETE_CHAT_URL = "http://backend-service:5000/delete_chat/"
UPLOAD_IMAGE_URL = "http://backend-service:5000/upload_image/"
IMAGE_RECOGNITION_URL = "http://backend-service:5000/image_recognition/"
CHAT_URL = "http://backend-service:5000/chat/"
LOAD_CHAT_URL = "http://backend-service:5000/load_chat/"

# Initialize session state
if "history_chats" not in st.session_state:
    st.session_state["history_chats"] = []
if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = None
if "chat_names" not in st.session_state:
    st.session_state["chat_names"] = {}

# ------------------------------
# Avatar Helper (from Code 1)
# ------------------------------
def avatar_updater(role):
    """
    Return the appropriate avatar image path based on the message role.
    For assistant messages, choose between a normal or error avatar.
    For user messages, return the default user avatar.
    """
    # Adjust paths as necessary:
    path_bot = "Image_gallery/bot.png"
    path_user = "Image_gallery/user.png"
    if role == "assistant":
        return path_bot
    else:
        return path_user

# ------------------------------
# Chat Management Functions (from Code 2)
# ------------------------------
def load_chats_from_db():
    response = requests.get(LOAD_CHAT_URL)
    if response.status_code == 200:
        records = response.json()
        for record in records:
            chat_id = record['id']
            messages = record['messages']
            name = record['chat_name']
            image_url = record.get('image_url')
            image_name = record.get('image_name')
            st.session_state["history_chats"].append({
                "id": chat_id, 
                "messages": messages, 
                "image_url": image_url,
                "image_name": image_name
            })
            st.session_state["chat_names"][chat_id] = name
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

def save_chat_to_db(chat_id, chat_name, messages, image_url=None, image_name=None):
    payload = {
        "chat_id": chat_id,
        "chat_name": chat_name,
        "messages": messages,
        "image_url": image_url,
        "image_name": image_name
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(SAVE_CHAT_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to save data. Status code: {response.status_code}")

def create_chat_with_image(chat_name, uploaded_image):
    with st.spinner("Uploading and Processing image, please wait..."):
        files = {"file": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
        response = requests.post(UPLOAD_IMAGE_URL, files=files)
        if response.status_code == 200:
            data = response.json()
            image_url = data["image_url"]
            image_name = data["image_name"]
            new_chat_id = str(uuid.uuid4())
            new_chat = {
                "id": new_chat_id, 
                "messages": [], 
                "image_url": image_url,
                "image_name": image_name
            }
            st.session_state["history_chats"].insert(0, new_chat)
            st.session_state["chat_names"][new_chat_id] = chat_name
            st.session_state["current_chat"] = new_chat_id
            save_chat_to_db(new_chat_id, chat_name, [], image_url, image_name)
            st.success("Successed!")
        else:
            st.error("Failed to upload image.")

def create_chat(chat_name):
    new_chat_id = str(uuid.uuid4())
    new_chat = {
        "id": new_chat_id, 
        "messages": [], 
        "image_url": None,
        "image_name": None
    }
    st.session_state["history_chats"].insert(0, new_chat)
    st.session_state["chat_names"][new_chat_id] = chat_name
    st.session_state["current_chat"] = new_chat_id
    save_chat_to_db(new_chat_id, chat_name, [])

def delete_chat():
    if st.session_state["current_chat"]:
        chat_id = st.session_state["current_chat"]
        st.session_state["history_chats"] = [
            chat for chat in st.session_state["history_chats"] if chat["id"] != chat_id
        ]
        del st.session_state["chat_names"][chat_id]
        payload = {"chat_id": chat_id}
        headers = {"Content-Type": "application/json"}
        response = requests.post(DELETE_CHAT_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Failed to delete data. Status code: {response.status_code}")
        st.session_state["current_chat"] = (
            st.session_state["history_chats"][0]["id"] if st.session_state["history_chats"] else None
        )

def select_chat(chat_id):
    st.session_state["current_chat"] = chat_id

# Load chats from database on start
load_chats_from_db()

# ------------------------------
# Sidebar: Chat Management & Image Upload
# ------------------------------
with st.sidebar:
    st.title("Chat Management")
    
    # Chat name input
    chat_name = st.text_input("Enter Chat Name:", key="new_chat_name")
    
    # Create regular chat button
    if st.button(":material/add: Create New Chat"):
        if chat_name.strip():
            create_chat(chat_name.strip())
        else:
            st.warning("Chat name cannot be empty.")
    
    # Image upload section
    st.subheader("Image Chat")
    uploaded_image = st.file_uploader("Upload Image 🖼️:", type=["png", "jpg", "jpeg", "webp"], key="image_uploader")
    if st.button(":material/image: Create New Chat with Image"):
        if not uploaded_image:
            st.warning("Please upload an image file before creating the chat.")
        elif chat_name.strip():
            create_chat_with_image(chat_name.strip(), uploaded_image)
        else:
            st.warning("Chat name cannot be empty.")
    
    # Chat selection
    if st.session_state["history_chats"]:
        st.subheader("Your Chats")
        chat_options = {
            chat["id"]: st.session_state["chat_names"][chat["id"]]
            for chat in st.session_state["history_chats"]
        }
        selected_chat = st.radio(
            "Select Chat",
            options=list(chat_options.keys()),
            format_func=lambda x: chat_options[x],
            key="chat_selector",
            on_change=lambda: select_chat(st.session_state.chat_selector),
        )
        st.session_state["current_chat"] = selected_chat
        st.button(":material/delete: Delete Chat", on_click=delete_chat)

# ------------------------------
# Main Content: Chat Interface with Avatars
# ------------------------------
st.header("Chatbot Application")
if st.session_state["current_chat"]:
    chat_id = st.session_state["current_chat"]
    chat_name = st.session_state["chat_names"][chat_id]
    st.info(f"Current Chat: {chat_name}")

    current_chat = next(
        (chat for chat in st.session_state["history_chats"] if chat["id"] == chat_id),
        None,
    )

    # If the chat has no messages yet, insert a default bot greeting
    if current_chat and not current_chat["messages"]:
        if current_chat.get("image_url"):
            greeting = "Hello, you have uploaded an image. What would you like to know about it?"
        else:
            greeting = "Hello, how can I help you today?"
        initial_message = {
            "role": "assistant",
            "content": greeting,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        current_chat["messages"].append(initial_message)
        save_chat_to_db(
            chat_id,
            chat_name,
            current_chat["messages"],
            current_chat.get("image_url"),
            current_chat.get("image_name")
        )

    if current_chat:
        # Display associated file info if exists
        if current_chat["image_url"]:
            st.info(f"Associated Image: {current_chat['image_name']}")
            # Convert web path to local file path for Streamlit
            image_path = current_chat["image_url"].lstrip("/")
            st.image(image_path, use_container_width=True)

        # Display chat messages with avatars
        for message in current_chat["messages"]:
            role = message["role"]
            avatar_path = avatar_updater(role)
            avatar_img = Image.open(avatar_path)
            with st.chat_message(role, avatar=avatar_img):
                st.caption(message.get("time", ""))
                st.markdown(f'{message["content"]}')

        # Chat input section
        prompt = st.chat_input("Your Message:")
        if prompt:
            user_message = {
                "role": "user",
                "content": prompt,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            current_chat["messages"].append(user_message)
            with st.chat_message("user", avatar=Image.open(avatar_updater("user"))):
                st.caption(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.markdown(prompt)

            # Prepare payload for backend
            payload = {
                "messages": [
                    {"role": m["role"], "content": m["content"]}
                    for m in current_chat["messages"]
                ]
            }
            headers = {"Content-Type": "application/json"}
            
            # Determine which endpoint to use based on chat type
            if current_chat.get("image_url"):
                payload["image_url"] = current_chat["image_url"]
                chat_target_url = IMAGE_RECOGNITION_URL
            else:
                chat_target_url = CHAT_URL

            # Function to stream backend response
            def get_stream_response():
                with requests.post(chat_target_url, json=payload, headers=headers, stream=True) as r:
                    for chunk in r:
                        yield chunk.decode("utf-8")

            # Display bot response with avatar while streaming
            bot_avatar = Image.open(avatar_updater("assistant"))
            response_text = ""
            get_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with st.chat_message("assistant", avatar=bot_avatar):
                time = st.empty()
                text = st.empty()
                with st.spinner(' '):
                    for chunk in get_stream_response():
                        response_text += chunk
                    # Update the message continuously with the streamed text
                    time.caption(get_time)
                    text.text(response_text)

            # Append the complete bot response to chat history
            bot_message = {
                "role": "assistant",
                "content": response_text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            current_chat["messages"].append(bot_message)
            save_chat_to_db(
                chat_id,
                chat_name,
                current_chat["messages"],
                current_chat.get("image_url"),
                current_chat.get("image_name")
            )
else:
    st.write("No chat selected. Use the sidebar to create or select a chat.")