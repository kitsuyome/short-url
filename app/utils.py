import random
import string

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def verify_custom_alias(custom_alias: str) -> bool:
    allowed_chars = string.ascii_letters + string.digits + "-_"
    return all(c in allowed_chars for c in custom_alias)
