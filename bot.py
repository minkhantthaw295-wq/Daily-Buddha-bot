import os
import logging
import threading
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# static-ffmpeg ကို စနစ်ထဲ ချိတ်ဆက်ခြင်း
from static_ffmpeg import run

# FFmpeg လမ်းကြောင်းကို စနစ်ထဲသို့ Auto ထည့်သွင်းခြင်း
ffmpeg_bin, ffprobe_bin = run.get_or_fetch_platform_executables_else_raise()
os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_bin)

# Logging စနစ်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dummy Server (Render Uptime အတွက်)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Dummy server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CURRENT_AD_TEXT = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "နာယူလိုသော **တရားတော်အမည်** သို့မဟုတ် **ပရိတ်တော်အမည်** ကို စာရိုက်၍ ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။"
    )
    final_text = f"{start_text}\n\n{CURRENT_AD_TEXT}" if CURRENT_AD_TEXT else start_text
    await update.message.reply_text(final_text, parse_mode="Markdown" if CURRENT_AD_TEXT else None, disable_web_page_preview=True)

async def set_ad_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_AD_TEXT
    ad_input = " ".join(context.args)
    if not ad_input:
        CURRENT_AD_TEXT = ""
        await update.message.reply_text("✨ ကြော်ငြာစနစ်ကို ပိတ်လိုက်ပါပြီ။ ယခုအချိန်မှစ၍ တရားဖိုင်များ သန့်သန့်လေးပဲ ကျလာပါမည်ဗျာ။")
        return
    CURRENT_AD_TEXT = ad_input
    await update.message.reply_text(f"✅ ကြော်ငြာအသစ်ကို သိမ်းဆည်းလိုက်ပါပြီဗျာ -\n\n{CURRENT_AD_TEXT}")

async def search_and_download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query.startswith('/'):
        return

    status_msg = await update.message.reply_text(f"🔍 '{query}' ကို အင်တာနက်ပေါ်တွင် အလိုအလျောက် ရှာဖွေနေပါသည်... 🙏")
    
    # နေရာလွတ်မပါသော ဖိုင်အမည် သတ်မှတ်ခြင်း
    output_filename = f"dhamma_{update.message.chat_id}"
    output_path = f"{output_filename}.mp3"
    
    try:
        # yt-dlp ဖြင့် အသံဖိုင်ကို Auto ရှာပြီး အရည်အသွေးမြင့် MP3 ဒေါင်းလုဒ်ဆွဲခြင်း
        cmd = [
            "yt-dlp",
            f"ytsearch1:{query} တရားတော်",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", f"{output_filename}.%(ext)s",
            "--no-playlist",
            "--ffmpeg-location", ffmpeg_bin  # static-ffmpeg ရဲ့ လမ်းကြောင်းကို လမ်းညွှန်ခြင်း
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        if os.path.exists(output_path):
            await status_msg.edit_text("🔄 အသံဖိုင် ရရှိပါပြီ။ Bot မှ ပို့ပေးနေပါသည်... 📦")
            
            caption_text = f"🙏 {query} နာယူပူဇော်ရန်။"
            if CURRENT_AD_TEXT:
                caption_text += f"\n\n{CURRENT_AD_TEXT}"
                
            with open(output_path, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption=caption_text,
                    title=query,
                    performer="Daily Buddha Bot",
                    parse_mode="Markdown" if CURRENT_AD_TEXT else None
                )
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("⚠️ တောင်းပန်ပါတယ်ဗျာ။ အဲဒီတရားတော်ကို ရှာမတွေ့ပါ သို့မဟုတ် ဖိုင်ပြောင်းလဲ၍ မရပါဗျာ။")
            
    except Exception as e:
        logging.error(f"Auto Search Error: {str(e)}")
        await status_msg.edit_text("⚠️ စနစ်အတွင်း အမှားအယွင်း ဖြစ်ပေါ်သွားပါသဖြင့် ခဏနေမှ ပြန်စမ်းပေးပါဗျာ။")
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    if not BOT_TOKEN: return
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setad", set_ad_command)) 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_download_audio))

    logging.info("YouTube Audio Search Bot with Static-FFmpeg started...")
    application.run_polling()

if __name__ == '__main__':
    main()
