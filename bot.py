#!/usr/bin/env python3
"""
Language09 Translator Bot
A Telegram bot that translates text between 100+ languages
Deployed on Railway with GitHub
"""

import os
import sys
import logging
import json
from typing import Dict, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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
    logger.info("🔄 Falling back to alternative translation method")
    GoogleTranslator = None

try:
    import httpx
    logger.info("✅ httpx imported successfully")
except ImportError:
    logger.warning("⚠️ httpx not available")

# ==================== CONFIGURATION ====================

# Language database - 100+ languages
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

# Bot configuration
BOT_CONFIG = {
    'default_lang': 'en',
    'max_text_length': 5000,
    'version': '1.0.0',
    'bot_name': 'language09translatobot'
}

# ==================== TRANSLATION ENGINE ====================

class TranslationEngine:
    """Handles translation with fallback mechanisms"""
    
    def __init__(self):
        self.translator = None
        self.use_googletrans = False
        self.init_translator()
    
    def init_translator(self):
        """Initialize the translation engine"""
        if GoogleTranslator:
            try:
                self.translator = GoogleTranslator()
                self.use_googletrans = True
                logger.info("✅ Using googletrans as translation engine")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to initialize googletrans: {e}")
        
        # Fallback to manual translation
        self.use_googletrans = False
        logger.warning("⚠️ Using fallback translation mode")
        return False
    
    def translate(self, text: str, dest: str = 'en', src: str = 'auto') -> Tuple[str, str]:
        """
        Translate text from source to destination language
        Returns: (translated_text, source_language)
        """
        if not text or not text.strip():
            return text, 'unknown'
        
        if len(text) > BOT_CONFIG['max_text_length']:
            text = text[:BOT_CONFIG['max_text_length']]
        
        try:
            if self.use_googletrans and self.translator:
                result = self.translator.translate(text, dest=dest, src=src)
                return result.text, result.src
            else:
                # Fallback: return original text with note
                return f"[⚠️ Translation unavailable] {text}", 'unknown'
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            return f"[❌ Error] {text}", 'unknown'
    
    def detect(self, text: str) -> Tuple[str, float]:
        """Detect language of text"""
        if not text or not text.strip():
            return 'unknown', 0.0
        
        try:
            if self.use_googletrans and self.translator:
                result = self.translator.detect(text)
                return result.lang, result.confidence
            else:
                return 'en', 0.5
        except Exception as e:
            logger.error(f"❌ Detection error: {e}")
            return 'unknown', 0.0

# Initialize translation engine
translator_engine = TranslationEngine()
logger.info(f"🚀 Translation engine ready (googletrans: {translator_engine.use_googletrans})")

# ==================== BOT HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    username = user.username or user.first_name
    
    # Set default language if not set
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = BOT_CONFIG['default_lang']
    
    # Get user stats
    if 'usage_count' not in context.user_data:
        context.user_data['usage_count'] = 0
    
    welcome_message = (
        f"🌍 *Welcome {username}!*\n"
        f"🤖 *Language09 Translator Bot*\n"
        f"Version: {BOT_CONFIG['version']}\n\n"
        f"I can translate text between {len(LANGUAGES)} languages instantly!\n\n"
        f"📌 *Your current settings:*\n"
        f"• Target language: `{context.user_data['target_lang']}` ({LANGUAGES.get(context.user_data['target_lang'], 'Unknown')})\n"
        f"• Total uses: {context.user_data['usage_count']}\n\n"
        f"*Commands:*\n"
        f"🔹 /start - Show this message\n"
        f"🔹 /help - Get help\n"
        f"🔹 /translate <text> - Translate text\n"
        f"🔹 /lang - Set target language\n"
        f"🔹 /detect <text> - Detect language\n"
        f"🔹 /languages - List all languages\n"
        f"🔹 /stats - Your statistics\n"
        f"🔹 /about - About this bot\n\n"
        f"💡 *Quick start:* Send me any text and I'll translate it!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("📚 Supported Languages", callback_data="list_langs")],
        [InlineKeyboardButton("📊 My Stats", callback_data="show_stats")],
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
        f"*Core Commands:*\n"
        f"• /translate <text> - Translate specific text\n"
        f"• /lang <code> - Set target language (e.g., /lang es)\n"
        f"• /detect <text> - Detect language of text\n"
        f"• /languages - Show all supported languages\n\n"
        f"*Other Commands:*\n"
        f"• /start - Welcome message\n"
        f"• /help - This help message\n"
        f"• /stats - Your usage statistics\n"
        f"• /about - About this bot\n\n"
        f"*Tips:*\n"
        f"• 📝 Send any message for auto-translation\n"
        f"• 🔄 Reply to a message with /translate to translate it\n"
        f"• 🌐 Use 2-letter ISO codes: en, es, fr, de, ja, ar\n"
        f"• 📋 See /languages for complete list\n\n"
        f"*Examples:*\n"
        f"• `/translate Hello world`\n"
        f"• `/lang es` (set Spanish)\n"
        f"• `/detect Bonjour`\n\n"
        f"🆘 Need more help? Contact @BotFather"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]]
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
        f"🤖 *Bot Name:* {BOT_CONFIG['bot_name']}\n"
        f"📦 *Version:* {BOT_CONFIG['version']}\n"
        f"🌍 *Languages:* {len(LANGUAGES)} supported\n"
        f"⚡ *Engine:* {'Google Translate' if translator_engine.use_googletrans else 'Fallback Mode'}\n"
        f"🆓 *Status:* Free to use\n"
        f"🔒 *Privacy:* No data stored\n"
        f"💻 *Source:* GitHub + Railway\n\n"
        f"*Features:*\n"
        f"• ✅ Instant translation\n"
        f"• ✅ Auto language detection\n"
        f"• ✅ 100+ languages\n"
        f"• ✅ Inline buttons\n"
        f"• ✅ Usage statistics\n\n"
        f"*Created by:* @language09translatobot\n"
        f"*Powered by:* Python, python-telegram-bot"
    )
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    usage_count = context.user_data.get('usage_count', 0)
    target_lang = context.user_data.get('target_lang', BOT_CONFIG['default_lang'])
    
    stats_text = (
        f"*📊 Your Statistics*\n\n"
        f"👤 *User:* {update.effective_user.username or update.effective_user.first_name}\n"
        f"🔄 *Total translations:* {usage_count}\n"
        f"🌐 *Target language:* {target_lang} ({LANGUAGES.get(target_lang, 'Unknown')})\n"
        f"📅 *First use:* {context.user_data.get('first_use', 'Not recorded')}\n"
        f"🏷️ *User ID:* {update.effective_user.id}\n\n"
        f"*Bot Status:*\n"
        f"• ✅ Online\n"
        f"• 🟢 Active\n"
        f"• 📡 Server: Railway"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def list_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /languages command"""
    # Create a formatted list
    lang_list = []
    for code, name in sorted(LANGUAGES.items()):
        lang_list.append(f"• `{code}` - {name}")
    
    lang_text = f"*🌐 Supported Languages ({len(LANGUAGES)})*\n\n" + "\n".join(lang_list)
    
    # Split into chunks if too long
    if len(lang_text) > 4096:
        chunks = []
        current_chunk = f"*🌐 Supported Languages ({len(LANGUAGES)})*\n\n"
        for item in lang_list:
            if len(current_chunk) + len(item) + 2 > 4096:
                chunks.append(current_chunk)
                current_chunk = "*Continued...*\n\n"
            current_chunk += item + "\n"
        chunks.append(current_chunk)
        
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='Markdown')
    else:
        await update.message.reply_text(lang_text, parse_mode='Markdown')

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang command"""
    args = context.args
    
    if not args:
        current = context.user_data.get('target_lang', BOT_CONFIG['default_lang'])
        current_name = LANGUAGES.get(current, 'Unknown')
        await update.message.reply_text(
            f"📝 *Current Language Settings*\n\n"
            f"🌐 Target language: `{current}` ({current_name})\n\n"
            f"To change, use: `/lang [code]`\n"
            f"Example: `/lang es` for Spanish\n"
            f"Use `/languages` to see all supported codes.",
            parse_mode='Markdown'
        )
        return
    
    lang_code = args[0].lower()
    
    if lang_code in LANGUAGES:
        context.user_data['target_lang'] = lang_code
        await update.message.reply_text(
            f"✅ *Language Updated!*\n\n"
            f"🌐 Target language: `{lang_code}` ({LANGUAGES[lang_code]})\n\n"
            f"📌 Send me any text and I'll translate it to {LANGUAGES[lang_code]}.",
            parse_mode='Markdown'
        )
    else:
        # Suggest similar languages
        suggestions = [code for code in LANGUAGES.keys() if code.startswith(lang_code[:2])]
        suggestion_text = ""
        if suggestions:
            suggestion_text = f"\n\n💡 Did you mean: {', '.join([f'`{s}`' for s in suggestions[:5]])}"
        
        await update.message.reply_text(
            f"❌ *Invalid Language Code*\n\n"
            f"`{lang_code}` is not supported.{suggestion_text}\n\n"
            f"📋 Use `/languages` to see all {len(LANGUAGES)} supported codes.",
            parse_mode='Markdown'
        )

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /detect command"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "🔍 *Language Detection*\n\n"
            "Please provide text to detect.\n"
            "Example: `/detect Hello, how are you?`\n\n"
            "💡 You can also just send any text and I'll auto-detect!",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(args)
    
    try:
        detected_lang, confidence = translator_engine.detect(text)
        lang_name = LANGUAGES.get(detected_lang, 'Unknown')
        
        # Determine confidence level
        confidence_level = "🔴 Low" if confidence < 0.3 else "🟡 Medium" if confidence < 0.7 else "🟢 High"
        
        response = (
            f"🔍 *Language Detection Result*\n\n"
            f"📝 *Text:* `{text[:100]}{'...' if len(text) > 100 else ''}`\n"
            f"🌐 *Language:* `{detected_lang}` ({lang_name})\n"
            f"📊 *Confidence:* {confidence:.2%} ({confidence_level})\n\n"
            f"💡 Want to translate? Send me text or use /translate!"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Detection error: {e}")
        await update.message.reply_text(
            f"❌ *Error detecting language*\n\n"
            f"Please try again with different text.",
            parse_mode='Markdown'
        )

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /translate command"""
    # Check if replying to a message
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    else:
        args = context.args
        if not args:
            await update.message.reply_text(
                "📝 *Translation Help*\n\n"
                "Usage: `/translate [text]`\n"
                "Or reply to a message with `/translate`\n\n"
                "Examples:\n"
                "• `/translate Hello world`\n"
                "• Reply to a message with `/translate`\n\n"
                "💡 For auto-translation, just send any text!",
                parse_mode='Markdown'
            )
            return
        text = " ".join(args)
    
    target_lang = context.user_data.get('target_lang', BOT_CONFIG['default_lang'])
    
    try:
        translated_text, source_lang = translator_engine.translate(text, dest=target_lang)
        source_name = LANGUAGES.get(source_lang, source_lang)
        target_name = LANGUAGES.get(target_lang, target_lang)
        
        # Update usage count
        context.user_data['usage_count'] = context.user_data.get('usage_count', 0) + 1
        if 'first_use' not in context.user_data:
            context.user_data['first_use'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        response = (
            f"🌐 *Translation Complete*\n\n"
            f"📌 *Original:*\n{text[:500]}{'...' if len(text) > 500 else ''}\n\n"
            f"🔤 *Translated:*\n{translated_text}\n\n"
            f"📊 *From:* `{source_lang}` ({source_name})\n"
            f"📊 *To:* `{target_lang}` ({target_name})"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(
            f"❌ *Translation Error*\n\n"
            f"Sorry, I couldn't translate that text.\n"
            f"Please try again or use different text.",
            parse_mode='Markdown'
        )

async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-translate any text message"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    # Skip if it's a command
    if text.startswith('/'):
        return
    
    # Skip if too short (avoid single characters)
    if len(text) < 2:
        return
    
    target_lang = context.user_data.get('target_lang', BOT_CONFIG['default_lang'])
    
    try:
        translated_text, source_lang = translator_engine.translate(text, dest=target_lang)
        
        # Skip if same language
        if source_lang == target_lang:
            # Still respond but inform user
            await update.message.reply_text(
                f"💡 *Info:* This text appears to already be in `{target_lang}`.\n"
                f"Use `/lang [code]` to change target language.\n\n"
                f"📝 *Detected:* {text[:100]}{'...' if len(text) > 100 else ''}",
                parse_mode='Markdown'
            )
            return
        
        # Update usage count
        context.user_data['usage_count'] = context.user_data.get('usage_count', 0) + 1
        if 'first_use' not in context.user_data:
            context.user_data['first_use'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
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
        # Silent fail for auto-translation

# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "change_lang":
        # Show popular languages first
        popular = ['en', 'es', 'fr', 'de', 'ja', 'zh-cn', 'ar', 'hi', 'pt', 'ru']
        keyboard = []
        
        # Popular languages row
        popular_row = []
        for code in popular:
            if code in LANGUAGES:
                popular_row.append(InlineKeyboardButton(
                    LANGUAGES[code][:3], 
                    callback_data=f"setlang_{code}"
                ))
        keyboard.append(popular_row)
        
        # More languages
        more_langs = list(LANGUAGES.items())[:20]
        for code, name in more_langs:
            if code not in popular:
                keyboard.append([InlineKeyboardButton(
                    f"{name} ({code})", 
                    callback_data=f"setlang_{code}"
                )])
        
        keyboard.append([InlineKeyboardButton("📋 View All Languages", callback_data="view_all_langs")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌐 *Select Your Target Language*\n\n"
            "Choose a language from below or use /lang command:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "view_all_langs":
        await list_languages(update, context)
        # Edit the previous message
        await query.message.edit_text(
            "📋 *All Languages*\n\n"
            "Use /languages to see the complete list in chat.",
            parse_mode='Markdown'
        )
    
    elif query.data.startswith("setlang_"):
        lang_code = query.data.replace("setlang_", "")
        context.user_data['target_lang'] = lang_code
        
        await query.edit_message_text(
            f"✅ *Language Updated!*\n\n"
            f"🌐 Target language: `{lang_code}` ({LANGUAGES.get(lang_code, 'Unknown')})\n\n"
            f"📌 Send me any text and I'll translate it automatically!\n"
            f"💡 Use /lang to change again.",
            parse_mode='Markdown'
        )
    
    elif query.data == "list_langs":
        await list_languages(update, context)
    
    elif query.data == "show_stats":
        await stats_command(update, context)
    
    elif query.data == "help":
        await help_command(update, context)
    
    elif query.data == "back_to_start":
        await start(update, context)

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ *Oops! Something went wrong.*\n\n"
                "Please try again later or use /help for assistance.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

# ==================== MAIN FUNCTION ====================

def main() -> None:
    """Start the bot"""
    # Get token from environment
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        logger.info("💡 Set BOT_TOKEN in Railway variables or .env file")
        sys.exit(1)
    
    logger.info("🚀 Starting Language09 Translator Bot...")
    logger.info(f"🌍 Supported languages: {len(LANGUAGES)}")
    logger.info(f"⚡ Translation engine: {'Google Translate' if translator_engine.use_googletrans else 'Fallback'}")
    
    try:
        # Create application
        application = Application.builder().token(token).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("languages", list_languages))
        application.add_handler(CommandHandler("lang", set_language))
        application.add_handler(CommandHandler("detect", detect_language))
        application.add_handler(CommandHandler("translate", translate_command))
        
        # Register message handler for auto-translation
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            auto_translate
        ))
        
        # Register callback handler for inline buttons
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Start bot
        logger.info("✅ Bot is running and ready to receive updates!")
        
        # Use webhook for Railway deployment
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_APP_ID"):
            logger.info("🚀 Deployed on Railway - Using polling mode")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
