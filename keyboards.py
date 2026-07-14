from telegram import ReplyKeyboardMarkup

def get_main_menu():
    keyboard = [
        ["📖 တရားတော်ရှာရန်"],
        ["👤 ဆရာတော်များ", "🎥 Video တရား"],
        ["🎧 Audio တရား", "📅 နေ့စဉ်တရားတော်"],
        ["❤️ အကြိုက်ဆုံး", "ℹ️ အကူအညီ"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="တရားတော်အမည် သို့မဟုတ် ဆရာတော်အမည်ကို ရိုက်ထည့်ပါ..."
    )
