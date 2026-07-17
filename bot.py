import os
import logging
import threading
import yt_dlp
import math
from http.server import SimpleHTTPRequestHandler, HTTPServer
from googleapiclient.discovery import build
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging စနစ် သတ်မှတ်ခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 🛠️ ဤနေရာတွင် static-ffmpeg လမ်းကြောင်းကို ချိတ်ဆက်ပေးခြင်း (Render Build Error ကာကွယ်ရန်) ---
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    logging.info("Static FFmpeg paths added successfully.")
except Exception as e:
    logging.error(f"Static FFmpeg Error: {str(e)}")
# ----------------------------------------------------------------------------------

# Dummy Server (Render ရဲ့ Free Plan Uptime ၂၄ နာရီလုံး အိပ်မသွားဘဲ အလုပ်လုပ်စေရန်)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Dummy server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Environment Variables (ပတ်ဝန်းကျင် ပြောင်းလဲနိုင်သော ကိန်းရှင်များ) မှ Token ယူခြင်း
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def youtube_search(query, is_paritta=False):
    """YouTube API သုံးပြီး Music သီချင်းသံများ မပါဘဲ တရားတော်စစ်စစ်များကိုသာ စစ်ထုတ်ရှာဖွေပေးခြင်း"""
    if not YOUTUBE_API_KEY:
        logging.error("YouTube API Key is missing in Environment Variables!")
        return None

    if is_paritta:
        refined_query = f"{query} ပရိတ်တော် တရားတော်"
    else:
        refined_query = f"{query} တရားတော် တရားပွဲ ဓမ္မ"

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=refined_query,
            part="snippet",
            maxResults=1,
            type="video",
            videoCategoryId="29"  # Nonprofits & Activism / Religious content စစ်ထုတ်ရန်
        )
        response = request.execute()
        
        if response.get("items"):
            video_id = response["items"][0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        logging.error(f"YouTube API Error: {str(e)}")
        return None

# 📌 တရားရှာဖွေပြီး မိနစ် ၃၀ စီ အပိုင်းခွဲ၍ ဒေါင်းလုဒ်ဆွဲကာ တစ်ခါတည်း ပို့ပေးသည့် အဓိက လုပ်ဆောင်ချက်
async def process_download(query, message_object, context, is_paritta=False):
    status_message = await message_object.reply_text(f"'{query}' တရားတော်ကို ရှာဖွေနေပါတယ်... ခဏစောင့်ပေးပါ 🙏")

    video_url = youtube_search(query, is_paritta)
    
    if not video_url:
        await status_message.edit_text("တောင်းပန်ပါတယ်ခင်ဗျာ၊ အဆိုပါတရားတော်ကို ရှာမတွေ့ပါ (သို့မဟုတ်) YouTube API Error ရှိနေပါသည်။")
        return

    try:
        # YouTube ရဲ့ Bot Block ("Sign in to confirm you're not a bot") ကို ကျော်ရန် Extractor Args များ ထည့်သွင်းခြင်း
        ydl_opts_info = {
            'format': 'bestaudio/best', 
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'skip': ['webpage']}}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', query)
            duration = info.get('duration', 0)

        # မိနစ် ၃၀ (စက္ကန့် ၁၈၀၀) စီ အပိုင်းခွဲရန် တွက်ချက်ခြင်း
        segment_duration = 1800 
        total_parts = math.ceil(duration / segment_duration)

        if total_parts == 0:
            total_parts = 1

        await status_message.edit_text(f"🔄 တရားတော်ကြာချိန်မှာ စုစုပေါင်း {math.ceil(duration/60)} မိနစ် ဖြစ်သဖြင့် အပိုင်း ({total_parts}) ပိုင်းခွဲ၍ ပို့ပေးနေပါပြီ... 🙏")

        # တစ်ပိုင်းချင်းစီကို ဆာဗာမပြည့်အောင် သီးသန့်စီ ဖြတ်တောက်ပြီး ဒေါင်းလုဒ်ဆွဲကာ ပို့ခြင်း
        for part in range(total_parts):
            start_time = part * segment_duration
            filename = f"dhamma_part_{part}_{info['id']}"
            
            # ဒေါင်းလုဒ်ဆွဲသည့် နေရာတွင်လည်း Bot Block ကျော်ရန်နှင့် static-ffmpeg သုံးရန် ပေါင်းစပ်ပြင်ဆင်ခြင်း
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.%(ext)s',
                'external_downloader': 'ffmpeg',
                'external_downloader_args': {
                    'ffmpeg_args': ['-ss', str(start_time), '-t', str(segment_duration)]
                },
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'quiet': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'skip': ['webpage']}}
            }

            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                ydl_down.download([video_url])

            audio_file_path = f"{filename}.mp3"
            
            # ဖိုင်တည်ရှိမှုရှိမရှိ သေချာစစ်ဆေးပြီး Telegram သို့ ပို့ပေးခြင်း
            if os.path.exists(audio_file_path):
                caption_text = f"🙏 တရားတော် - {title}\n📌 အပိုင်း - ({part + 1}/{total_parts})"
                with open(audio_file_path, 'rb') as audio:
                    await message_object.reply_audio(
                        audio=audio, 
                        title=f"{query} - အပိုင်း ({part + 1})", 
                        performer="Daily Buddha Bot",
                        caption=caption_text
                    )
                # ဆာဗာနေရာလွတ်စေရန် ဒေါင်းလုဒ်ပြီးဖိုင်ကို ချက်ချင်းပြန်ဖျက်ခြင်း
                os.remove(audio_file_path)
            else:
                await message_object.reply_text(f"⚠️ အပိုင်း ({part + 1}) ကို ဖန်တီး၍ မရနိုင်ဖြစ်သွားပါသည်။")

        # ပို့ဆောင်မှုအားလုံး ပြီးဆုံးပါက အခြေအနေပြစာတိုကို ဖျက်ပေးခြင်း
        await status_message.delete()
        
    except Exception as e:
        logging.error(f"Download/Split Error: {str(e)}")
        await status_message.edit_text("တရားတော်ကို ရယူပြီး အပိုင်းခွဲရာတွင် အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။")

# --- Commands & Handlers (အမိန့်နှင့် မက်ဆေ့ခ်ျ ကိုင်တွယ်မှုအပိုင်း) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "သင် နာယူလိုသော တရားတော်အမည် သို့မဟုတ် ဆရာတော်ဘွဲ့အမည်ကို ရိုက်ထည့်ပြီး ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။"
    )
    await update.message.reply_text(start_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    # အကယ်၍ အသုံးပြုသူက "ပရိတ်" ဟူသော စာလုံးထည့်ပါက သုတ်တော်များ Menu ပေါ်လာစေရန်
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
        # ရိုးရိုးတရားစာသားဆိုလျှင် တိုက်ရိုက်ရှာဖွေဒေါင်းလုဒ်လုပ်ခြင်း
        await process_download(user_text, update.message, context, is_paritta=False)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ခလုတ်နှိပ်သည့် ပရိတ်သုတ်တော်များကို ဒေါင်းလုဒ်လုပ်ခြင်း
    await process_download(query.data, query.message, context, is_paritta=True)

def main():
    if not BOT_TOKEN:
        logging.error("Error: TELEGRAM_BOT_TOKEN ဖြည့်သွင်းရန် လိုအပ်ပါသည်။")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))

    logging.info("Bot is successfully started with Audio Splitting & Anti-Block system...")
    application.run_polling()

if __name__ == '__main__':
    main()
