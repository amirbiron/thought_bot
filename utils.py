"""
utils.py - Helper functions
"""
from datetime import datetime, timedelta
import re


def extract_tags(text):
    """מחלץ תגיות מטקסט (#תגית)"""
    tags = re.findall(r'#(\w+)', text)
    # מסיר את התגיות מהטקסט
    clean_text = re.sub(r'\s*#\w+', '', text).strip()
    return clean_text, tags


def format_item(item):
    """מעצב פריט להצגה"""
    item_type = "💭 מחשבה" if item['type'] == 'thought' else "✅ משימה"
    
    # תאריך
    created = item['created_at']
    days_ago = (datetime.now() - created).days
    if days_ago == 0:
        date_str = "היום"
    elif days_ago == 1:
        date_str = "אתמול"
    else:
        date_str = f"לפני {days_ago} ימים"
    
    # תגיות
    tags_str = ""
    if item.get('tags'):
        tags_str = " | " + " ".join([f"#{tag}" for tag in item['tags']])
    
    # תזכורת
    reminder_str = ""
    if item.get('reminder_date') and not item.get('reminded'):
        reminder_date = item['reminder_date']
        reminder_str = f"\n⏰ תזכורת ל-{reminder_date.strftime('%d/%m/%Y %H:%M')}"
    
    return f"{item_type} | {date_str}{tags_str}\n{item['content']}{reminder_str}"


def format_items_list(items):
    """מעצב רשימת פריטים"""
    if not items:
        return "אין פריטים להצגה 🤷‍♂️"
    
    result = []
    for idx, item in enumerate(items, 1):
        result.append(f"{idx}. {format_item(item)}")
        result.append("─" * 30)
    
    return "\n".join(result)


def get_reminder_date(option):
    """ממיר אופציית תזכורת לתאריך"""
    now = datetime.now()
    
    if option == "tomorrow":
        return now + timedelta(days=1)
    elif option == "3days":
        return now + timedelta(days=3)
    elif option == "week":
        return now + timedelta(days=7)
    else:
        return None


def format_reminder_option(option):
    """מעצב טקסט לכפתור תזכורת"""
    options = {
        "tomorrow": "מחר",
        "3days": "בעוד 3 ימים",
        "week": "בעוד שבוע"
    }
    return options.get(option, option)


def validate_date_input(text):
    """בודק ומחזיר תאריך מטקסט (dd/mm/yyyy או dd/mm)"""
    try:
        # ניסיון עם שנה
        if len(text.split('/')) == 3:
            return datetime.strptime(text, '%d/%m/%Y')
        # ניסיון בלי שנה (השנה הנוכחית)
        elif len(text.split('/')) == 2:
            date = datetime.strptime(text + f"/{datetime.now().year}", '%d/%m/%Y')
            # אם התאריך עבר השנה, מוסיף שנה
            if date < datetime.now():
                date = date.replace(year=date.year + 1)
            return date
    except:
        return None
