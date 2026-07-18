import os
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Logging စနစ် သတ်မှတ်ခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dummy Server (Render Uptime အမြဲရစေရန် ပုံသေမောင်းနှင်ခြင်း)
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Dummy server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# 📢 [အစ်ကို့အတွက် Channel ကြော်ငြာထည့်ရန်နေရာ] - ဤနေရာတွင် စိတ်ကြိုက်စာသားနှင့် လင့်ခ် ပြောင်းလဲနိုင်ပါသည်
AD_TEXT = (
    "\n\n--- ✨ ဓမ္မလမ်းပြ Channel ကြော်ငြာ ✨ ---\n"
    "တရားတော်များ နေ့စဉ်နာယူရန် ကျွန်ုပ်တို့ Channel ကို Join ထားပါဦးဗျာ။\n"
    "👉 [ဤနေရာတွင် သင့် Channel Link ကို အစားထိုးရန်](https://t.me/your_channel_username)"
)

# 📌 ၁။ ဆရာတော်ကြီးများ၏ တရားတော်များ (/audio) အတွက် Telegram File ID များ
# (Telegram ထဲတွင် ဖိုင်တင်ပြီး ရလာသော Unique File ID များကို ဤနေရာတွင် အစားထိုးပါ)
DHAMMA_AUDIO_IDS = {
    "သီတဂူ_တရားတော်": "BAACAgIAAxkBAAE...", 
    "ချမ်းမြေ့_တရားတော်": "BAACAgIAAxkBAAE...",
    "တိပိဋက_တရားတော်": "BAACAgIAAxkBAAE..."
}

# 📌 ၂။ ပရိတ်တော်များ (/paritta) အတွက် Telegram File ID များ
PARITTA_AUDIO_IDS = {
    "မင်္ဂလသုတ်": "BAACAgIAAxkBAAE...", 
    "မေတ္တာသုတ်": "BAACAgIAAxkBAAE...",
    "ရတနသုတ်": "BAACAgIAAxkBAAE...",
    "ခန္ဓသုတ်": "BAACAgIAAxkBAAE...",
    "မောရသုတ်": "BAACAgIAAxkBAAE...",
    "ဝဋ္ဋသုတ်": "BAACAgIAAxkBAAE..."
}

# --- Bot Commands Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start ဟု နှိပ်လျှင် ပြသမည့် စာတန်းနှင့် ကြော်ငြာ"""
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "အောက်ခြေရှိ **Menu** ခလုတ်ကို နှိပ်၍ မိမိနာယူလိုသော တရားတော်များကို လွယ်ကူစွာ ရွေးချယ်နိုင်ပါတယ်ခင်ဗျာ။"
    )
    await update.message.reply_text(start_text + AD_TEXT, parse_mode="Markdown", disable_web_page_preview=True)

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/audio ဆရာတော်ကြီးများ၏ တရားတော်များ ခလုတ်စာရင်း"""
    keyboard = [
        [InlineKeyboardButton("🎙️ သီတဂူဆရာတော်ဘုရားကြီး", callback_data="သီတဂူ_တရားတော်")],
        [InlineKeyboardButton("🎙️ ချမ်းမြေ့ဆရာတော်ဘုရားကြီး", callback_data="ချမ်းမြေ့_တရားတော်")],
        [InlineKeyboardButton("🎙️ တိပိဋကဆရာတော်ဘုရားကြီး", callback_data="တိပိဋက_တရားတော်")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🪷 **နာယူလိုသော ဆရာတော်ကြီးများ၏ တရားတော်ကို ရွေးချယ်ပါ** 🪷", reply_markup=reply_markup)

async def paritta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/paritta ပရိတ်တော်များ ခလုတ်စာရင်း"""
    keyboard = [
        [InlineKeyboardButton("✨ မင်္ဂလသုတ်", callback_data="မင်္ဂလသုတ်"), InlineKeyboardButton("✨ မေတ္တာသုတ်", callback_data="မေတ္တာသုတ်")],
        [InlineKeyboardButton("✨ ရတနသုတ်", callback_data="ရတနသုတ်"), InlineKeyboardButton("✨ ခန္ဓသုတ်", callback_data="ခန္ဓသုတ်")],
        [InlineKeyboardButton("✨ မောရသုတ်", callback_data="မောရသုတ်"), InlineKeyboardButton("✨ ဝဋ္ဋသုတ်", callback_data="ဝဋ္ဋသုတ်")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🪷 **နာယူပူဇော်လိုသော ပရိတ်သုတ်တော်ကို ရွေးချယ်ပါ** 🪷", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User များ ခလုတ်နှိပ်သည့်အခါ Error မရှိဘဲ တိုက်ရိုက် ဖိုင်ပို့ပေးခြင်း"""
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    # ရွေးချယ်ထားသော အသံဖိုင် ID ကို လှမ်းယူခြင်း
    audio_id = PARITTA_AUDIO_IDS.get(choice) or DHAMMA_AUDIO_IDS.get(choice)
    
    if audio_id and audio_id != "BAACAgIAAxkBAAE...":
        # အသံဖိုင်ကို တိုက်ရိုက်ပို့ပြီး အောက်ခြေတွင် ကြော်ငြာစာသား အလိုအလျောက် ကပ်ပေးခြင်း
        await query.message.reply_audio(
            audio=audio_id, 
            caption=f"🙏 {choice.replace('_', ' ')} နာယူပူဇော်ရန်။" + AD_TEXT,
            parse_mode="Markdown"
        )
    else:
        # ဖိုင် ID မထည့်ရသေးပါက ပြသမည့် စာသားအဆင်သင့်စနစ်
        await query.message.reply_text(
            f"🪷 **{choice.replace('_', ' ')}** တရားတော်ဖိုင်ကို စနစ်အတွင်း မကြာမီ အချောသတ် ဖြည့်သွင်းပေးပါမည်ခင်ဗျာ 🙏" + AD_TEXT,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

async def handle_user_text_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User များ စာလျှောက်ရိုက်ပြီး ဘောကလိခြင်း၊ စနစ်အား ကြောင်စေခြင်းမှ ကာကွယ်ရန်"""
    await update.message.reply_text(
        "⚠️ တောင်းပန်ပါတယ်ခင်ဗျာ။ စာရိုက်၍ ရှာဖွေခြင်းကို ပိတ်ထားပါသည်။ အောက်ခြေရှိ **Menu** ခလုတ်ကိုနှိပ်၍ တရားတော်များကိုသာ ရွေးချယ်နာယူပေးပါရန် 🙏"
    )

def main():
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN ဖြည့်သွင်းရန် လိုအပ်ပါသည်။")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    # 📌 အစ်ကိုအလိုရှိသည့် အလုပ်လုပ်မည့် Menu သုံးခုသာ သိမ်းဆည်းခြင်း
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("audio", audio_command))
    application.add_handler(CommandHandler("paritta", paritta_command))
    
    # ခလုတ်နှိပ်ခြင်းနှင့် စာရိုက်ခြင်း ထိန်းချုပ်မှုများ
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text_restrict))

    logging.info("Clean Bot with Strict 3-Menu Layout and Ads system successfully deployed...")
    application.run_polling()

if __name__ == '__main__':
    main()
