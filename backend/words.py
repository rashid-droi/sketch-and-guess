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
    # Initially show all underscores with spaces
    return " ".join(["_" for _ in range(len(word))])

def get_hint(word: str, hints_used: int) -> str:
    if not word:
        return ""
    
    # Reveal more letters as hints_used increases
    # 1st hint: Reveal 1st letter
    # 2nd hint: Reveal 1st and mid letter
    # 3rd hint: Reveal 1st, mid, and last letter
    
    chars = list("_" * len(word))
    indices_to_reveal = []
    
    if hints_used >= 1:
        indices_to_reveal.append(0)
    if hints_used >= 2:
        indices_to_reveal.append(len(word) // 2)
    if hints_used >= 3:
        indices_to_reveal.append(len(word) - 1)
        
    for i in indices_to_reveal:
        chars[i] = word[i]
        
    return " ".join(chars)
