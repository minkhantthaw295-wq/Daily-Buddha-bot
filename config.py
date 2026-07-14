import os

# Render Environment Variables ထဲမှ Key နာမည်များအတိုင်း တိတိကျကျ လှမ်းဖတ်ခြင်း
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Telegram Channel ID နှင့် အချိန်ဇယားအတွက် Timezone သတ်မှတ်ချက်
CHANNEL_ID = os.getenv("CHANNEL_ID", "@DailyBuddhaDhammaMM")
TIMEZONE = "Asia/Yangon"
