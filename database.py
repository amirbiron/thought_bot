"""
database.py - MongoDB connection and operations
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# חיבור ל-MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['thought_bot']

# Collections
users_collection = db['users']
items_collection = db['items']

# יצירת אינדקסים לביצועים טובים יותר
users_collection.create_index('user_id', unique=True)
items_collection.create_index([('user_id', 1), ('created_at', -1)])
items_collection.create_index([('user_id', 1), ('status', 1)])


def get_or_create_user(user_id):
    """מקבל או יוצר משתמש"""
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        user = {
            'user_id': user_id,
            'last_review_date': None,
            'created_at': datetime.now()
        }
        users_collection.insert_one(user)
    return user


def update_last_review(user_id):
    """מעדכן את תאריך הסיקור האחרון"""
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'last_review_date': datetime.now()}}
    )


def should_review(user_id):
    """בודק אם עבר שבוע מאז הסיקור האחרון"""
    user = users_collection.find_one({'user_id': user_id})
    if not user or not user.get('last_review_date'):
        return True
    
    week_ago = datetime.now() - timedelta(days=7)
    return user['last_review_date'] < week_ago


def add_item(user_id, item_type, content, tags=None):
    """מוסיף פריט חדש"""
    item = {
        'user_id': user_id,
        'type': item_type,
        'content': content,
        'tags': tags or [],
        'status': 'active',
        'created_at': datetime.now(),
        'keep_until': None,
        'reminder_date': None,
        'reminded': False
    }
    result = items_collection.insert_one(item)
    return str(result.inserted_id)


def get_items_today(user_id):
    """מחזיר פריטים מהיום"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return list(items_collection.find({
        'user_id': user_id,
        'status': 'active',
        'created_at': {'$gte': today_start}
    }).sort('created_at', -1))


def get_items_week(user_id):
    """מחזיר פריטים מהשבוע"""
    week_ago = datetime.now() - timedelta(days=7)
    return list(items_collection.find({
        'user_id': user_id,
        'status': 'active',
        'created_at': {'$gte': week_ago}
    }).sort('created_at', -1))


def get_archived_items(user_id):
    """מחזיר פריטים בארכיון"""
    return list(items_collection.find({
        'user_id': user_id,
        'status': 'archived'
    }).sort('created_at', -1).limit(50))


def search_items(user_id, query):
    """חיפוש פריטים"""
    return list(items_collection.find({
        'user_id': user_id,
        'status': {'$ne': 'deleted'},
        '$or': [
            {'content': {'$regex': query, '$options': 'i'}},
            {'tags': {'$regex': query, '$options': 'i'}}
        ]
    }).sort('created_at', -1).limit(30))


def get_item_by_id(item_id):
    """מקבל פריט לפי ID"""
    from bson.objectid import ObjectId
    return items_collection.find_one({'_id': ObjectId(item_id)})


def update_item_status(item_id, status):
    """מעדכן סטטוס של פריט"""
    from bson.objectid import ObjectId
    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'status': status}}
    )


def update_item_content(item_id, content):
    """מעדכן תוכן של פריט"""
    from bson.objectid import ObjectId
    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'content': content}}
    )


def keep_for_next_week(item_id):
    """שומר פריט לשבוע הבא"""
    from bson.objectid import ObjectId
    next_week = datetime.now() + timedelta(days=7)
    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'keep_until': next_week}}
    )


def set_reminder(item_id, reminder_date):
    """מגדיר תזכורת לפריט"""
    from bson.objectid import ObjectId
    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'reminder_date': reminder_date, 'reminded': False}}
    )


def get_pending_reminders(user_id):
    """מחזיר תזכורות שצריך לשלוח"""
    now = datetime.now()
    return list(items_collection.find({
        'user_id': user_id,
        'reminder_date': {'$lte': now},
        'reminded': False,
        'status': {'$ne': 'deleted'}
    }))


def mark_reminder_sent(item_id):
    """מסמן שתזכורת נשלחה"""
    from bson.objectid import ObjectId
    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'reminded': True}}
    )


def get_items_for_review(user_id):
    """מחזיר פריטים לסיקור שבועי"""
    week_ago = datetime.now() - timedelta(days=7)
    return list(items_collection.find({
        'user_id': user_id,
        'status': 'active',
        'created_at': {'$gte': week_ago}
    }).sort('created_at', 1))
