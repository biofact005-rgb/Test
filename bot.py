import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time
import json
import os
from flask import Flask
from threading import Thread

# --- TOKEN AUR ADMIN ID HIDE KAR DIYE GAYE HAIN ---
# Render par Environment Variables mein BOT_TOKEN aur ADMIN_ID set karna na bhulein
TOKEN = os.environ.get("BOT_TOKEN") 
# Agar local testing kar rahe hain toh int() error na de, isliye default 0 lagaya hai.
# Render pe error nahi aayega jab aap variable set kar denge.
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0)) 
CHANNEL_USERNAME = "@errorkidk_05" 

bot = telebot.TeleBot(TOKEN)

# --- LOCAL DATABASE (RAM Storage) ---
bot_data = {
    "menus": {
        "Main Menu": {
            "subfolders": [], 
            "files": [], 
            "parent": "Main Menu"
        }
    },
    "users": [] 
}
user_location = {} 

# --- FLASK SERVER (Render ko zinda rakhne ke liye) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running perfectly on Render!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- LOADING ANIMATION ---
def simulate_loading(chat_id):
    msg = bot.send_message(chat_id, "⏳ <b>Extracting Data...</b>\n<code>[□□□□□□□□□□] 0%</code>", parse_mode="HTML")
    bars = [
        ("■■□□□□□□□□", 20),
        ("■■■■□□□□□□", 40),
        ("■■■■■■■□□□", 70),
        ("■■■■■■■■■■", 100)
    ]
    for bar, percent in bars:
        time.sleep(0.4)
        try:
            bot.edit_message_text(f"⏳ <b>Extracting Data...</b>\n<code>[{bar}] {percent}%</code>", chat_id, msg.message_id, parse_mode="HTML")
        except:
            pass
    bot.delete_message(chat_id, msg.message_id)

# --- KEYBOARDS ---
def get_menu_keyboard(folder_name):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = []
    
    if folder_name in bot_data["menus"]:
        for item in bot_data["menus"][folder_name]["subfolders"]:
            buttons.append(KeyboardButton(item))
            
    if folder_name != "Main Menu":
        markup.add(KeyboardButton("🔙 Back"))
        
    markup.add(*buttons)
    return markup

# ✅ NAYA: Channel Links wala Keyboard wapas add kar diya
def get_links_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📢 Join Channel", url="https://t.me/+WLphTFO-vFJkMjk1")
    btn2 = InlineKeyboardButton("🔔 Bot Updates", url="https://t.me/NM_INFO_1")
    markup.add(btn1, btn2)
    return markup

# --- 1. START & VERIFICATION ---
@bot.message_handler(commands=['start'])
def start_bot(message):
    chat_id = message.chat.id
    
    if chat_id not in bot_data["users"]:
        bot_data["users"].append(chat_id)
        
    user_location[chat_id] = "Verification"
    
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    btn2 = InlineKeyboardButton("✅ Verify", callback_data="verify")
    markup.add(btn1, btn2)
    
    text = (
        "🛑 <b>Access Denied!</b>\n\n"
        f"Is bot ko use karne ke liye aapko hamara official channel {CHANNEL_USERNAME} join karna hoga.\n\n"
        "1️⃣ Pehle 'Join Channel' par click karein.\n"
        "2️⃣ Phir 'Verify' button dabayein."
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# --- CALLBACK QUERY (Verify & Intro) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "verify":
        try:
            status = bot.get_chat_member(CHANNEL_USERNAME, chat_id).status
            if status in ['member', 'administrator', 'creator']:
                bot.delete_message(chat_id, call.message.message_id)
                
                intro_text = (
                    "🎓 <b>Welcome to Allen Test Paper Bot (2026)</b> 🎓\n\n"
                    "✨ <b>India's Best Resource Bot for NEET/JEE Aspirants!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📚 Yahan aapko milenge:\n"
                    "🔹 Latest Allen Minor & Major Tests\n"
                    "🔹 High-Quality PDF Materials\n"
                    "🔹 Detailed Syllabus & Solutions\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Mera maksad aapki preparation ko aur majboot banana hai. Best of luck for 2026!</i>"
                )
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🚀 Start Menu", callback_data="start_menu"))
                bot.send_message(chat_id, intro_text, parse_mode="HTML", reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "⚠️ Bot Server Error! (Make sure bot is admin in channel)", show_alert=True)

    elif call.data == "start_menu":
        bot.delete_message(chat_id, call.message.message_id)
        user_location[chat_id] = "Main Menu"
        markup = get_menu_keyboard("Main Menu")
        bot.send_message(chat_id, "💠 <b>MAIN MENU</b> 💠\n\n👇 <i>Niche diye gaye options select karein:</i>", parse_mode="HTML", reply_markup=markup)
        
        # ✅ NAYA: Main menu ke niche channels ke links bhej diye
        bot.send_message(chat_id, "📌 Hamare Official Channels Join Karein:", reply_markup=get_links_keyboard())

# --- BACKUP & RESTORE SYSTEM ---
@bot.message_handler(commands=['backup'])
def backup_db(message):
    if message.chat.id != ADMIN_ID: return
    with open("backup.json", "w") as f:
        json.dump(bot_data, f)
    with open("backup.json", "rb") as f:
        bot.send_document(ADMIN_ID, f, caption="📂 Database Backup\n(Restore ke liye is file par reply karke /restore likhein)")
    os.remove("backup.json")

@bot.message_handler(commands=['restore'])
def restore_db(message):
    global bot_data
    if message.chat.id != ADMIN_ID: return
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.send_message(ADMIN_ID, "❌ Kripya kisi backup .json file par reply karein.")
        return
    
    file_info = bot.get_file(message.reply_to_message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    try:
        bot_data = json.loads(downloaded_file)
        bot.send_message(ADMIN_ID, "✅ Database successfully restored!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Restore failed: {e}")

# --- ADD FOLDER ---
@bot.message_handler(commands=['addfolder'])
def add_folder(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    current_folder = user_location.get(chat_id, "Main Menu")
    
    try:
        folder_name = "📁 " + message.text.split(" ", 1)[1]
        if folder_name not in bot_data["menus"][current_folder]["subfolders"]:
            bot_data["menus"][current_folder]["subfolders"].append(folder_name)
            bot_data["menus"][folder_name] = {"subfolders": [], "files": [], "parent": current_folder} 
            markup = get_menu_keyboard(current_folder)
            bot.send_message(chat_id, f"✅ Folder '{folder_name}' ban gaya!", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⚠️ Ye folder pehle se hai.")
    except IndexError:
        bot.send_message(chat_id, "❌ Aise likho: /addfolder Minor Test 1")

# --- DELETE LAST FILE ---
@bot.message_handler(commands=['delfile'])
def delete_last_file(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    current_folder = user_location.get(chat_id, "Main Menu")
    
    if len(bot_data["menus"][current_folder]["files"]) > 0:
        bot_data["menus"][current_folder]["files"].pop()
        bot.send_message(chat_id, "🗑️ ✅ Last upload ki hui file delete kar di gayi hai!")
    else:
        bot.send_message(chat_id, "⚠️ Is folder mein delete karne ke liye koi file nahi hai.")

# --- BROADCAST ---
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.id != ADMIN_ID: return
    try:
        msg = message.text.split(" ", 1)[1]
        count = 0
        bot.send_message(ADMIN_ID, "⏳ Broadcasting started...")
        for user_id in bot_data["users"]:
            try:
                bot.send_message(user_id, f"📢 <b>Broadcast:</b>\n\n{msg}", parse_mode="HTML")
                count += 1
            except:
                pass 
        bot.send_message(ADMIN_ID, f"✅ Broadcast Complete! Users received: {count}")
    except IndexError:
        bot.send_message(ADMIN_ID, "❌ Format: /broadcast Hello")

# --- FILE UPLOAD ---
@bot.message_handler(content_types=['document', 'video', 'photo', 'audio'])
def handle_file_upload(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
        
    current_folder = user_location.get(chat_id, "Main Menu")
    file_id, file_type = None, None

    if message.document:
        file_id = message.document.file_id
        file_type = 'document'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.photo:
        file_id = message.photo[-1].file_id 
        file_type = 'photo'
    elif message.audio:
        file_id = message.audio.file_id
        file_type = 'audio'

    bot_data["menus"][current_folder]["files"].append({"id": file_id, "type": file_type})
    bot.send_message(chat_id, f"✅ File Uploaded & Saved!\nTotal files: <b>{len(bot_data['menus'][current_folder]['files'])}</b>", parse_mode="HTML")

# --- NAVIGATION & SENDING FILES ---
@bot.message_handler(func=lambda message: True)
def handle_button_clicks(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "🔙 Back":
        current = user_location.get(chat_id, "Main Menu")
        previous_folder = bot_data["menus"].get(current, {}).get("parent", "Main Menu")
        user_location[chat_id] = previous_folder 
        markup = get_menu_keyboard(previous_folder)
        bot.send_message(chat_id, f"🔙 Aap '{previous_folder}' mein aa gaye.", reply_markup=markup)
        
        # ✅ NAYA: Agar back karke wapas Main Menu mein aaye, toh firse links dikhao
        if previous_folder == "Main Menu":
            bot.send_message(chat_id, "📌 Hamare Official Channels Join Karein:", reply_markup=get_links_keyboard())
        return

    if text in bot_data["menus"]:
        user_location[chat_id] = text 
        markup = get_menu_keyboard(text)
        folder_files = bot_data["menus"][text]["files"]
        
        if len(folder_files) > 0:
            simulate_loading(chat_id)
            for f in folder_files:
                try:
                    caption_text = "Extract by - ERROR"
                    if f["type"] == 'document':
                        bot.send_document(chat_id, f["id"], caption=caption_text, visible_file_name="@errorkidk_05.pdf", protect_content=True)
                    elif f["type"] == 'video':
                        bot.send_video(chat_id, f["id"], caption=caption_text, protect_content=True)
                    elif f["type"] == 'photo':
                        bot.send_photo(chat_id, f["id"], caption=caption_text, protect_content=True)
                    elif f["type"] == 'audio':
                        bot.send_audio(chat_id, f["id"], caption=caption_text, protect_content=True)
                except Exception as e:
                    print(f"Error: {e}")
        else:
            if chat_id != ADMIN_ID:
                bot.send_message(chat_id, f"📂 '{text}' abhi khali hai.")
        
        if chat_id == ADMIN_ID:
            bot.send_message(chat_id, f"⚙️ <b>Admin Panel</b>: '{text}'\nNayi file bhejein ya /addfolder dabayein.", parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"📂 Aap '{text}' ke andar hain.", reply_markup=markup)
        return

# Render server start karna aur phir bot start karna
if __name__ == "__main__":
    keep_alive() # Yeh Render ko btayega ki server chal raha hai
    print("Bot is running perfectly...")
    bot.polling(none_stop=True)
