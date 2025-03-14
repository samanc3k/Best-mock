import gspread
from google.oauth2.service_account import Credentials
from telegram import (Update, ReplyKeyboardMarkup, KeyboardButton, 
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          CallbackQueryHandler, filters, ContextTypes)

# Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

table = client.open("Mock Exam Registrations")
cefr_sheet = table.worksheet("CEFR Registrations")
ielts_sheet = table.worksheet("IELTS Registrations")

# Channel settings
CHANNEL_USERNAME = "@BestITM"
ADMINS = [1486347042]
USERS = set()

def is_admin(user_id):
    return user_id in ADMINS

async def is_subscribed(bot, user_id):
    """
    Foydalanuvchi kanalga obuna bo‘lganligini tekshirish.
    """
    try:
        chat_member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start komandasi.
    Foydalanuvchidan kanalga obuna bo‘lishni so‘raydi yoki imtihon tanlash menyusini ko‘rsatadi.
    """
    user_id = update.message.from_user.id
    USERS.add(user_id)
    if not await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("🔔 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Botdan foydalanish uchun kanalga obuna bo‘lishingiz kerak! 👇", 
            reply_markup=reply_markup
        )
        return
    
    # Obuna bo'lgan bo'lsa, imtihon tanlash menyusi
    reply_keyboard = [["CEFR Mock Imtihoni", "IELTS Mock Imtihoni"]]
    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum! Qaysi imtihonga ro‘yxatdan o‘tmoqchisiz?", 
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Obunani tekshirish tugmasi bosilganda ishlaydi.
    """
    query = update.callback_query
    user_id = query.from_user.id
    if await is_subscribed(context.bot, user_id):
        await query.message.delete()
        reply_keyboard = [["CEFR Mock Imtihoni", "IELTS Mock Imtihoni"]]
        await query.message.reply_text(
            "Rahmat! Endi davom etishingiz mumkin. Qaysi imtihonga ro‘yxatdan o‘tmoqchisiz?", 
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
    else:
        await query.answer("Siz hali ham kanalga obuna bo‘lmagansiz! 🔔", show_alert=True)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Foydalanuvchi "CEFR Mock Imtihoni" yoki "IELTS Mock Imtihoni" tanlaganida ishga tushadi.
    """
    text = update.message.text
    if text == "CEFR Mock Imtihoni":
        context.user_data["exam"] = "CEFR"
    elif text == "IELTS Mock Imtihoni":
        context.user_data["exam"] = "IELTS"
    else:
        await update.message.reply_text("Iltimos, berilgan variantlardan birini tanlang.")
        return
    
    # To'liq ism kiritish bosqichiga o'tamiz
    context.user_data["step"] = "full_name"
    await update.message.reply_text("Iltimos, to'liq ismingizni kiriting:")

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Foydalanuvchi to'liq ismini kiritadi. Keyin telefon raqamni so'raymiz.
    """
    full_name = update.message.text
    context.user_data["full_name"] = full_name
    context.user_data["step"] = "phone_number"

    phone_button = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text("Endi telefon raqamingizni yuboring:", reply_markup=phone_button)

async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Foydalanuvchi telefon raqamni yuboradi. Google Sheets ga yozamiz va ro'yxatdan o'tganini tasdiqlaymiz.
    """
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring.")
        return
    
    full_name = context.user_data.get("full_name")
    phone_number = contact.phone_number
    exam = context.user_data.get("exam")

    if exam == "CEFR":
        cefr_sheet.append_row([full_name, phone_number])
    elif exam == "IELTS":
        ielts_sheet.append_row([full_name, phone_number])
    
    await update.message.reply_text(f"Tabriklaymiz! Siz {exam} imtihoniga ro‘yxatdan o‘tdingiz!")
    context.user_data.clear()

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin komandasi. Faqat ADMINS ro'yxatida bo'lganlarga ruxsat beriladi.
    """
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Siz admin emassiz!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 Reklama jo‘natish", callback_data="send_ad")],
        [InlineKeyboardButton("⚙ Majburiy obunani yangilash", callback_data="update_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin panelga xush kelibsiz!", reply_markup=reply_markup)

async def send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Reklama xabarini barcha foydalanuvchilarga yuborish uchun callback.
    """
    query = update.callback_query
    await query.message.reply_text("Reklama xabarini yuboring:")
    context.user_data["step"] = "send_ad"

async def update_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Majburiy obuna kanalini yangilash uchun callback.
    """
    query = update.callback_query
    await query.message.reply_text("Yangi kanal username-ni kiriting (@ bilan):")
    context.user_data["step"] = "update_subscription"

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin kiritgan matnni (reklama yoki yangi kanal username) qayta ishlash.
    """
    text = update.message.text
    if context.user_data.get("step") == "send_ad":
        # Reklama matnini barcha foydalanuvchilarga yuboramiz
        for user_id in USERS:
            try:
                await context.bot.send_message(user_id, text)
            except Exception:
                pass
        await update.message.reply_text("Reklama barcha foydalanuvchilarga jo‘natildi!")
    
    elif context.user_data.get("step") == "update_subscription":
        global CHANNEL_USERNAME
        CHANNEL_USERNAME = text
        await update.message.reply_text(f"Majburiy obuna kanali {CHANNEL_USERNAME} ga o‘zgartirildi!")
    
    context.user_data.clear()

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Barcha matnli xabarlarni qayta ishlash. step ga qarab keyingi funksiyaga yo'naltiradi.
    """
    step = context.user_data.get("step")
    text = update.message.text

    # Agar step hali o'rnatilmagan bo'lsa (ya'ni foydalanuvchi imtihon turini tanlashi kerak bo'lsa),
    # handle_choice funksiyasiga yo'naltiramiz.
    if step is None:
        if text in ["CEFR Mock Imtihoni", "IELTS Mock Imtihoni"]:
            await handle_choice(update, context)
        else:
            await update.message.reply_text("Iltimos, boshlang'ich menyu uchun /start buyrug'idan foydalaning.")
        return
    
    # step == "full_name"
    if step == "full_name":
        await handle_full_name(update, context)
        return
    
    # Admin qismi
    if step == "send_ad" or step == "update_subscription":
        await handle_admin_input(update, context)
        return

    # Aks holda
    await update.message.reply_text("Iltimos, boshlang'ich menyu uchun /start buyrug'idan foydalaning.")

def main():
    # Bot tokeningizni shu yerga yozing
    bot_token = "8192600685:AAG2Kxr8mTS81XRuWhNCwKRtn80yea4JhKQ"
    app = ApplicationBuilder().token(bot_token).build()
    
    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    app.add_handler(CallbackQueryHandler(send_ad, pattern="send_ad"))
    app.add_handler(CallbackQueryHandler(update_subscription, pattern="update_subscription"))

    # Matnli xabarlar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    # Telefon raqam (contact) uchun
    app.add_handler(MessageHandler(filters.CONTACT, handle_phone_number))
    
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
