import asyncio
import sys
import logging
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Render/Render Web Port အတွက် aiohttp ထည့်သွင်းခြင်း
from aiohttp import web

from config import BOT_TOKEN, YOUTUBE_API_KEY, CHANNEL_ID, TIMEZONE
from keyboards import get_main_menu

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def search_youtube_dhamma(query):
    if not YOUTUBE_API_KEY:
        return "⚠️ စနစ်ချို့ယွင်းနေပါသည်။ YouTube API Key မရှိသေးသဖြင့် ရှာမရနိုင်ပါ။"
    
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        search_query = f"{query} တရားတော်"
        
        request = youtube.search().list(
            q=search_query,
            part='snippet',
            maxResults=3,
            type='video'
        )
        response = request.execute()
        
        results = []
        for item in response.get('items', []):
            title = item['snippet']['title']
            video_id = item['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            results.append(f"🎥 **{title}**\n🔗 {video_url}\n")
            
        if not results:
            return "🔍 စိတ်မရှိပါနဲ့ခင်ဗျာ၊ ရှာဖွေမှုရလဒ် မတွေ့ရှိပါ။"
            
        return "\n".join(results)
    except Exception as e:
        logging.error(f"YouTube Search Error: {e}")
        return "⚠️ တရားတော်ရှာဖွေရာတွင် အဆင်မပြေဖြစ်နေပါသည်။ ခဏနေမှ ပြန်လည်စမ်းသပ်ပေးပါ။"

# Scheduler Error မတက်စေရန် Parameter တွင် *args ထည့်သွင်းထားသည်
async def post_dhamma_to_channel(app: Application, *args):
    if not YOUTUBE_API_KEY:
        return
        
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q="တရားတော်များ နေ့စဉ်နာယူရန်",
            part='snippet',
            maxResults=15,
            type='video'
        )
        response = request.execute()
        
        items = response.get('items', [])
        if items:
            selected_video = random.choice(items)
            title = selected_video['snippet']['title']
            video_id = selected_video['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            message = f"🙏 **နေ့စဉ် ဓမ္မဒါန တရားတော်** 🙏\n\nတရားတော်အမည် - {title}\n\nနာယူကြည်ညိုရန် အောက်ပါလင့်ခ်ကို နှိပ်ပါ -\n🔗 {video_url}"
            
            await app.bot.send_message(chat_id=CHANNEL_ID, text=message)
            logging.info("Successfully posted to channel.")
    except Exception as e:
        logging.error(f"Auto Post Failure: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 မင်္ဂလာပါရှင်\n\nDaily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်။\nသင် နာယူလိုသော တရားတော်အမည် သို့မဟုတ် ဆရာတော်အမည်ကို ရိုက်ထည့်ပြီး ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။",
        reply_markup=get_main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if user_text in ["📖 တရားတော်ရှာရန်", "👤 ဆရာတော်များ", "🎥 Video တရား", "🎧 Audio တရား", "📅 နေ့စဉ်တရားတော်", "❤️ အကြိုက်ဆုံး", "ℹ️ အကူအညီ"]:
        await update.message.reply_text(
            f"✨ '{user_text}' အတွက် တရားတော်အမည် သို့မဟုတ် ဆရာတော်အမည်ကို ရိုက်ထည့်ပေးပါခင်ဗျာ။ Bot မှ အလိုအလျောက် ရှာဖွေပေးပါမည်။"
        )
    else:
        waiting_msg = await update.message.reply_text("🔍 တရားတော်များကို ရှာဖွေပေးနေပါသည်၊ ခဏစောင့်ပေးပါ...")
        search_result = search_youtube_dhamma(user_text)
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_msg.message_id)
        except Exception:
            pass
        await update.message.reply_text(search_result)

# Render Port အတွက် အလုပ်လုပ်မည့် ရိုးရှင်းသော ကူညီပံ့ပိုးမှု Function
async def handle_ping(request):
    return web.Response(text="Bot is alive")

async def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    scheduler.add_job(post_dhamma_to_channel, 'cron', hour=7, minute=0, args=[app])
    scheduler.add_job(post_dhamma_to_channel, 'cron', hour=13, minute=0, args=[app])
    scheduler.add_job(post_dhamma_to_channel, 'cron', hour=19, minute=0, args=[app])
    scheduler.start()

    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    
    print("Buddha Bot is successfully running...")
    
    # Render Web Service Port Binding ပြဿနာကို ဖြေရှင်းရန် Web Server မောင်းနှင်ခြင်း
    web_app = web.Application()
    web_app.router.add_get("/", handle_ping)
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    # Render မှ ပေးမည့် Port သို့မဟုတ် Default 8080 တွင် Listen လုပ်မည်
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    # Bot အမြဲပွင့်နေစေရန် စောင့်ဆိုင်းခြင်း
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
