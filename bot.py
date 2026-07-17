import os
import logging
import threading
import yt_dlp
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dummy Server (Render အတွက်)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Dummy server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Environment Variables မှ Telegram Token ယူခြင်း
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- တရားတော် ရှာဖွေခြင်းနှင့် ပို့ခြင်း Logic (အသစ်ပြင်ဆင်ထားသည်) ---
async def process_download(query, message_object, context):
    """တရားတော် ရှာဖွေပြီး အသံဖိုင်ပို့မည့် အဓိက Function"""
    status_message = await message_object.reply_text(f"'{query}' တရားတော်ကို ရှာဖွေပြီး အသံဖိုင် ပြောင်းလဲနေပါတယ်... ခဏစောင့်ပေးပါ 🙏")

    ydl_opts_search = {'format': 'bestaudio/best', 'default_search': 'ytsearch1', 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' not in info or not info['entries']:
                await status_message.edit_text("တောင်းပန်ပါတယ်ခင်ဗျာ၊ အဆိုပါတရားတော်ကို ရှာမတွေ့ပါ။")
                return

            video_data = info['entries'][0]
            video_url = video_data['webpage_url']
            title = video_data.get('title', 'တရားတော်')
            duration = video_data.get('duration', 0)

            if duration > 1800:
                await status_message.edit_text("⚠️ ဤတရားတော်သည် မိနစ် ၃၀ ကျော်လွန်နေသဖြင့် အသံဖိုင်ပြောင်းလဲ၍ မရနိုင်ပါ။")
                return

            filename = f"dhamma_{video_data['id']}"
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                ydl_down.download([video_url])

            audio_file_path = f"{filename}.mp3"
            if os.path.exists(audio_file_path):
                await status_message.delete()
                with open(audio_file_path, 'rb') as audio:
                    await message_object.reply_audio(audio=audio, title=title, performer="Daily Buddha Bot")
                os.remove(audio_file_path)
            else:
                await status_message.edit_text("အသံဖိုင် ပြောင်းလဲခြင်း မအောင်မြင်ပါ။")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await status_message.edit_text("တရားတော်ကို ဒေါင်းလုဒ်ဆွဲရာတွင် အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။")

# --- Commands & Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = "မင်္ဂလာပါဗျာ 🙏\n\nDaily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\nတရားတော်အမည်ကို ရိုက်ထည့်ပြီး ရှာဖွေနိုင်ပါတယ်ဗျာ။"
    await update.message.reply_text(start_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # ပရိတ်ကြီး ၁၁ သုတ် ရှာဖွေမှုအတွက် မီနူးပြခြင်း
    if "ပရိတ်" in user_text:
        keyboard = [
            [InlineKeyboardButton("✨ မေတ္တာသုတ်", callback_data="မေတ္တာသုတ်"), InlineKeyboardButton("✨ ရတနသုတ်", callback_data="ရတနသုတ်")],
            [InlineKeyboardButton("✨ ခန္ဓသုတ်", callback_data="ခန္ဓသုတ်"), InlineKeyboardButton("✨ မောရသုတ်", callback_data="မောရသုတ်")]
        ]
        await update.message.reply_text("နာယူလိုသော သုတ်တော်ကို ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # ပုံမှန်ရှာဖွေမှု
        await process_download(user_text, update.message, context)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ခလုတ်နှိပ်လိုက်လျှင် ရှာဖွေခြင်းလုပ်ငန်းစဉ်ကို စတင်မည်
    await process_download(query.data, query.message, context)

def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN ဖြည့်သွင်းရန် လိုအပ်ပါသည်။")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))

    print("Bot is successfully started...")
    application.run_polling()

if __name__ == '__main__':
    main()
