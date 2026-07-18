import os
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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

# 📢 ကြော်ငြာစာသားကို မန်မိုရီထဲတွင် ယာယီသိမ်းဆည်းထားမည့်နေရာ (အစပိုင်းတွင် လုံးဝ Empty ဖြစ်နေမည်၊ ဘာလင့်ခ်မှ မပါပါ)
CURRENT_AD_TEXT = ""

# 📌 ၁။ ဆရာတော်ကြီးများ၏ တရားတော်များ (Direct MP3 Link များ သို့မဟုတ် Telegram File ID များ)
DHAMMA_AUDIO_SOURCES = {
    "သီတဂူ_တရားတော်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", 
    "ချမ်းမြေ့_တရားတော်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "တိပိဋက_တရားတော်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
}

# 📌 ၂။ ပရိတ်တော်များအတွက် Direct MP3 Link များ သို့မဟုတ် Telegram File ID များ
PARITTA_AUDIO_SOURCES = {
    "မင်္ဂလသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", 
    "မေတ္တာသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    "ရတနသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    "ခန္ဓသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
    "မောရသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "ဝဋ္ဋသုတ်": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3"
}

# --- Bot Commands Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start Command ပို့လျှင် ပြသမည့်စာ (ပုံမှန်အချိန်တွင် ကြော်ငြာလုံးဝမပါပါ)"""
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "တရားတော်များ နာယူရန်အတွက် အောက်ခြေရှိ **Menu** ခလုတ်မှတစ်ဆင့် စိတ်ကြိုက်ရွေးချယ်နိုင်ပါတယ်ခင်ဗျာ။"
    )
    # အစ်ကို သီးသန့်ထည့်ထားတဲ့ ကြော်ငြာစာသားရှိမှသာ အောက်တွင် ကပ်ပြမည်။
    final_text = f"{start_text}\n\n{CURRENT_AD_TEXT}" if CURRENT_AD_TEXT else start_text
    await update.message.reply_text(final_text, parse_mode="Markdown" if CURRENT_AD_TEXT else None, disable_web_page_preview=True)

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/audio ဆရာတော်ကြီးများ၏ တရားတော်များ ခလုတ်စာရင်း"""
    keyboard = [
        [InlineKeyboardButton("🎙️ သီတဂူဆရာတော်ဘုရားကြီး", callback_data="သီတဂူ_တရားတော်")],
        [InlineKeyboardButton("🎙️ ချမ်းမြေ့ဆရာတော်ဘုရားကြီး", callback_data="ချမ်းမြေ့_တရားတော်")],
        [InlineKeyboardButton("🎙️ တိပိဋကဆရာတော်ဘုရားကြီး", callback_data="တိပိဋက_တရားတော်")]
    ]
    await update.message.reply_text("🪷 **နာယူလိုသော ဆရာတော်ကြီးများ၏ တရားတော်ကို ရွေးချယ်ပါ** 🪷", reply_markup=InlineKeyboardMarkup(keyboard))

async def paritta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/paritta ပရိတ်တော်များ ခလုတ်စာရင်း"""
    keyboard = [
        [InlineKeyboardButton("✨ မင်္ဂလသုတ်", callback_data="မင်္ဂလသုတ်"), InlineKeyboardButton("✨ မေတ္တာသုတ်", callback_data="မေတ္တာသုတ်")],
        [InlineKeyboardButton("✨ ရတနသုတ်", callback_data="ရတနသုတ်"), InlineKeyboardButton("✨ ခန္ဓသုတ်", callback_data="ခန္ဓသုတ်")],
        [InlineKeyboardButton("✨ မောရသုတ်", callback_data="မောရသုတ်"), InlineKeyboardButton("✨ ဝဋ္ဋသုတ်", callback_data="ဝဋ္ဋသုတ်")]
    ]
    await update.message.reply_text("🪷 **နာယူပူဇော်လိုသော ပရိတ်သုတ်တော်ကို ရွေးချယ်ပါ** 🪷", reply_markup=InlineKeyboardMarkup(keyboard))

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
    await update.message.reply_text(f"✅ ကြော်ငြာအသစ်ကို အောင်မြင်စွာ သိမ်းဆည်းလိုက်ပါပြီဗျာ -\n\n{CURRENT_AD_TEXT}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User များ ခလုတ်နှိပ်သည့်အခါ တရားဖိုင် ထုတ်ပေးခြင်း"""
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    audio_source = PARITTA_AUDIO_SOURCES.get(choice) or DHAMMA_AUDIO_SOURCES.get(choice)
    
    if audio_source:
        clean_name = choice.replace('_', ' ')
        status_msg = await query.message.reply_text(f"🔄 {clean_name} ကို စနစ်ထဲမှ ဆွဲထုတ်နေပါသည်... ขဏစောင့်ပေးပါ 🙏")
        
        try:
            caption_text = f"🙏 {clean_name} နာယူပူဇော်ရန်။"
            
            # အစ်ကို လိုအပ်လို့ `/setad` နဲ့ ထည့်ထားတဲ့ ကြော်ငြာစာသားရှိမှသာ အောက်ခြေတွင် တွဲပေးမည်။
            if CURRENT_AD_TEXT:
                caption_text += f"\n\n{CURRENT_AD_TEXT}"
                
            await query.message.reply_audio(
                audio=audio_source, 
                caption=caption_text,
                title=clean_name,
                performer="Daily Buddha Bot",
                parse_mode="Markdown" if CURRENT_AD_TEXT else None
            )
            await status_msg.delete()
        except Exception as e:
            logging.error(f"Audio Send Error: {str(e)}")
            await status_msg.edit_text("⚠️ တရားဖိုင်လင့်ခ် ချို့ယွင်းချက်ကြောင့် မရနိုင်သေးပါဗျာ။")
    else:
        await query.message.reply_text(f"⚠️ {choice.replace('_', ' ')} အား စနစ်ထဲတွင် ရှာမတွေ့သေးပါ။")

async def handle_user_text_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User များ စာလျှောက်ရိုက်ခြင်းကို ကာကွယ်ရန်"""
    await update.message.reply_text(
        "⚠️ တောင်းပန်ပါတယ်ခင်ဗျာ။ စာရိုက်၍ ရှာဖွေခြင်းကို ပိတ်ထားပါသည်။ အောက်ခြေရှိ **Menu** ခလုတ်ကိုနှိပ်၍ တရားတော်များကိုသာ ရွေးချယ်နာယူပေးပါရန် 🙏"
    )

def main():
    if not BOT_TOKEN: return
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 3-Menu Layout Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("audio", audio_command))
    application.add_handler(CommandHandler("paritta", paritta_command))
    
    # အစ်ကို ကြော်ငြာပြောင်းရန် သီးသန့် Command
    application.add_handler(CommandHandler("setad", set_ad_command)) 
    
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text_restrict))

    logging.info("Dynamic Flexible Ad Bot successfully started...")
    application.run_polling()

if __name__ == '__main__':
    main()
