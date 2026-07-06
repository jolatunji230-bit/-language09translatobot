import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Try to import translator
try:
    from googletrans import Translator
    translator = Translator()
    USE_TRANSLATOR = True
    logger.info("✅ Google Translator loaded")
except:
    USE_TRANSLATOR = False
    logger.warning("⚠️ Google Translator not available, using fallback")

# Language database
LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh-cn': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
    'bn': 'Bengali', 'ur': 'Urdu', 'tr': 'Turkish', 'vi': 'Vietnamese',
    'th': 'Thai', 'id': 'Indonesian', 'ms': 'Malay', 'tl': 'Filipino',
    'pl': 'Polish', 'uk': 'Ukrainian', 'ro': 'Romanian', 'nl': 'Dutch',
    'sv': 'Swedish', 'no': 'Norwegian', 'da': 'Danish', 'fi': 'Finnish',
    'el': 'Greek', 'he': 'Hebrew', 'fa': 'Persian', 'sw': 'Swahili'
}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['target_lang'] = 'en'
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("📚 All Languages", callback_data="list_langs")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"🤖 I'm Language09 Translator Bot\n"
        f"🌍 I can translate between {len(LANGUAGES)} languages\n\n"
        f"📌 Just send me any text and I'll translate it!\n"
        f"🎯 Current target language: English\n\n"
        f"Commands:\n"
        f"/start - Show this menu\n"
        f"/help - Get help\n"
        f"/lang [code] - Set language\n"
        f"/translate [text] - Translate text\n"
        f"/languages - List all languages",
        reply_markup=reply_markup
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Help*\n\n"
        "• Send any text - Auto translate\n"
        "• /lang [code] - Set target language\n"
        "• /translate [text] - Translate specific text\n"
        "• /languages - Show all languages\n\n"
        "Examples:\n"
        "/lang es - Set Spanish\n"
        "/translate Hello world\n\n"
        "Supported languages: en, es, fr, de, it, pt, ru, ja, ar, hi, ur, tr, vi, th, id, ms, tl, pl, uk, ro, nl, sv, no, da, fi, el, he, fa, sw",
        parse_mode='Markdown'
    )

# Languages command
async def list_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_list = "\n".join([f"• {code}: {name}" for code, name in sorted(LANGUAGES.items())])
    await update.message.reply_text(
        f"🌐 *Supported Languages ({len(LANGUAGES)})*\n\n{lang_list}",
        parse_mode='Markdown'
    )

# Set language command
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        current = context.user_data.get('target_lang', 'en')
        await update.message.reply_text(
            f"📌 Current language: {current} - {LANGUAGES.get(current, 'Unknown')}\n"
            f"Use: /lang [code]\n"
            f"Example: /lang es"
        )
        return
    
    lang = args[0].lower()
    if lang in LANGUAGES:
        context.user_data['target_lang'] = lang
        await update.message.reply_text(f"✅ Language set to: {lang} - {LANGUAGES[lang]}")
    else:
        await update.message.reply_text(f"❌ Language '{lang}' not supported. Use /languages to see all.")

# Translate command
async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please provide text to translate.\nExample: /translate Hello")
        return
    
    text = " ".join(args)
    target = context.user_data.get('target_lang', 'en')
    
    try:
        if USE_TRANSLATOR:
            result = translator.translate(text, dest=target)
            await update.message.reply_text(
                f"📝 *Translation*\n\n"
                f"From: {result.src}\n"
                f"To: {target}\n\n"
                f"{result.text}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"⚠️ Translation not available. Please try again later.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

# Auto translate
async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    if text.startswith('/') or len(text) < 2:
        return
    
    target = context.user_data.get('target_lang', 'en')
    
    try:
        if USE_TRANSLATOR:
            result = translator.translate(text, dest=target)
            if result.src != target:
                await update.message.reply_text(
                    f"🌍 {result.text}\n\n"
                    f"From: {result.src} → To: {target}"
                )
    except Exception as e:
        logger.error(f"Translation error: {e}")

# Button callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "change_lang":
        keyboard = []
        for code, name in list(LANGUAGES.items())[:10]:
            keyboard.append([InlineKeyboardButton(f"{name} ({code})", callback_data=f"setlang_{code}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        await query.edit_message_text("🌐 Select language:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("setlang_"):
        lang = query.data.replace("setlang_", "")
        context.user_data['target_lang'] = lang
        await query.edit_message_text(f"✅ Language set to: {lang} - {LANGUAGES.get(lang, 'Unknown')}")
    
    elif query.data == "list_langs":
        lang_list = "\n".join([f"• {code}: {name}" for code, name in sorted(LANGUAGES.items())])
        await query.edit_message_text(f"🌐 Languages:\n{lang_list}")
    
    elif query.data == "help":
        await query.edit_message_text(
            "📖 Help\n\n"
            "• Send any text - Auto translate\n"
            "• /lang [code] - Set language\n"
            "• /translate [text] - Translate\n"
            "• /languages - List all"
        )
    
    elif query.data == "back":
        await start(update, context)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# Main function
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    logger.info("🚀 Starting Language09 Translator Bot...")
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("languages", list_languages))
    app.add_handler(CommandHandler("lang", set_language))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_translate))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot is ready!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
