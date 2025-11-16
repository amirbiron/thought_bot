"""
bot.py - Main Telegram Bot
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)

import database as db
import utils

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# States לשיחות
ADD_CONTENT, ADD_REMINDER, EDIT_CONTENT, SEARCH_QUERY, CUSTOM_DATE = range(5)

# תפריט ראשי
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    ['➕ הוסף', '📅 היום'],
    ['📆 השבוע', '📦 ארכיון'],
    ['🔍 חיפוש', '📋 סיקור']
], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /start"""
    user_id = update.effective_user.id
    db.get_or_create_user(user_id)
    
    welcome_message = """
ברוך הבא לבוט ריקון מחשבות! 🧠

הבוט יעזור לך לשמור מחשבות ומשימות, לארגן אותם לפי נושאים, ולעשות סיקור שבועי.

📝 איך להשתמש:
• לחץ על "➕ הוסף" כדי להוסיף מחשבה או משימה
• הוסף תגיות עם # (לדוגמה: #עבודה #רעיון)
• הבוט יזכיר לך לעשות סיקור כל שבוע

השתמש בתפריט למטה או שלח /help למדריך מלא.

בהצלחה! 🚀
    """
    
    await update.message.reply_text(welcome_message, reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /help"""
    help_text = """
📚 מדריך שימוש מלא:

➕ *הוספת פריטים:*
לחץ "הוסף" ושלח את התוכן. אפשר להוסיף תגיות עם #

📅 *צפייה:*
• היום - פריטים שנוספו היום
• השבוע - כל הפריטים מ-7 הימים האחרונים
• ארכיון - פריטים ישנים שארכבת

🔍 *חיפוש:*
חפש לפי מילות מפתח או תגיות

📋 *סיקור שבועי:*
הבוט יזכיר לך אוטומטית לעשות סיקור כל שבוע.
באפשרותך גם להפעיל באופן ידני עם "סיקור"

⏰ *תזכורות:*
אחרי הוספת פריט, תוכל להוסיף תזכורת

✏️ *עריכה:*
לחץ על הכפתורים ליד כל פריט

---
/start - התחל מחדש
/help - מדריך זה
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def check_reminders_and_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """בודק תזכורות וצורך בסיקור"""
    user_id = update.effective_user.id
    
    # בדיקת תזכורות
    reminders = db.get_pending_reminders(user_id)
    for item in reminders:
        reminder_text = f"🔔 *תזכורת!*\n\n{utils.format_item(item)}"
        keyboard = get_item_keyboard(str(item['_id']))
        await context.bot.send_message(
            chat_id=user_id,
            text=reminder_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        db.mark_reminder_sent(str(item['_id']))
    
    # בדיקת צורך בסיקור
    if db.should_review(user_id):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("בוא נתחיל ✅", callback_data="start_review"),
            InlineKeyboardButton("אחר כך ⏰", callback_data="skip_review")
        ]])
        
        await context.bot.send_message(
            chat_id=user_id,
            text="היי! עבר שבוע מאז הסיקור האחרון 📋\n\nרוצה לעשות סיקור של הפריטים?",
            reply_markup=keyboard
        )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """התחלת תהליך הוספת פריט"""
    await update.message.reply_text(
        "מה תרצה להוסיף? 💭\n\n"
        "שלח את התוכן, ותוכל להוסיף תגיות עם # (לדוגמה: #עבודה #רעיון)\n\n"
        "שלח /cancel לביטול"
    )
    return ADD_CONTENT


async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """קבלת התוכן לפריט חדש"""
    text = update.message.text
    
    if text == '/cancel':
        await update.message.reply_text("בוטל ✖️", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    
    # חילוץ תגיות
    content, tags = utils.extract_tags(text)
    
    # שמירה בקונטקסט
    context.user_data['new_item'] = {
        'content': content,
        'tags': tags,
        'type': 'thought'  # ברירת מחדל
    }
    
    # בחירת סוג הפריט
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💭 מחשבה", callback_data="type_thought"),
            InlineKeyboardButton("✅ משימה", callback_data="type_task")
        ]
    ])
    
    tags_text = f"\nתגיות: {', '.join(['#' + t for t in tags])}" if tags else ""
    
    await update.message.reply_text(
        f"מעולה! קיבלתי:\n\n{content}{tags_text}\n\nזו מחשבה או משימה?",
        reply_markup=keyboard
    )
    
    return ADD_REMINDER


async def set_item_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """קביעת סוג הפריט"""
    query = update.callback_query
    await query.answer()
    
    item_type = 'thought' if 'thought' in query.data else 'task'
    context.user_data['new_item']['type'] = item_type
    
    # שאלה על תזכורת
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("מחר", callback_data="reminder_tomorrow")],
        [InlineKeyboardButton("בעוד 3 ימים", callback_data="reminder_3days")],
        [InlineKeyboardButton("בעוד שבוע", callback_data="reminder_week")],
        [InlineKeyboardButton("תאריך מדויק", callback_data="reminder_custom")],
        [InlineKeyboardButton("ללא תזכורת ✖️", callback_data="reminder_none")]
    ])
    
    await query.edit_message_text(
        "האם להוסיף תזכורת? ⏰",
        reply_markup=keyboard
    )
    
    return ADD_REMINDER


async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """קביעת תזכורת"""
    query = update.callback_query
    await query.answer()
    
    item_data = context.user_data['new_item']
    user_id = update.effective_user.id
    
    # הוספת הפריט
    item_id = db.add_item(
        user_id,
        item_data['type'],
        item_data['content'],
        item_data['tags']
    )
    
    # טיפול בתזכורת
    if 'none' in query.data:
        await query.edit_message_text(
            f"נשמר בהצלחה! ✅\n\n{utils.format_item(db.get_item_by_id(item_id))}",
            reply_markup=MAIN_KEYBOARD
        )
    elif 'custom' in query.data:
        context.user_data['pending_item_id'] = item_id
        await query.edit_message_text(
            "שלח תאריך בפורמט dd/mm/yyyy או dd/mm\n"
            "לדוגמה: 25/12 או 25/12/2024\n\n"
            "שלח /cancel לביטול"
        )
        return CUSTOM_DATE
    else:
        # תזכורת מהירה
        option = query.data.split('_')[1]
        reminder_date = utils.get_reminder_date(option)
        db.set_reminder(item_id, reminder_date)
        
        await query.edit_message_text(
            f"נשמר עם תזכורת! ✅⏰\n\n"
            f"{utils.format_item(db.get_item_by_id(item_id))}",
            reply_markup=MAIN_KEYBOARD
        )
    
    # ניקוי קונטקסט
    context.user_data.clear()
    return ConversationHandler.END


async def receive_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """קבלת תאריך מותאם אישית"""
    text = update.message.text
    
    if text == '/cancel':
        await update.message.reply_text("בוטל ✖️", reply_markup=MAIN_KEYBOARD)
        context.user_data.clear()
        return ConversationHandler.END
    
    date = utils.validate_date_input(text)
    
    if not date:
        await update.message.reply_text(
            "תאריך לא תקין ❌\n\n"
            "נסה שוב בפורמט: dd/mm/yyyy או dd/mm\n"
            "או שלח /cancel לביטול"
        )
        return CUSTOM_DATE
    
    item_id = context.user_data['pending_item_id']
    db.set_reminder(item_id, date)
    
    await update.message.reply_text(
        f"נשמר עם תזכורת! ✅⏰\n\n"
        f"{utils.format_item(db.get_item_by_id(item_id))}",
        reply_markup=MAIN_KEYBOARD
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת פריטים מהיום"""
    user_id = update.effective_user.id
    
    # בדיקת תזכורות וסיקור
    await check_reminders_and_review(update, context)
    
    items = db.get_items_today(user_id)
    
    if not items:
        await update.message.reply_text("אין פריטים מהיום 📅", reply_markup=MAIN_KEYBOARD)
        return
    
    for item in items:
        keyboard = get_item_keyboard(str(item['_id']))
        await update.message.reply_text(
            utils.format_item(item),
            reply_markup=keyboard
        )


async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת פריטים מהשבוע"""
    user_id = update.effective_user.id
    
    # בדיקת תזכורות וסיקור
    await check_reminders_and_review(update, context)
    
    items = db.get_items_week(user_id)
    
    if not items:
        await update.message.reply_text("אין פריטים מהשבוע 📆", reply_markup=MAIN_KEYBOARD)
        return
    
    await update.message.reply_text(f"נמצאו {len(items)} פריטים מהשבוע האחרון 📆")
    
    for item in items:
        keyboard = get_item_keyboard(str(item['_id']))
        await update.message.reply_text(
            utils.format_item(item),
            reply_markup=keyboard
        )


async def show_archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת ארכיון"""
    user_id = update.effective_user.id
    items = db.get_archived_items(user_id)
    
    if not items:
        await update.message.reply_text("הארכיון ריק 📦", reply_markup=MAIN_KEYBOARD)
        return
    
    await update.message.reply_text(f"הארכיון ({len(items)} פריטים) 📦")
    
    for item in items:
        keyboard = get_item_keyboard(str(item['_id']), is_archived=True)
        await update.message.reply_text(
            utils.format_item(item),
            reply_markup=keyboard
        )


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """התחלת חיפוש"""
    await update.message.reply_text(
        "מה תרצה לחפש? 🔍\n\n"
        "שלח מילת מפתח או תגית\n"
        "שלח /cancel לביטול"
    )
    return SEARCH_QUERY


async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ביצוע חיפוש"""
    query = update.message.text
    
    if query == '/cancel':
        await update.message.reply_text("בוטל ✖️", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    items = db.search_items(user_id, query)
    
    if not items:
        await update.message.reply_text(
            f'לא נמצאו תוצאות עבור "{query}" 🤷‍♂️',
            reply_markup=MAIN_KEYBOARD
        )
        return ConversationHandler.END
    
    await update.message.reply_text(f"נמצאו {len(items)} תוצאות 🔍")
    
    for item in items:
        keyboard = get_item_keyboard(str(item['_id']), item['status'] == 'archived')
        await update.message.reply_text(
            utils.format_item(item),
            reply_markup=keyboard
        )
    
    return ConversationHandler.END


def get_item_keyboard(item_id, is_archived=False):
    """יוצר מקלדת לפריט"""
    if is_archived:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 החזר לפעיל", callback_data=f"unarchive_{item_id}"),
            InlineKeyboardButton("🗑️ מחק", callback_data=f"delete_{item_id}")
        ]])
    else:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("✏️ ערוך", callback_data=f"edit_{item_id}"),
            InlineKeyboardButton("📦 ארכיון", callback_data=f"archive_{item_id}"),
            InlineKeyboardButton("🗑️ מחק", callback_data=f"delete_{item_id}")
        ]])


async def handle_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפעולות על פריטים"""
    query = update.callback_query
    await query.answer()
    
    action, item_id = query.data.split('_', 1)
    
    if action == 'archive':
        db.update_item_status(item_id, 'archived')
        await query.edit_message_text("הועבר לארכיון 📦")
    
    elif action == 'unarchive':
        db.update_item_status(item_id, 'active')
        await query.edit_message_text("הוחזר לפעיל 🔄")
    
    elif action == 'delete':
        db.update_item_status(item_id, 'deleted')
        await query.edit_message_text("נמחק 🗑️")
    
    elif action == 'edit':
        context.user_data['edit_item_id'] = item_id
        await query.edit_message_text(
            "שלח את התוכן החדש:\n\n"
            "שלח /cancel לביטול"
        )
        return EDIT_CONTENT


async def receive_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """קבלת תוכן ערוך"""
    text = update.message.text
    
    if text == '/cancel':
        await update.message.reply_text("בוטל ✖️", reply_markup=MAIN_KEYBOARD)
        context.user_data.clear()
        return ConversationHandler.END
    
    content, tags = utils.extract_tags(text)
    item_id = context.user_data['edit_item_id']
    
    db.update_item_content(item_id, content)
    
    await update.message.reply_text(
        f"עודכן בהצלחה! ✅\n\n{utils.format_item(db.get_item_by_id(item_id))}",
        reply_markup=MAIN_KEYBOARD
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """התחלת סיקור שבועי"""
    query = update.callback_query
    
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    items = db.get_items_for_review(user_id)
    
    if not items:
        message = "אין פריטים לסיקור! 🎉"
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message, reply_markup=MAIN_KEYBOARD)
        db.update_last_review(user_id)
        return
    
    # שמירה בקונטקסט
    context.user_data['review_items'] = [str(item['_id']) for item in items]
    context.user_data['review_index'] = 0
    
    # הצגת הפריט הראשון
    await show_review_item(update, context, query)


async def show_review_item(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """הצגת פריט בסיקור"""
    items_ids = context.user_data['review_items']
    index = context.user_data['review_index']
    
    if index >= len(items_ids):
        # סיום הסיקור
        message = f"סיימת את הסיקור! ✅\n\nעברת על {len(items_ids)} פריטים."
        if query:
            await query.edit_message_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        
        db.update_last_review(update.effective_user.id)
        context.user_data.clear()
        return
    
    item = db.get_item_by_id(items_ids[index])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 לארכיון", callback_data=f"review_archive_{item['_id']}")],
        [InlineKeyboardButton("♻️ שמור לשבוע הבא", callback_data=f"review_keep_{item['_id']}")],
        [InlineKeyboardButton("🗑️ מחק", callback_data=f"review_delete_{item['_id']}")],
        [InlineKeyboardButton("⏭️ דלג", callback_data="review_skip")]
    ])
    
    message = f"סיקור שבועי ({index + 1}/{len(items_ids)}) 📋\n\n{utils.format_item(item)}\n\nמה לעשות עם זה?"
    
    if query:
        await query.edit_message_text(message, reply_markup=keyboard)
    else:
        await update.callback_query.edit_message_text(message, reply_markup=keyboard)


async def handle_review_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפעולות בסיקור"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "review_skip":
        context.user_data['review_index'] += 1
        await show_review_item(update, context, query)
        return
    
    if query.data == "skip_review":
        await query.edit_message_text("אוקיי, נזכיר לך בפעם הבאה 👍")
        return
    
    action, item_id = query.data.split('_', 2)[1:]
    
    if action == 'archive':
        db.update_item_status(item_id, 'archived')
    elif action == 'keep':
        db.keep_for_next_week(item_id)
    elif action == 'delete':
        db.update_item_status(item_id, 'deleted')
    
    context.user_data['review_index'] += 1
    await show_review_item(update, context, query)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בהודעות טקסט מהתפריט"""
    text = update.message.text
    
    if text == '➕ הוסף':
        return await add_command(update, context)
    elif text == '📅 היום':
        return await show_today(update, context)
    elif text == '📆 השבוע':
        return await show_week(update, context)
    elif text == '📦 ארכיון':
        return await show_archive(update, context)
    elif text == '🔍 חיפוש':
        return await search_start(update, context)
    elif text == '📋 סיקור':
        return await start_review(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ביטול פעולה"""
    await update.message.reply_text("בוטל ✖️", reply_markup=MAIN_KEYBOARD)
    context.user_data.clear()
    return ConversationHandler.END


def main():
    """הפעלת הבוט"""
    token = os.getenv('TELEGRAM_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_TOKEN not found in environment variables!")
        return
    
    application = Application.builder().token(token).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # ConversationHandler להוספת פריט
    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            MessageHandler(filters.Regex('^➕ הוסף$'), add_command)
        ],
        states={
            ADD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_content)],
            ADD_REMINDER: [CallbackQueryHandler(set_item_type, pattern='^type_')],
            CUSTOM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_date)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # ConversationHandler לחיפוש
    search_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🔍 חיפוש$'), search_start)
        ],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_execute)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # ConversationHandler לעריכה
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_item_action, pattern='^edit_')],
        states={
            EDIT_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(add_conv)
    application.add_handler(search_conv)
    application.add_handler(edit_conv)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(set_reminder, pattern='^reminder_'))
    application.add_handler(CallbackQueryHandler(handle_item_action, pattern='^(archive|unarchive|delete)_'))
    application.add_handler(CallbackQueryHandler(start_review, pattern='^start_review$'))
    application.add_handler(CallbackQueryHandler(handle_review_action, pattern='^review_'))
    
    # Text handlers
    application.add_handler(MessageHandler(filters.Regex('^📅 היום$'), show_today))
    application.add_handler(MessageHandler(filters.Regex('^📆 השבוע$'), show_week))
    application.add_handler(MessageHandler(filters.Regex('^📦 ארכיון$'), show_archive))
    application.add_handler(MessageHandler(filters.Regex('^📋 סיקור$'), start_review))
    
    # התחלת הבוט
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
