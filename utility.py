import random
import string
from datetime import datetime
from typing import Optional


def shorten_url(long_url: str, expires_at: Optional[datetime] = None):
    """Shorten a long URL and return the short URL."""
    # Generate a random 7-character string
    short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=7))

    # You could store the mapping in a database here
    # For now, just return a dummy shortened URL
    return f"localhost:8000/{short_code}"