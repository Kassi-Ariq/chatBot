
from better_profanity import profanity

# Load a custom profanity word list (optional)
profanity.load_censor_words()

def contains_profanity(text):
    """Check if text contains profanity."""
    return profanity.contains_profanity(text)

def clean_message(text):
    """Censor detected profanity in a message."""
    return profanity.censor(text)