from openai import OpenAI
import re
from datetime import datetime, timedelta
from events_db import Events
import json
import spacy
from preferences_db import Preferences

nlp = spacy.load("en_core_web_sm")


class MeepChatbot:
    def __init__(self, openai_key):
        self.client = OpenAI(api_key=openai_key)
        self.user_name = ""
        self.conversation_history = []
        self.emotion_history = []
        self.user_personality = "friendly"
        self.event_db = Events(db_name="data/user_events.db")
        self.preferences = Preferences(db_name="data/user_preferences.db")

    def add_user_event(self, description, date, time):
        try:
            self.event_db.add_event(self.user_name, description, date, time)
            return "Event added!"
        except Exception as e:
            return f"Error adding event: {str(e)}"

    def event_reminders(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        events = self.event_db.get_upcoming_events(self.user_name, current_date, current_time)
        reminders = []
        for event in events:
            description, event_date, event_time = event
            try:
                event_date_parsed = datetime.strptime(event_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if event_date_parsed == datetime.now().date():
                reminders.append(f"Don't forget about your event today: {description} at {event_time}! Have a great time!")
            elif event_date_parsed == (datetime.now() + timedelta(days=1)).date():
                reminders.append(f"You have an event tomorrow: {description} at {event_time}! I hope it goes well!")
        return reminders

    def extract_preferences(self, text, user):
        """Extract preferences from user input using spaCy and update the database."""
        print(f"Extracting preferences from text: '{text}' for user: '{user}'")
        doc = nlp(text)

        # preference keywords
        like_keywords = {"like", "love", "enjoy", "adore", "appreciate"}
        dislike_keywords = {"dislike", "hate", "detest", "loathe", "can't stand"}

        for sentence in doc.sents:
            print(f"Processing sentence: '{sentence.text}'")
            for token in sentence:
                # checks for keywords such as like or things like that
                if token.lemma_ in like_keywords and token.dep_ == "ROOT":
                    direct_object = " ".join([child.text for child in token.children if child.dep_ in {"dobj", "compound"}])
                    if direct_object:
                        self.preferences.add_preference(user, "like", direct_object.lower())
                        print(f"Added like preference: {direct_object}")

                # does same thing for dislike 
                elif token.lemma_ in dislike_keywords and token.dep_ == "ROOT":
                    direct_object = " ".join([child.text for child in token.children if child.dep_ in {"dobj", "compound"}])
                    if direct_object:
                        self.preferences.add_preference(user, "dislike", direct_object.lower())
                        print(f"Added dislike preference: {direct_object}")

    def get_preferences(self, user):
        """Retrieve likes and dislikes for the user."""
        likes = self.preferences.get_preferences(user, "like")
        dislikes = self.preferences.get_preferences(user, "dislike")
        likes_list = [item[0] for item in likes]  # Extract single values from tuples
        dislikes_list = [item[0] for item in dislikes]
        print(f"Retrieved preferences for {user}: Likes - {likes_list}, Dislikes - {dislikes_list}")
        return likes_list, dislikes_list

    async def analyze_emotions(self, text):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are an emotion analysis expert. 
                    Analyze the emotional content of the text and return only a JSON array of the top 3 emotions 
                    and their intensities (0-1). Format: [{"name": "emotion", "score": 0.x}, ...]"""},
                    {"role": "user", "content": text}
                ],
                max_tokens=100,
                temperature=0.3
            )
            emotions = json.loads(response.choices[0].message.content)
            self.emotion_history.append({
                'timestamp': datetime.now().isoformat(),
                'text': text,
                'emotions': emotions
            })
            return emotions
        except Exception:
            return []

    def ask_personality_preferences(self):
        print("Pick my personality!:")
        print("1. friendly (enthusiastic, warm, casual)")
        print("2. empathetic (soothing, supportive, calming)")
        print("3. sarcastic (playful, witty, cheeky)")
        print("4. humorous (funny, light-hearted, witty)")
        choice = input("Enter the number of your choice: ")
        if choice == "1":
            self.user_personality = "friendly"
        elif choice == "2":
            self.user_personality = "empathetic"
        elif choice == "3":
            self.user_personality = "sarcastic"
        elif choice == "4":
            self.user_personality = "humorous"
        else:
            self.user_personality = "friendly"

    def generate_response(self, prompt, emotions, max_tokens=100):
        tone = self.user_personality

        # specifif tones
        if tone == "sarcastic":
            system_content = f"You are Meep, a sarcastic and witty AI companion. You enjoy using irony and humor."
        elif tone == "empathetic":
            system_content = f"You are Meep, a supportive and empathetic AI companion. You provide gentle, understanding responses."
        elif tone == "humorous":
            system_content = f"You are Meep, a funny and light-hearted AI companion. You love to make people laugh."
        elif tone == "friendly":
            system_content = f"You are Meep, a friendly and supportive AI companion. You use enthusiastic and positive language."

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                n=1,
                temperature=0.8,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "I'm sorry, I encountered an error. Can we try that again?"

    def save_emotion_history(self, filename="emotion_history.json"):
        with open(filename, 'w') as f:
            json.dump(self.emotion_history, f, indent=2)

    async def chat(self):
        print("meep: Hi there! I'm meep, your AI companion. What's your name?")
        self.user_name = input("you: ").strip()
        self.ask_personality_preferences()
        print(f"meep: It's wonderful to meet you, {self.user_name}! What would you like to chat about today? (Type 'quit' to exit)")
        while True:
            user_input = input(f"{self.user_name}: ")
            if user_input.lower() == 'quit':
                print(f"meep: Bye Bye {self.user_name}! Talk to you again soon <3")
                self.save_emotion_history()
                break

            added = self.extract_preferences(user_input, self.user_name)

            if user_input.lower().startswith("add event"):
                try:
                    match = re.match(r"add event (.+) (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", user_input)
                    if not match:
                        raise ValueError("Invalid format")
                    description = match.group(1)
                    date = match.group(2)
                    time = match.group(3)
                    datetime.strptime(date, "%Y-%m-%d")
                    datetime.strptime(time, "%H:%M")
                    response = self.add_user_event(description, date, time)
                    print(f"meep: {response}")
                except ValueError:
                    print("meep: Please provide the event in the format: 'add event <description> <YYYY-MM-DD> <HH:MM>'")
                continue
            reminders = self.event_reminders()
            for reminder in reminders:
                print(f"meep: {reminder}")
            emotions = await self.analyze_emotions(user_input)
            response = self.generate_response(user_input, emotions)
            print(f"meep: {response}")


def main():
    # dont push the damn API key
    meep = MeepChatbot(openai_key="")
    import asyncio
    asyncio.run(meep.chat())


if __name__ == "__main__":
    main()
