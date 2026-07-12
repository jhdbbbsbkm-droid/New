import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading

# --- AAPKI DETAILS ---
BOT_TOKEN = "8770445986:AAF4xwpxUvivXnxId1jDF3ZaCOV4U_Imz7E"
API_KEY = "nxa_75ffb927199d51a425dee389e89697fd727fef03"
BASE_URL = "http://nexaotpservice.com/api/v1"

bot = telebot.TeleBot(BOT_TOKEN)

# Headers jo Nexa OTP Service ke liye chahiye
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📱 Get Number", callback_data="get_number"))
    bot.send_message(
        message.chat.id, 
        "🤖 **Nexa OTP Bot** mein aapka swagat hai!\n\nVirtual number lene ke liye niche button par click karein:", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "get_number")
def handle_get_number(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, "Number request kiya ja raha hai...")
    bot.send_message(chat_id, "⏳ Nexa Server se number fetch ho raha hai, kripya intezar karein...")

    # Telegram service aur India (IN) country ke liye request
    payload = {"service": "telegram", "country": "IN"} 
    
    try:
        response = requests.post(f"{BASE_URL}/numbers/get", json=payload, headers=HEADERS).json()
        
        if "number" in response:
            num = response["number"]
            num_id = response["number_id"]
            
            msg_text = f"✅ **Aapka Number Mil Gaya Hai!**\n\n📞 **Number:** `{num}`\n\n⏳ Bot background me OTP ka wait kar raha hai. Jaise hi OTP aayega, aapko yahan turant dikhayega."
            bot.send_message(chat_id, msg_text, parse_mode="Markdown")
            
            # Background thread shuru karna taaki bot freeze na ho
            threading.Thread(target=wait_for_otp_worker, args=(chat_id, num_id)).start()
        else:
            bot.send_message(chat_id, "❌ Error: Nexa server par abhi koi number khali nahi hai ya balance kam hai.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: Site se connect nahi ho paya. ({str(e)})")

def wait_for_otp_worker(chat_id, number_id):
    max_attempts = 36  # 3 minutes tak check karega (36 * 5 seconds)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            sms_url = f"{BASE_URL}/numbers/{number_id}/sms"
            response = requests.get(sms_url, headers=HEADERS).json()
            
            if response.get("sms") and len(response["sms"]) > 0:
                latest_sms = response["sms"][0]
                otp_code = latest_sms.get("otp", "N/A")
                full_text = latest_sms.get("text", "No text")
                
                success_msg = f"📩 **🎉 OTP AA GAYA HAI!**\n\n🔢 **OTP Code:** `{otp_code}`\n📝 **Full SMS:** {full_text}"
                bot.send_message(chat_id, success_msg, parse_mode="Markdown")
                return # OTP mil gaya, loop band
        except Exception as e:
            print(f"Polling error: {e}")
            
        time.sleep(5)
        attempt += 1
        
    bot.send_message(chat_id, f"❌ **Timeout!** Number (ID: {number_id}) par 3 minute tak koi OTP nahi aaya.")

if __name__ == "__main__":
    print("🤖 Telegram Bot successfully start ho gaya hai...")
    bot.infinity_polling()
