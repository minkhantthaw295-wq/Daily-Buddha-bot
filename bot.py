import os
import logging
import threading
import urllib.request
import re
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

# 🛠️ [အစ်ကို့အတွက် ကြော်ငြာ အဖွင့်/အပိတ် Command]
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

async def search_buddha_dhamma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ရိုက်လိုက်တဲ့ စာသားကို YouTube ပေါ်မှာ ခေါင်းစဉ်အတိုင်း Auto ရှာပြီး ကစားသမားလင့်ခ် တန်းပေးမည့်စနစ်"""
    query = update.message.text
    
    if query.startswith('/'):
        return

    status_msg = await update.message.reply_text(f"🔍 '{query}' တရားတော်အား အင်တာနက်ပေါ်တွင် အလိုအလျောက် ရှာဖွေနေပါသည်... 🙏")
    
    try:
        # YouTube မှာ တရားတော် စာသားကို နောက်က Auto တွဲပြီး အသံကြည်လင်တာကို အလိုအလျောက် ရှာဖွေခြင်း
        search_keyword = urllib.parse.quote(f"{query} တရားတော်")
        html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={search_keyword}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        
        if video_ids:
            # အကောင်းဆုံး ပထမဆုံးရလဒ်ကို ယူသည်
            video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            
            # Telegram စာသား တည်ဆောက်ခြင်း
            caption_text = f"🙏 **{query} တရားတော် နာယူရန်** 🙏\n\n🎧 တရားတော်အား အောက်ပါလင့်ခ်တွင် ချက်ချင်း တိုက်ရိုက်နာယူပူဇော်နိုင်ပါပြီခင်ဗျာ -\n{video_url}"
            
            # အစ်ကို လိုအပ်လို့ ထည့်ထားတဲ့ ကြော်ငြာစာသားရှိမှသာ အောက်ခြေတွင် ကပ်ပေးမည်
            if CURRENT_AD_TEXT:
                caption_text += f"\n\n---\n{CURRENT_AD_TEXT}"
                
            await update.message.reply_text(caption_text, parse_mode="Markdown" if CURRENT_AD_TEXT else None, disable_web_page_preview=False)
            await status_msg.delete()
        else:
            await status_msg.edit_text("⚠️ တောင်းပန်ပါတယ်ဗျာ။ အဲဒီတရားတော်ကို YouTube ပေါ်တွင် ရှာမတွေ့ပါဗျာ။")
            
    except Exception as e:
        logging.error(f"Search Error: {str(e)}")
        await status_msg.edit_text("⚠️ လိုင်းကြပ်နေသဖြင့် ခဏနေမှ ပြန်စမ်းပေးပါဗျာ။")

def main():
    if not BOT_TOKEN: return
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setad", set_ad_command)) 
    
    # User ရိုက်သမျှစာကို Auto ရှာပေးမည့်စနစ်
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_buddha_dhamma))

    logging.info("Lightweight Auto-Search Bot successfully started...")
    application.run_polling()

if __name__ == '__main__':
    main()
