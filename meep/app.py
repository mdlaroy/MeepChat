import streamlit as st
from chatbot import MeepChatbot
import re

# dont push the damn api key
chatbot = MeepChatbot(openai_key="")

# title
st.title("meep")
st.write("your new pal")

# Persistent session state
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "assistant", "content": "Hello! My name is Meep, your AI companion :) What's your name?"}
    ]
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_personality" not in st.session_state:
    st.session_state.user_personality = ""
if "user_input" not in st.session_state:
    st.session_state.user_input = ""


def process_input():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return

    # user input for convo history
    st.session_state.conversation.append({"role": "user", "content": user_input})

    # add event command
    if user_input.lower().startswith("add event"):
        try:
            # stupid regex thing for format
            match = re.match(r"add event (.+) (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", user_input, re.IGNORECASE)
            if not match:
                raise ValueError("Invalid format. Use: 'add event <description> <YYYY-MM-DD> <HH:MM>'")
            description = match.group(1)
            date = match.group(2)
            time = match.group(3)
            response = chatbot.add_user_event(description, date, time)
            st.session_state.conversation.append({"role": "assistant", "content": response})
        except ValueError as e:
            st.session_state.conversation.append({"role": "assistant", "content": str(e)})
        st.session_state.user_input = ""
        return

    # show events command
    if "upcoming events" in user_input.lower():
        events = chatbot.event_reminders()
        if events:
            response = "\n".join(events)
        else:
            response = "You have no upcoming events."
        st.session_state.conversation.append({"role": "assistant", "content": response})
        st.session_state.user_input = ""
        return

    # show past events command
    if "past events" in user_input.lower():
        past_events = chatbot.event_db.get_past_events(st.session_state.user_name)
        if past_events:
            response = "\n".join([f"{event[0]} on {event[1]} at {event[2]}" for event in past_events])
        else:
            response = "You have no past events."
        st.session_state.conversation.append({"role": "assistant", "content": response})
        st.session_state.user_input = ""
        return

    # preferences requests
    if "preferences" in user_input.lower():
        likes, dislikes = chatbot.get_preferences(st.session_state.user_name)
        likes_list = [item for item in likes]
        dislikes_list = [item for item in dislikes]
        response = (
            # lists preferences but if there is nothing, it will say there is nothing!
            f"You like: {', '.join(likes_list) if likes_list else 'nothing yet'}."
            f" You dislike: {', '.join(dislikes_list) if dislikes_list else 'nothing yet'}."
        )
        st.session_state.conversation.append({"role": "assistant", "content": response})
        st.session_state.user_input = ""
        return

    # user name input
    if not st.session_state.user_name:
        st.session_state.user_name = user_input
        st.session_state.conversation.append({
            "role": "assistant",
            "content": f"Nice to meet you, {st.session_state.user_name}!"
        })
        st.session_state.conversation.append({
            "role": "assistant",
            "content": (
                "Pick my personality:\n"
                "1. Friendly (enthusiastic, warm, casual)\n"
                "2. Empathetic (soothing, supportive, calming)\n"
                "3. Sarcastic (playful, witty, cheeky)\n"
                "4. Humorous (funny, light-hearted, witty)"
            )
        })
        st.session_state.user_input = ""
        return

    # pick ur personality but idk if this is working correctly tbh, i will workshop it later
    if not st.session_state.user_personality:
        personality_options = {
            "1": "friendly",
            "2": "empathetic",
            "3": "sarcastic",
            "4": "humorous"
        }
        selected_personality = personality_options.get(user_input)
        if selected_personality:
            st.session_state.user_personality = selected_personality
            st.session_state.conversation.append({
                "role": "assistant",
                "content": f"Great choice! I'll be {st.session_state.user_personality} from now on."
            })
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "What would you like to chat about?"
            })
        else:
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "I didn't understand that. Please pick a number (1-4) for your personality."
            })
        st.session_state.user_input = ""
        return

    # chat flow
    chatbot.extract_preferences(user_input, st.session_state.user_name)
    emotions = []  # emotional anaylsis (not working but we will workshop this later)
    response = chatbot.generate_response(user_input, emotions)
    st.session_state.conversation.append({"role": "assistant", "content": response})

    # should clear input after processing 
    st.session_state.user_input = ""

# convo histroy
st.markdown("### Conversation History")
for message in st.session_state.conversation:
    if message["role"] == "assistant":
        st.markdown(f"**Meep:** {message['content']}")
    elif message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")

# text input prompt user
st.text_input(
    "Your message:",
    key="user_input",
    placeholder="Type your message here...",
    on_change=process_input
)

# clear conversation button
if st.button("Clear Conversation"):
    st.session_state.conversation = [
        {"role": "assistant", "content": "Hi there! I'm Meep, your AI companion. What's your name?"}
    ]
    st.session_state.user_name = ""
    st.session_state.user_personality = ""
