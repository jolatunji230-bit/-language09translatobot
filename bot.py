#!/usr/bin/env python3
"""
Language09 Translator Bot
A Telegram bot that translates text between 100+ languages
Deployed on Railway with GitHub
"""

import os
import sys
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Try importing required libraries
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )
    logger.info("✅ python-telegram-bot imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import telegram: {e}")
    sys.exit(1)

try:
    from googletrans import Translator as GoogleTranslator
    logger.info("✅ googletrans imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ googletrans not available: {e}")
    GoogleTranslator = None

# ==================== LANGUAGE DATABASE ====================

LANGUAGES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
    'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
    'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)', 'co': 'Corsican', 'hr': 'Croatian',
    'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
    'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish',
    'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
    'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole',
    'ha': 'Hausa', 'haw': 'Hawaiian', 'he': 'Hebrew', 'hi': 'Hindi',
    'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo',
    'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese',
    'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer',
    'rw': 'Kinyarwanda', 'ko': 'Korean', 'ku': 'Kurdish', 'ky': 'Kyrgyz',
    'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
    'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
    'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori',
    'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar', 'ne': 'Nepali',
    'no': 'Norwegian', 'or': 'Odia', 'ps': 'Pashto', 'fa': 'Persian',
    'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian',
    'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic', 'sr': 'Serbian',
    'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala',
    'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali', 'es': 'Spanish',
    'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'tg': 'Tajik',
    'ta': 'Tamil', 'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai',
    'tr': 'Turkish', 'tk': 'Turkmen', 'uk': 'Ukrainian', 'ur': 'Urdu',
    'ug': 'Uyghur', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh',
    'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
}

# ==================== TRANSLATION ENGINE ====================

class TranslationEngine:
    def __init__(self):
        self.translator = None
        self.use_googletrans = False
        if GoogleTranslator:
            try:
                self.translator = GoogleTranslator()
                self.use_googletrans = True
                logger.info("✅ Using Google Translate engine")
            except Exception as e:
                logger.error(f"❌ Failed to initialize translator: {e}")

    def translate(self, text: str, dest: str = 'en', src: str = 'auto') -> Tuple[str, str]:
        if not text or not text.strip():
            return text, 'unknown'
        
        try:
            if self.use_googletrans and self.translator:
                result = self.translator.translate(text, dest=dest, src=src)
                return result.text, result.src
            else:
                return f"[Translation unavailable] {text}", 'unknown'
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[Error: {str(e)[:50]}] {text}", 'unknown'

    def detect(self, text: str) -> Tuple[str, float]:
        if not text or not text.strip():
            return 'unknown', 0.0
        
        try:
            if self.use_googletrans and self.translator:
                result = self.translator.detect(text)
                return result.lang, result.confidence
            else:
                return 'en', 0.5
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return 'unknown', 0.0

# Initialize translator
translator_engine = TranslationEngine()

# ==================== BOT HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    username = user.username or user.first_name
    
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = 'en'
    
    welcome_message = (
        f"🌍 *Welcome {username}!*\n"
        f"🤖 *Language09 Translator Bot*\n\n"
        f"I can translate between {len(LANGUAGES)} languages!\n\n"
        f"📌 *Your settings:*\n"
        f"• Target language: `{context.user_data['target_lang']}` ({LANGUAGES.get(context.user_data['target_lang'], 'Unknown')})\n\n"
        f"*Commands:*\n"
        f"🔹 /start - Welcome\n"
        f"🔹 /help - Help\n"
        f"🔹 /translate <text> - Translate\n"
        f"🔹 /lang <code> - Set language\n"
        f"🔹 /detect <text> - Detect language\n"
        f"🔹 /languages - List all languages\n"
        f"🔹 /about - About\n\n"
        f"💡 *Just send me any text and I'll translate it!*"
    )
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("📚 Languages", callback_data="list_langs")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = (
        f"*📖 Help - Language09 Translator Bot*\n\n"
        f"*Commands:*\n"
        f"• /translate <text> - Translate text\n"
        f"• /lang <code> - Set target language\n"
        f"• /detect <text> - Detect language\n"
        f"• /languages - Show all languages\n\n"
        f"*Examples:*\n"
        f"• `/translate Hello world`\n"
        f"• `/lang es` - Set Spanish\n"
        f"• `/detect Bonjour`\n\n"
        f"*Quick tip:* Just send any message for auto-translation!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_text = (
        f"*ℹ️ About Language09 Translator Bot*\n\n"
        f"🤖 *Bot:* @language09translatobot\n"
        f"🌍 *Languages:* {len(LANGUAGES)}\n"
        f"⚡ *Engine:* {'Google Translate' if translator_engine.use_googletrans else 'Fallback'}\n"
        f"🆓 *Status:* Free\n"
        f"🔒 *Privacy:* No data stored\n"
        f"💻 *Deployed on:* Railway + GitHub\n\n"
        f"*Features:*\n"
        f"• ✅ Instant translation\n"
        f"• ✅ Auto language detection\n"
        f"• ✅ 100+ languages\n"
        f"• ✅ Inline buttons\n\n"
        f"*Powered by:* Python, python-telegram-bot"
    )
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def list_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /languages command"""
    lang_list = []
    for code, name in sorted(LANGUAGES.items()):
        lang_list.append(f"• `{code}` - {name}")
    
    lang_text = f"*🌐 Supported Languages ({len(LANGUAGES)})*\n\n" + "\n".join(lang_list)
    
    if len(lang_text) > 4096:
        chunks = [lang_text[i:i+4096] for i in range(0, len(lang_text), 4096)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='Markdown')
    else:
        await update.message.reply_text(lang_text, parse_mode='Markdown')

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang command"""
    args = context.args
    
    if not args:
        current = context.user_data.get('target_lang', 'en')
        current_name = LANGUAGES.get(current, 'Unknown')
        await update.message.reply_text(
            f"📝 *Current Language:* `{current}` ({current_name})\n\n"
            f"To change: `/lang [code]`\n"
            f"Example: `/lang es`\n"
            f"Use `/languages` to see all codes.",
            parse_mode='Markdown'
        )
        return
    
    lang_code = args[0].lower()
    
    if lang_code in LANGUAGES:
        context.user_data['target_lang'] = lang_code
        await update.message.reply_text(
            f"✅ *Language updated!*\n\n"
            f"🌐 Target: `{lang_code}` ({LANGUAGES[lang_code]})\n"
            f"Send me any text to translate!",
            parse_mode='Markdown'
        )
    else:
        suggestions = [code for code in LANGUAGES.keys() if code.startswith(lang_code[:2])]
        suggestion_text = ""
        if suggestions:
            suggestion_text = f"\n\n💡 Did you mean: {', '.join([f'`{s}`' for s in suggestions[:5]])}"
        
        await update.message.reply_text(
            f"❌ *Invalid language code:* `{lang_code}`{suggestion_text}\n\n"
            f"Use `/languages` to see all codes.",
            parse_mode='Markdown'
        )

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /detect command"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "🔍 *Language Detection*\n\n"
            "Usage: `/detect [text]`\n"
            "Example: `/detect Hello, how are you?`",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(args)
    
    try:
        detected_lang, confidence = translator_engine.detect(text)
        lang_name = LANGUAGES.get(detected_lang, 'Unknown')
        
        response = (
            f"🔍 *Language Detection Result*\n\n"
            f"📝 *Text:* `{text[:100]}{'...' if len(text) > 100 else ''}`\n"
            f"🌐 *Language:* `{detected_lang}` ({lang_name})\n"
            f"📊 *Confidence:* {confidence:.2%}\n\n"
            f"💡 Send me text to translate!"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /translate command"""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    else:
        args = context.args
        if not args:
            await update.message.reply_text(
                "📝 *Translation Help*\n\n"
                "Usage: `/translate [text]`\n"
                "Or reply to a message with `/translate`\n\n"
                "Example: `/translate Hello world`",
                parse_mode='Markdown'
            )
            return
        text = " ".join(args)
    
    target_lang = context.user_data.get('target_lang', 'en')
    
    try:
        translated_text, source_lang = translator_engine.translate(text, dest=target_lang)
        source_name = LANGUAGES.get(source_lang, source_lang)
        target_name = LANGUAGES.get(target_lang, target_lang)
        
        response = (
            f"🌐 *Translation Complete*\n\n"
            f"📌 *Original:*\n{text[:500]}{'...' if len(text) > 500 else ''}\n\n"
            f"🔤 *Translated:*\n{translated_text}\n\n"
            f"📊 *From:* `{source_lang}` ({source_name})\n"
            f"📊 *To:* `{target_lang}` ({target_name})"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-translate any text message"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    if text.startswith('/') or len(text) < 2:
        return
    
    target_lang = context.user_data.get('target_lang', 'en')
    
    try:
        translated_text, source_lang = translator_engine.translate(text, dest=target_lang)
        
        if source_lang == target_lang:
            await update.message.reply_text(
                f"💡 This text is already in `{target_lang}`.\n"
                f"Use `/lang [code]` to change language.",
                parse_mode='Markdown'
            )
            return
        
        source_name = LANGUAGES.get(source_lang, source_lang)
        target_name = LANGUAGES.get(target_lang, target_lang)
        
        response = (
            f"🌍 *Translation*\n"
            f"From: `{source_lang}` ({source_name}) → To: `{target_lang}` ({target_name})\n\n"
            f"{translated_text}"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Auto-translation error: {e}")

# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "change_lang":
        keyboard = []
        popular = ['en', 'es', 'fr', 'de', 'ja', 'zh-cn', 'ar', 'hi', 'pt', 'ru']
        
        popular_row = []
        for code in popular:
            if code in LANGUAGES:
                popular_row.append(InlineKeyboardButton(
                    LANGUAGES[code][:3], 
                    callback_data=f"setlang_{code}"
                ))
        keyboard.append(popular_row)
        
        for code, name in list(LANGUAGES.items())[:20]:
            if code not in popular:
                keyboard.append([InlineKeyboardButton(
                    f"{name} ({code})", 
                    callback_data=f"setlang_{code}"
                )])
        
        keyboard.append([InlineKeyboardButton("📋 All Languages", callback_data="view_all_langs")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌐 *Select Target Language*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "view_all_langs":
        await list_languages(update, context)
        await query.message.edit_text(
            "📋 *All Languages*\n\nUse /languages to see the complete list.",
            parse_mode='Markdown'
        )
    
    elif query.data.startswith("setlang_"):
        lang_code = query.data.replace("setlang_", "")
        context.user_data['target_lang'] = lang_code
        await query.edit_message_text(
            f"✅ *Language Updated!*\n\n"
            f"🌐 Target: `{lang_code}` ({LANGUAGES.get(lang_code, 'Unknown')})\n"
            f"Send me any text to translate!",
            parse_mode='Markdown'
        )
    
    elif query.data == "list_langs":
        await list_languages(update, context)
    
    elif query.data == "help":
        await help_command(update, context)
    
    elif query.data == "back_to_start":
        await start(update, context)

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# ==================== MAIN FUNCTION ====================

def main() -> None:
    """Start the bot"""
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        logger.info("💡 Set BOT_TOKEN in Railway variables")
        sys.exit(1)
    
    logger.info("🚀 Starting Language09 Translator Bot...")
    logger.info(f"🌍 Languages: {len(LANGUAGES)}")
    logger.info(f"⚡ Engine: {'Google Translate' if translator_engine.use_googletrans else 'Fallback'}")
    
    try:
        application = Application.builder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("languages", list_languages))
        application.add_handler(CommandHandler("lang", set_language))
        application.add_handler(CommandHandler("detect", detect_language))
        application.add_handler(CommandHandler("translate", translate_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_translate))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_error_handler(error_handler)
        
        logger.info("✅ Bot is running!")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
