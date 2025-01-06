import os
import json
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import ChatAdminRequiredError
from telethon.errors.rpcerrorlist import PeerIdInvalidError, FloodWaitError
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError, ChannelPrivateError
from telethon.tl.types import PeerUser
from config import *
from time import sleep
from groq import Groq
import logging
import re
import sys
import asyncio  



#read 

#use your phone number for telegram login because some function wont work for bot so make ur own id into a bot
"""
commands:
-info: 
1)get info of you by default
2) info user id or username get their info
3) get reply msg info

-id: get chat id and user id

-/aion - globaly on ai reply for everyone

-/aioff: globally ai off

-/on <userid>: on ai reply for any specific user
-/off <user id>: off 

-/msg <user id><msg> send msg to any user

-/spurge: delete all msg of chat

-/del: delete specific msg

-/echo: reply to any msg of user or user id then bot will echo their msg everytime
-/echend: for echo end
"""

load_dotenv()


api_id = api_id 
api_hash = api_hash  

ADMIN_IDS = ADMIN_IDS  


client = TelegramClient('user_bot', api_id, api_hash)

#groq api key
API_KEY = API_KEY  
groq_client = Groq(api_key=API_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

system_prompt = system_prompt
# Global exception handling
def handle_exception(exc_type, exc_value, exc_tb):
    logging.error(f"Unhandled exception: {exc_type}, {exc_value}, {exc_tb}")

sys.excepthook = handle_exception

# Load or initialize AI status from a JSON file
AI_STATUS_FILE = 'ai_status.json'

def load_ai_status():
    """Load AI status from the JSON file."""
    if os.path.exists(AI_STATUS_FILE):
        with open(AI_STATUS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"global_ai_enabled": False, "user_ai_status": {}}

def save_ai_status(status):
    """Save AI status to the JSON file."""
    with open(AI_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=4)

# Load current AI status
ai_status = load_ai_status()

def add_message(role, content, messages):
    """Add messages to the conversation history."""
    messages.append({"role": role, "content": content})

async def GroqAI(question):
    """Interact with the Groq AI and get a response."""
    try:
        messages = [{"role": "system", "content": system_prompt}]
        add_message("user", question, messages)

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",  # Specify model if needed
        )

        if chat_completion and chat_completion.choices:
            response = chat_completion.choices[0].message.content.strip()
            # Shorten the response and make it more friendly
            friendly_response = f"{response} "
            return friendly_response
        else:
            return "I couldn't get an answer for that. Please try again! 😊💪"
    except Exception as e:
        logging.error(f"Error interacting with Groq AI: {e}")
        return "Oops! Something went wrong. Try again later. 😊💪"

# Helper function to check if the user is an admin
def is_admin(user_id):
    return user_id in ADMIN_IDS



@client.on(events.NewMessage(pattern='/id'))
async def id_command(event):
    """Handles the '/id' command to get user and chat ID."""
    try:
        # Delay execution by 0.5 seconds
        await asyncio.sleep(0.5)

        user_id = event.sender_id
        chat_id = event.chat_id if event.chat_id else "Not available"
        
        # Respond with user and chat ID
        await event.respond(f"User ID: <code>{user_id}</code>\nChat ID: <code>{chat_id}</code>", parse_mode='html')

    except Exception as e:
        logging.error(f"Error handling /id command: {e}")
        await event.respond("Oops! Something went wrong while processing the '/id' command. Please try again later.", parse_mode='html')

@client.on(events.NewMessage(pattern='/info'))
async def info(event):
    """Handles the '/info' command."""
    try:
        # Delay execution by 0.5 seconds
        await asyncio.sleep(0.5)

        if event.is_reply:
            replied_msg = await event.get_reply_message()
            if replied_msg:  # Ensure the replied message exists
                user = replied_msg.sender_id
                user_info = await get_user_info(user)
                await event.respond(user_info, parse_mode='html')
            else:
                await event.respond("❌ sorry couldnot find info of this user", parse_mode='html')
        
        elif event.message.text.strip() != '/info':
            match = re.match(r'/info\s+(@?[A-Za-z0-9_]{5,32})', event.message.text.strip())  # Improved username regex
            if match:
                username = match.group(1)
                user_info = await get_user_info(username)
                await event.respond(user_info, parse_mode='html')
            else:
                await event.respond("❌ Invalid username format. Please use '@username' or 'username'.", parse_mode='html')
        else:
            # If no reply and no username, return info of the user who sent the command
            user_info = await get_user_info(event.sender_id)
            await event.respond(user_info, parse_mode='html')

    except Exception as e:
        logging.error(f"Error handling /info command: {e}")
        await event.respond("⚠️ sorry i couldn't find info regarding this.. are you sure i have meet them before", parse_mode='html')


async def get_user_info(user):
    try:
        if isinstance(user, int):
            user_info = await client.get_entity(user)
        elif isinstance(user, str):
            if user.startswith('@'):
                user_info = await client.get_entity(user)
            else:
                try:
                    user_info = await client.get_entity(int(user))  # Try converting to an ID
                except ValueError:
                    user_info = await client.get_entity(user)  # Treat as username if not an ID
        else:
            return "❌ Invalid user information format."

        first_name = f"<code>{user_info.first_name}</code>" if user_info.first_name else "Not set"
        last_name = f"<code>{user_info.last_name}</code>" if user_info.last_name else "Not set"
        
        # Check if the user has a username, and use their ID if they don't
        if user_info.username:
            username = f"@{user_info.username}"
            profile_link = f"<a href='@{user_info.username}'>Profile Link</a>"
        else:
            username = "Not set"
            profile_link = "No profile link"
        
        user_id = f"<code>{user_info.id}</code>"

        return (f"<b>Info of user:</b>\n"
                f"😊 <b>First Name</b>: {first_name}\n"
                f"📝 <b>Last Name</b>: {last_name}\n"
                f"👤 <b>Username</b>: {username}\n"
                f"🆔 <b>User ID</b>: {user_id}\n"
                f"🔗 <b>Profile Link</b>: {profile_link}")
    
    except ValueError:
        logging.error(f"Invalid user ID or username: {user}")
        return "❌ Invalid user ID or username. Please check the input and try again."
    except Exception as e:
        logging.error(f"Error fetching user info: {e}")
        return "⚠️ Could not fetch user info. Please try again later."

# Command handlers for admin-only commands
@client.on(events.NewMessage(pattern='/on'))
async def ai_on_command(event):
    """Handles the '/on' command to enable AI for a specific user."""
    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    try:
        if event.message.text.strip() == "on":
            await event.respond("Please provide a user ID to enable AI for that user. Example: /on <user_id>")
            return

        user_id = event.message.text.split()[1]
        ai_status["user_ai_status"][user_id] = True
        save_ai_status(ai_status)
        await event.respond(f"AI has been enabled for user with ID {user_id}.")
    except Exception as e:
        logging.error(f"Error handling /on command: {e}")
        await event.respond("❌ Failed to enable AI for the specified user.")

@client.on(events.NewMessage(pattern='/off'))
async def ai_off_command(event):
    """Handles the '/off' command to disable AI for a specific user."""
    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    try:
        if event.message.text.strip() == "off":
            await event.respond("Please provide a user ID to disable AI for that user. Example: /off <user_id>")
            return

        user_id = event.message.text.split()[1]
        ai_status["user_ai_status"][user_id] = False
        save_ai_status(ai_status)
        await event.respond(f"AI has been disabled for user with ID {user_id}.")
    except Exception as e:
        logging.error(f"Error handling /off command: {e}")
        await event.respond("❌ Failed to disable AI for the specified user.")

@client.on(events.NewMessage(pattern='/aion'))
async def ai_global_on(event):
    """Handles the '/aion' command to enable AI globally."""
    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    ai_status["global_ai_enabled"] = True
    save_ai_status(ai_status)
    await event.respond("Global AI has been enabled for all users.")

@client.on(events.NewMessage(pattern='/aioff'))
async def ai_global_off(event):
    """Handles the '/aioff' command to disable AI globally."""
    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    ai_status["global_ai_enabled"] = False
    save_ai_status(ai_status)
    await event.respond("Global AI has been disabled for all users.")

# Check AI status before responding
@client.on(events.NewMessage)
async def chatbot_response(event):
    """Handles all incoming messages and replies using Groq AI."""
    user_input = event.message.text.strip()

    # Ignore all commands (messages starting with '/')
    if user_input.startswith('/'):
        return  # Do nothing for commands

    # Handle regular messages (not commands)
    if user_input.lower() == "exit":
        await event.respond("Goodbye! 😊💪")
    else:
        user_id = str(event.sender_id)
        if ai_status["global_ai_enabled"] or ai_status["user_ai_status"].get(user_id, False):
            # Get Groq AI response
            response = await GroqAI(user_input)
            # Send Groq AI response back to Telegram
            await event.reply(response)


@client.on(events.NewMessage(pattern='/spurge'))
async def spurge_command(event):
    """Handles the '/spurge' command to delete all messages starting from a specific message."""
    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    try:
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            if replied_msg:
                # Get the message ID that was replied to
                start_msg_id = replied_msg.id
                messages_to_delete = []
                
                # Collect all messages starting from the replied-to message up to the most recent one
                async for message in client.iter_messages(event.chat_id, reverse=True):
                    if message.id <= start_msg_id:
                        messages_to_delete.append(message)
                
                # Now, delete all the messages one by one
                for message in messages_to_delete:
                    await message.delete()

                # Delete the /spurge command itself
                await event.delete()
            else:
                await event.reply("❌ No message to reply to for spurge.", parse_mode='html')
        else:
            await event.reply("❌ You must reply to a message to use /spurge.", parse_mode='html')
    except Exception as e:
        logging.error(f"Error handling /spurge command: {e}")
        await event.reply("⚠️ Something went wrong while trying to delete the messages.", parse_mode='html')




@client.on(events.NewMessage)
async def msg_handler(event):
    # Check if the sender is an admin
    if event.sender_id not in ADMIN_IDS:
        return

    # Check if the message starts with /msg
    if event.text.startswith('/msg'):
        try:
            # Split the command to extract user ID and message
            parts = event.text.split(maxsplit=2)

            # Ensure the message is correctly formatted
            if len(parts) < 3:
                await event.reply("⚠️ Usage: /msg <user_id> <message>")
                return

            # Extract the user ID and the message
            try:
                user_id = int(parts[1])
            except ValueError:
                await event.reply("⚠️ Invalid user ID. Please provide a valid numeric user ID.")
                return

            message = parts[2]

            # Send the message to the user
            try:
                await client.send_message(PeerUser(user_id), message)
                await event.reply(f"✅ Message sent to {user_id}")

            except PeerFloodError:
                await event.reply("❌ You have been rate-limited. Please try again later.")
            except UserPrivacyRestrictedError:
                await event.reply("❌ The user has restricted privacy settings and cannot receive your message.")
            except ChannelPrivateError:
                await event.reply("❌ The channel or user is private and cannot be contacted.")
            except Exception as e:
                await event.reply(f"❌ An unexpected error occurred: {str(e)}")

        except Exception as e:
            # Catch unexpected exceptions at a higher level
            await event.reply(f"❌ An error occurred while processing your request: {str(e)}")
            # Optionally log the exception for further debugging
            print(f"Error: {str(e)}")


@client.on(events.NewMessage(pattern='/del'))
async def del_command(event):
    """Handles the '/del' command to delete a specific message."""

    if not is_admin(event.sender_id):
        await event.respond("❌ You do not have permission to use this command.")
        return

    if not event.is_reply:
            await event.reply("❌ You must reply to a message to use /del.", parse_mode='html')
            return

    try:
        message_to_delete = await event.get_reply_message()
        await message_to_delete.delete()  # Delete the specific message
        await event.delete()  # Delete the /del command message itself
    except Exception as e:
        logging.error(f"Error handling /del command: {e}")
        await event.reply("⚠️ Something went wrong while trying to delete the message.", parse_mode='html')





def load_data():
    try:
        with open('echo_data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    with open('echo_data.json', 'w') as f:
        json.dump(data, f, indent=4)


echo_enabled = load_data()


@client.on(events.NewMessage(pattern='/echo'))
async def echo_on(event):
    try:
       
        if event.sender_id not in ADMIN_IDS:
            await event.respond("❌ Only the bot admins can use this command.")
            return
        
        if event.reply_to_msg_id:
            # Enable echo for the user who sent the replied message
            original_msg = await event.get_reply_message()
            user_id = original_msg.sender_id
            echo_enabled[user_id] = True  # Set echo to True
            save_data(echo_enabled)  # Save changes to the JSON file
            await event.respond(f"✅ Echo enabled for user {user_id}!\nThey will now receive an echo of their messages.")
        else:
            # If no reply, expect a user ID
            parts = event.message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1])
                    echo_enabled[user_id] = True  # Set echo to True
                    save_data(echo_enabled)  # Save changes to the JSON file
                    await event.respond(f"✅ Echo enabled for user {user_id}!\nThey will now receive an echo of their messages.")
                except ValueError:
                    await event.respond("❌ Invalid user ID format. Please use a valid numeric user ID.")
            else:
                await event.respond("❌ Invalid command format. Use `/echo user_id` or reply to a message.")
    
    except PeerIdInvalidError:
        await event.respond("❌ User ID is invalid.")
    except FloodWaitError as e:
        await event.respond(f"⏳ Please wait for {e.seconds} seconds before trying again.")
        sleep(e.seconds)
    except Exception as e:
        await event.respond(f"❌ An unexpected error occurred: {str(e)}")
        logging.error(f"Error in /echo command: {str(e)}")

# Command to disable echo for a user
@client.on(events.NewMessage(pattern='/echend'))
async def echo_off(event):
    try:
        # Check if the sender is an admin
        if event.sender_id not in ADMIN_IDS:
            await event.respond("❌ Only the bot admins can use this command.")
            return

        if event.reply_to_msg_id:
            # Disable echo for the user who sent the replied message
            original_msg = await event.get_reply_message()
            user_id = original_msg.sender_id
            if user_id in echo_enabled:
                echo_enabled[user_id] = False  # Set echo to False
                save_data(echo_enabled)  # Save changes to the JSON file
                await event.respond(f"✅ Echo disabled for user {user_id}.")
            else:
                await event.respond(f"❌ Echo is not enabled for user {user_id}.")
        else:
            # If no reply, expect a user ID
            parts = event.message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1])
                    if user_id in echo_enabled:
                        echo_enabled[user_id] = False  # Set echo to False
                        save_data(echo_enabled)  # Save changes to the JSON file
                        await event.respond(f"✅ Echo disabled for user {user_id}.")
                    else:
                        await event.respond(f"❌ Echo is not enabled for user {user_id}.")
                except ValueError:
                    await event.respond("❌ Invalid user ID format. Please use a valid numeric user ID.")
            else:
                await event.respond("❌ Invalid command format. Use `/echend user_id` or reply to a message.")
    
    except PeerIdInvalidError:
        await event.respond("❌ User ID is invalid.")
    except FloodWaitError as e:
        await event.respond(f"⏳ Please wait for {e.seconds} seconds before trying again.")
        sleep(e.seconds)
    except Exception as e:
        await event.respond(f"❌ An unexpected error occurred: {str(e)}")
        logging.error(f"Error in /echend command: {str(e)}")

# Main function to listen for messages and reply
@client.on(events.NewMessage())
async def echo_messages(event):
    try:
        if event.sender_id in echo_enabled and echo_enabled[event.sender_id]:
            # Reply with the same message
            await event.respond(f" {event.text}")
    except Exception as e:
        logging.error(f"Error in message echo: {str(e)}")



# Start the bot
client.start()
client.run_until_disconnected()
