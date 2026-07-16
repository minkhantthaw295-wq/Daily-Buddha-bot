import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_dummy_server():
    # Render က ပေးမယ့် PORT ကို ယူ၊ မရှိရင် 10000 ကို သုံး
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Dummy server running on port {port}")
    server.serve_forever()

# Thread တစ်ခုခွဲပြီး Server ကို နောက်ကွယ်ကနေ Run ထားခိုင်းမယ်
threading.Thread(target=run_dummy_server, daemon=True).start()
import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging သတ်မှတ်ခြင်း (ဆာဗာ Error စစ်ဆေးရန်)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment Variables မှ Telegram Token ယူခြင်း
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# 📌 /start နှိပ်လျှင် "ရှင်" ကို လုံးဝဖျက်ပြီး ယောက်ျားလေးသီးသန့်ပုံစံ တိုတိုရှင်းရှင်း ပြသခြင်း
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "မင်္ဂလာပါဗျာ 🙏\n\n"
        "Daily Buddha Dhamma Bot မှ ကြိုဆိုပါတယ်ဗျာ။\n"
        "သင် နာယူလိုသော တရားတော်အမည် သို့မဟုတ် ဆရာတော်ဘွဲ့အမည်ကို ရိုက်ထည့်ပြီး ရှာဖွေနိုင်ပါတယ်ခင်ဗျာ။"
    )
    await update.message.reply_text(start_text)

# 📌 တရားရှာဖွေပြီး အသံဖိုင် (Audio) ပြောင်းလဲပေးသည့် လုပ်ဆောင်ချက်
async def search_and_send_dhamma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_message = await update.message.reply_text("တရားတော်ကို အသံဖိုင်ပြောင်းလဲနေပါတယ်... ခဏစောင့်ပေးပါ 🙏")

    # YouTube Search Option (အကောင်းဆုံး ဗီဒီယို ၁ ပုဒ်တည်း ရှာမည်)
    ydl_opts_search = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'quiet': True,
    }

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

            # 🛑 ဆာဗာ RAM မပြည့်စေရန် မိနစ် ၃၀ (စက္ကန့် ၁၈၀၀) ထက် ကျော်လွန်ပါက ပယ်ချခြင်း
            if duration > 1800:
                await status_message.edit_text("⚠️ ဤတရားတော်သည် မိနစ် ၃၀ ထက် ကျော်လွန်နေသဖြင့် အသံဖိုင်ပြောင်းလဲ၍ မရနိုင်ပါ။ မိနစ် ၃၀ အောက် တရားတော်များကိုသာ ရှာပေးပါရန်။")
                return

            # YouTube Title ထဲမှ ဆရာတော်ဘွဲ့နှင့် တရားခေါင်းစဉ်ကို ပိုင်းခြားရန် ကြိုးစားခြင်း
            performer = "ဆရာတော်"
            track_title = title
            
            if " - " in title:
                parts = title.split(" - ", 1)
                performer = parts[0].strip()
                track_title = parts[1].strip()
            elif "၏" in title:
                parts = title.split("၏", 1)
                performer = parts[0].strip()
                track_title = parts[1].strip()

            # 🔊 အသံအရည်အသွေး လုံးဝကြည်လင်ပြတ်သားစေရန် (အမြင့်ဆုံး 320kbps ထားခြင်း)
            filename = f"dhamma_{video_data['id']}"
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True,
            }

            # အသံဖိုင်ဒေါင်းလုဒ်ဆွဲခြင်း
            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                ydl_down.download([video_url])

            audio_file_path = f"{filename}.mp3"
            
            if os.path.exists(audio_file_path):
                # "ခဏစောင့်ပါ" ဆိုသည့် စာတိုကို ဖျက်လိုက်မည်
                await status_message.delete()

                # User အလုပ်မရှုပ်စေရန် ဗီဒီယိုလင့်ခ်များမပါဘဲ စာသားတိုတို ၂ ကြောင်းသာ ပြမည်
                caption_text = f"🙏 ဆရာတော် - {performer}\n📌 တရားတော် - {track_title}"

                # သီချင်းဖွင့်သလို တိုက်ရိုက်နားထောင်နိုင်ရန် Telegram Audio ဖြင့် ပို့ခြင်း
                with open(audio_file_path, 'rb') as audio:
                    await update.message.reply_audio(
                        audio=audio,
                        title=track_title,
                        performer=performer,
                        caption=caption_text
                    )
                
                # နေရာလွတ်ရအောင် စက်ထဲက ဒေါင်းထားသောဖိုင်ကို ပြန်ဖျက်ခြင်း
                os.remove(audio_file_path)
            else:
                await status_message.edit_text("အသံဖိုင်ပြောင်းလဲခြင်း မအောင်မြင်ပါ။ နောက်တစ်ကြိမ် ပြန်စမ်းကြည့်ပါ။")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await status_message.edit_text("တရားတော်ကို ဒေါင်းလုဒ်ဆွဲရာတွင် အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။")

def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN ဖြည့်သွင်းရန် လိုအပ်ပါသည်။")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_send_dhamma))

    application.run_polling()

if __name__ == '__main__':
    main()
