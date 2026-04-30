import random

WORDS = [
    "APPLE", "BANANA", "CAT", "DOG", "ELEPHANT", "FLOWER", "GUITAR", 
    "HOUSE", "ISLAND", "JACKET", "KITE", "LEMON", "MOUNTAIN", "NOTEBOOK", 
    "ORANGE", "PIANO", "QUEEN", "RABBIT", "SUN", "TREE", "UMBRELLA", 
    "VIOLIN", "WHALE", "XYLOPHONE", "YACHT", "ZEBRA"
]

def get_random_word() -> str:
    return random.choice(WORDS)

def mask_word(word: str) -> str:
    if not word:
        return ""
    # Show first letter, other letters as underscores
    masked = word[0] + " " + " ".join(["_" for _ in range(len(word) - 1)])
    return masked
