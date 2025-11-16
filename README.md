# בוט ריקון מחשבות 🧠

בוט טלגרם מתקדם לניהול מחשבות ומשימות עם מערכת תיוג, תזכורות וסיקור שבועי אוטומטי.

## תכונות עיקריות ✨

- 💭 שמירת מחשבות ומשימות
- 🏷️ תיוג אוטומטי עם hashtags
- 📅 צפייה לפי תאריכים (היום, השבוע)
- 📦 מערכת ארכיון
- 🔍 חיפוש מתקדם
- ⏰ תזכורות גמישות
- 📋 סיקור שבועי אוטומטי
- ✏️ עריכה ומחיקה של פריטים

## התקנה 🚀

### 1. דרישות מקדימות

- Python 3.9+
- MongoDB Atlas account (חינמי)
- Telegram Bot Token

### 2. יצירת בוט בטלגרם

1. פתח שיחה עם [@BotFather](https://t.me/botfather)
2. שלח `/newbot` ועקוב אחר ההוראות
3. שמור את ה-Token שקיבלת

### 3. הגדרת MongoDB Atlas

1. צור חשבון ב-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. צור Cluster חדש (בחר בתוכנית החינמית)
3. לחץ על "Connect" וקבל את connection string
4. החלף `<password>` בסיסמה שלך

### 4. התקנת הפרויקט

```bash
# שכפול או הורדת הקבצים
cd thought_bot

# התקנת dependencies
pip install -r requirements.txt

# יצירת קובץ .env
cp .env.example .env
```

### 5. הגדרת משתני סביבה

ערוך את קובץ `.env`:

```env
TELEGRAM_TOKEN=your_bot_token_here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 6. הרצת הבוט

```bash
python bot.py
```

## העלאה ל-Render 🌐

### 1. הכנת הפרויקט

צור קובץ `render.yaml`:

```yaml
services:
  - type: web
    name: thought-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: TELEGRAM_TOKEN
        sync: false
      - key: MONGODB_URI
        sync: false
```

### 2. העלאה ל-Render

1. צור חשבון ב-[Render](https://render.com)
2. לחץ על "New" → "Web Service"
3. חבר את ה-GitHub repository או העלה את הקבצים
4. הוסף את משתני הסביבה:
   - `TELEGRAM_TOKEN`
   - `MONGODB_URI`
5. בחר בתוכנית בתשלום (כדי שהבוט לא ירדם)
6. לחץ על "Create Web Service"

### 3. בדיקת הבוט

פתח את הבוט בטלגרם ושלח `/start`

## שימוש 📱

### פקודות בסיסיות

- `/start` - התחלה וברוכים הבאים
- `/help` - מדריך שימוש מלא
- `/add` - הוספת פריט חדש
- `/cancel` - ביטול פעולה

### תפריט מהיר

השתמש בכפתורים בתחתית המסך:
- ➕ הוסף
- 📅 היום
- 📆 השבוע
- 📦 ארכיון
- 🔍 חיפוש
- 📋 סיקור

### הוספת פריט עם תגיות

```
זכור לקנות חלב #קניות #דחוף
```

הבוט יזהה אוטומטית את התגיות `#קניות` ו-`#דחוף`

### תזכורות

אחרי הוספת פריט, הבוט ישאל אם תרצה תזכורת:
- מחר
- בעוד 3 ימים
- בעוד שבוע
- תאריך מדויק (dd/mm/yyyy)

### סיקור שבועי

הבוט בודק אוטומטית אם עבר שבוע מאז הסיקור האחרון.
בסיקור תוכל:
- 📦 להעביר לארכיון
- ♻️ לשמור לשבוע הבא
- 🗑️ למחוק
- ⏭️ לדלג

## מבנה הפרויקט 📂

```
thought_bot/
├── bot.py              # קובץ הבוט הראשי
├── database.py         # פונקציות MongoDB
├── utils.py            # פונקציות עזר
├── requirements.txt    # תלויות
├── .env               # משתני סביבה (לא להעלות ל-git!)
└── README.md          # מדריך זה
```

## טיפים ⚡

1. **תגיות:** השתמש בתגיות קבועות לארגון טוב יותר
2. **סיקור קבוע:** עשה סיקור בכל סוף שבוע
3. **ארכיון:** העבר לארכיון דברים שסיימת, אל תמחק הכל
4. **תזכורות:** השתמש בתזכורות למשימות בעלות deadline

## תמיכה 💬

יש בעיה? 
1. בדוק את ה-logs ב-Render
2. ודא שמשתני הסביבה מוגדרים נכון
3. בדוק שה-MongoDB Atlas מאפשר גישה מכל מקום (IP Whitelist)

## רישיון 📄

MIT License - חופשי לשימוש ושינוי

---

נוצר עם ❤️ בעברית
