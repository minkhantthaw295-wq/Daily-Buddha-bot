import os
import logging
import threading
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

# 📢 ကြော်ငြာစာသား (အစပိုင်းတွင် အလွတ်ဖြစ်ပြီး၊ အစ်ကို /setad ပို့မှသာ အလုပ်လုပ်မည်)
CURRENT_AD_TEXT = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start ပြသမည့်စာ"""
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "နာယူလိုသော **တရားတော်အမည်** သို့မဟုတ် **ပရိတ်တော်အမည်** ကို စာရိုက်၍ ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။"
    )
    final_text = f"{start_text}\n\n{CURRENT_AD_TEXT}" if CURRENT_AD_TEXT else start_text
    await update.message.reply_text(final_text, parse_mode="Markdown" if CURRENT_AD_TEXT else None, disable_web_page_preview=True)

# 🛠️ [အစ်ကို့အတွက် သီးသန့် ကြော်ငြာ စီမံခန့်ခွဲမှု Command]
async def set_ad_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """အစ်ကိုက `/setad [စာသား]` ဟု ပို့လိုက်မှသာ ကြော်ငြာဝင်မည့်စနစ်"""
    global CURRENT_AD_TEXT
    ad_input = " ".join(context.args)
    
    if not ad_input:
        CURRENT_AD_TEXT = ""
        await update.message.reply_text("✨ ကြော်ငြာစနစ်ကို ပိတ်လိုက်ပါပြီ။ ယခုအချိန်မှစ၍ တရားဖိုင်များ သန့်သန့်လေးပဲ ကျလာပါမည်ဗျာ။")
        return
        
    CURRENT_AD_TEXT = ad_input
    await update.message.reply_text(f"✅ ကြော်ငြာအသစ်ကို သိမ်းဆည်းလိုက်ပါပြီဗျာ -\n\n{CURRENT_AD_TEXT}")

async def search_and_download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ရိုက်လိုက်တဲ့ စာသားကို YouTube ပေါ်မှာ Auto ရှာပြီး MP3 တန်းပို့ပေးမည့်စနစ်"""
    query = update.message.text
    
    # Bot ရိုက်ထားတဲ့ Command တွေကို ကျော်ရန်
    if query.startswith('/'):
        return

    status_msg = await update.message.reply_text(f"🔍 '{query}' ကို အင်တာနက်ပေါ်တွင် အလိုအလျောက် ရှာဖွေနေပါသည်... 🙏")
    
    # ဖိုင်သိမ်းမည့် နာမည် သတ်မှတ်ခြင်း
    output_filename = f"dhamma_{update.message.chat_id}"
    output_path = f"{output_filename}.mp3"
    
    try:
        # yt-dlp ကို သုံးပြီး YouTube ပေါ်ကနေ အကောင်းဆုံး အသံဖိုင်ကို Auto ရှာပြီး ဒေါင်းလုဒ်ဆွဲခြင်း
        cmd = [
            "yt-dlp",
            f"ytsearch1:{query} တရားတော်", # တရားတော် စာသားကို နောက်က Auto တွဲရှာပေးခြင်း
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0", # အကောင်းဆုံး အသံကြည်လင်မှု ရရှိရန်
            "-o", f"{output_filename}.%(ext)s",
            "--no-playlist"
        ]
        
        # ဒေါင်းလုဒ်လုပ်ခြင်းကို စတင်သည်
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if os.path.exists(output_path):
            await status_msg.edit_text("🔄 အသံဖိုင် ပြောင်းလဲခြင်း ပြီးမြောက်ပါပြီ။ Bot မှ ပို့ပေးနေပါသည်... 📦")
            
            caption_text = f"🙏 {query} နာယူပူဇော်ရန်။"
            if CURRENT_AD_TEXT:
                caption_text += f"\n\n{CURRENT_AD_TEXT}"
                
            # တရားအသံဖိုင်ကို တန်းပို့ပေးခြင်း
            with open(output_path, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption=caption_text,
                    title=query,
                    performer="Daily Buddha Bot",
                    parse_mode="Markdown" if CURRENT_AD_TEXT else None
                )
            
            # ပို့ပြီးရင် ဖုန်းမပြည့်အောင် ဖိုင်ကို ချက်ချင်း ပြန်ဖျက်သည်
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("⚠️ တောင်းပန်ပါတယ်ဗျာ။ အဲဒီတရားတော်ကို ရှာမတွေ့ပါ သို့မဟုတ် အသံဖိုင် ပြောင်းလဲ၍ မရပါဗျာ။")
            
    except Exception as e:
        logging.error(f"Auto Search Error: {str(e)}")
        await status_msg.edit_text("⚠️ စနစ်အတွင်း အမှားအယွင်း ဖြစ်ပေါ်သွားပါသဖြင့် ခဏနေမှ ပြန်စမ်းပေးပါဗျာ။")
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    if not BOT_TOKEN: return
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setad", set_ad_command)) # ကြော်ငြာ ထိန်းချုပ်ရန်
    
    # User ရိုက်သမျှ စာသားကို Auto ရှာပေးမည့် Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_download_audio))

    logging.info("YouTube Audio Search Bot successfully started...")
    application.run_polling()

if __name__ == '__main__':
    main()
