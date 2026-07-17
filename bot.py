import os
import logging
import threading
import yt_dlp
import math
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
from googleapiclient.discovery import build
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging စနစ် သတ်မှတ်ခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 🛠️ static-ffmpeg လမ်းကြောင်း ချိတ်ဆက်ခြင်း ---
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    logging.info("Static FFmpeg paths added successfully.")
except Exception as e:
    logging.error(f"Static FFmpeg Error: {str(e)}")

# Dummy Server (Render Uptime အတွက်)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Dummy server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Environment Variables မှ Token ယူခြင်း
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def youtube_search(query, is_paritta=False):
    """YouTube API သုံးပြီး တရားတော်စစ်စစ်များကိုသာ ရှာဖွေပေးခြင်း"""
    if not YOUTUBE_API_KEY:
        logging.error("YouTube API Key is missing!")
        return None

    refined_query = f"{query} ပရိတ်တော် တရားတော်" if is_paritta else f"{query} တရားတော် တရားပွဲ ဓမ္မ"

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=refined_query,
            part="snippet",
            maxResults=1,
            type="video",
            videoCategoryId="29"
        )
        response = request.execute()
        
        if response.get("items"):
            return response["items"][0]["id"]["videoId"]
        return None
    except Exception as e:
        logging.error(f"YouTube API Error: {str(e)}")
        return None

# 📌 YouTube Bot Block ကို ကျော်ဖြတ်ရန် ကြားခံ Invidious API သုံး၍ Stream URL ရှာပေးသည့် စနစ်
def get_invidious_stream_url(video_id):
    # အလုပ်လုပ်တတ်သော အများသုံး Invidious Servers များ စာရင်း
    instances = [
        "https://invidious.nerdvpn.de",
        "https://yewtu.be",
        "https://inv.tux.digital",
        "https://invidious.flokinet.to"
    ]
    
    for instance in instances:
        try:
            url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(url, timeout=10).json()
            
            # အသံဖိုင် သီးသန့်ထုတ်ပေးထားသော URL ကို ရှာဖွေခြင်း
            if "adaptiveFormats" in res:
                for fmt in res["adaptiveFormats"]:
                    if "audio/" in fmt.get("type", ""):
                        return fmt["url"], res.get("title", "Dhamma Talk"), res.get("lengthSeconds", 0)
            
            # အကယ်၍ adaptive မတွေ့ပါက ရိုးရိုး format ထဲမှ ရှာခြင်း
            if "formatStreams" in res and res["formatStreams"]:
                return res["formatStreams"][0]["url"], res.get("title", "Dhamma Talk"), res.get("lengthSeconds", 0)
        except Exception as e:
            logging.warning(f"Failed to fetch from {instance}: {str(e)}")
            continue
            
    return None, None, None

# 📌 တရားရှာဖွေပြီး မိနစ် ၃၀ စီ အပိုင်းခွဲ၍ ဒေါင်းလုဒ်ဆွဲကာ ပို့ပေးသည့် အဓိက လုပ်ဆောင်ချက်
async def process_download(query, message_object, context, is_paritta=False):
    status_message = await message_object.reply_text(f"'{query}' တရားတော်ကို ရှာဖွေနေပါတယ်... ခဏစောင့်ပေးပါ 🙏")

    video_id = youtube_search(query, is_paritta)
    
    if not video_id:
        await status_message.edit_text("တောင်းပန်ပါတယ်ခင်ဗျာ၊ အဆိုပါတရားတော်ကို ရှာမတွေ့ပါ (သို့မဟုတ်) YouTube API Error ရှိနေပါသည်။")
        return

    # Invidious Proxy သုံးပြီး Bot Block မထိဘဲ အချက်အလက်နှင့် Stream URL ဆွဲထုတ်ခြင်း
    stream_url, title, duration = get_invidious_stream_url(video_id)
    
    if not stream_url:
        await status_message.edit_text("⚠️ YouTube ဆာဗာများ အလုပ်မလုပ်ပါသဖြင့် ခဏကြာမှ ပြန်လည်ကြိုးစားပေးပါရန် 🙏")
        return

    try:
        # မိနစ် ၃၀ (စက္ကန့် ၁၈၀၀) စီ အပိုင်းခွဲရန် တွက်ချက်ခြင်း
        segment_duration = 1800 
        total_parts = math.ceil(duration / segment_duration)
        if total_parts == 0: total_parts = 1

        await status_message.edit_text(f"🔄 တရားတော်ကြာချိန်မှာ สုစုပေါင်း {math.ceil(duration/60)} မိနစ် ဖြစ်သဖြင့် အပိုင်း ({total_parts}) ပိုင်းခွဲ၍ ပို့ပေးနေပါပြီ... 🙏")

        for part in range(total_parts):
            start_time = part * segment_duration
            filename = f"dhamma_part_{part}_{video_id}"
            
            # `yt-dlp` ကို YouTube ဆီ မလွှတ်တော့ဘဲ ကြားခံ Stream URL ကို တိုက်ရိုက်ခေါ်ခိုင်းခြင်း
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.%(ext)s',
                'external_downloader': 'ffmpeg',
                'external_downloader_args': {
                    'ffmpeg_args': ['-ss', str(start_time), '-t', str(segment_duration)]
                },
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                ydl_down.download([stream_url])

            audio_file_path = f"{filename}.mp3"
            
            if os.path.exists(audio_file_path):
                caption_text = f"🙏 တရားတော် - {title}\n📌 အပိုင်း - ({part + 1}/{total_parts})"
                with open(audio_file_path, 'rb') as audio:
                    await message_object.reply_audio(
                        audio=audio, 
                        title=f"{query} - အပိုင်း ({part + 1})", 
                        performer="Daily Buddha Bot",
                        caption=caption_text
                    )
                os.remove(audio_file_path)
            else:
                await message_object.reply_text(f"⚠️ အပိုင်း ({part + 1}) ကို ဖန်တီး၍ မရနိုင်ဖြစ်သွားပါသည်။")

        await status_message.delete()
        
    except Exception as e:
        logging.error(f"Download/Split Error: {str(e)}")
        await status_message.edit_text("တရားတော်ကို ရယူပြီး အပိုင်းခွဲရာတွင် အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။")

# --- Commands & Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "သင် နာယူလိုသော တရားတော်အမည် သို့မဟုတ် ဆရာတော်ဘွဲ့အမည်ကို ရိုက်ထည့်ပြီး ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။"
    )
    await update.message.reply_text(start_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    if "ပရိတ်" in user_text:
        keyboard = [
            [InlineKeyboardButton("✨ မင်္ဂလသုတ်", callback_data="မင်္ဂလသုတ်"), InlineKeyboardButton("✨ မေတ္တာသုတ်", callback_data="မေတ္တာသုတ်")],
            [InlineKeyboardButton("✨ ရတနသုတ်", callback_data="ရတနသုတ်"), InlineKeyboardButton("✨ ခန္ဓသုတ်", callback_data="ခန္ဓသုတ်")],
            [InlineKeyboardButton("✨ မောရသုတ်", callback_data="မောရသုတ်"), InlineKeyboardButton("✨ ဝဋ္ဋသုတ်", callback_data="ဝဋ္ဋသုတ်")],
            [InlineKeyboardButton("✨ ဓဇဂ္ဂသုတ်", callback_data="ဓဇဂ္ဂသုတ်"), InlineKeyboardButton("✨ အာဋာနာဋိယသုတ်", callback_data="အာဋာနာဋိယသုတ်")],
            [InlineKeyboardButton("✨ အင်္ဂုလိမာလသုတ်", callback_data="အင်္ဂုလိမာလသုတ်"), InlineKeyboardButton("✨ ပုဗ္ဗဏှသုတ်", callback_data="ပုဗ္ဗဏှသုတ်")],
            [InlineKeyboardButton("✨ ဓရဏသုတ်", callback_data="ဓရဏသုတ်")]
        ]
        await update.message.reply_text("🪷 **ပရိတ်ကြီး ၁၁ သုတ်တော်များ** 🪷\n\nနာယူလိုသော သုတ်တော်ကို ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await process_download(user_text, update.message, context, is_paritta=False)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await process_download(query.data, query.message, context, is_paritta=True)

def main():
    if not BOT_TOKEN:
        logging.error("Error: TELEGRAM_BOT_TOKEN ဖြည့်သွင်းရန် လိုအပ်ပါသည်။")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))

    logging.info("Bot is successfully started with Invidious Proxy & Audio Splitting system...")
    application.run_polling()

if __name__ == '__main__':
    main()
