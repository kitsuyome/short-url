import time
import threading
from app.database import SessionLocal
from app.crud import delete_expired_links, delete_unused_links
from app.config import settings

def cleanup_expired_links():
    while True:
        try:
            db = SessionLocal()
            count = delete_expired_links(db)
            if count:
                print(f"Удалено просроченных ссылок: {count}")
        except Exception as e:
            print(f"Ошибка при удалении просроченных ссылок: {e}")
        finally:
            db.close()
        time.sleep(3600)

def cleanup_unused_links():
    while True:
        try:
            db = SessionLocal()
            count = delete_unused_links(db, settings.INACTIVE_DAYS)
            if count:
                print(f"Удалено неиспользуемых ссылок: {count}")
        except Exception as e:
            print(f"Ошибка при удалении неиспользуемых ссылок: {e}")
        finally:
            db.close()
        time.sleep(3600)

def schedule_cleanup_task():
    thread1 = threading.Thread(target=cleanup_expired_links, daemon=True)
    thread1.start()
    thread2 = threading.Thread(target=cleanup_unused_links, daemon=True)
    thread2.start()
