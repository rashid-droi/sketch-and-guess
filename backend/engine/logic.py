import random

def mask_word(word: str, hints_revealed: int = 0) -> str:
    """
    Shows the first letter of every word and hides the rest.
    Preserves spaces and punctuation.
    """
    if not word:
        return ""
        
    words = word.split(" ")
    masked_words = []
    
    for w in words:
        if not w: 
            masked_words.append("")
            continue
            
        # First letter is always visible
        m = w[0]
        # Rest are underscores (preserving punctuation)
        for char in w[1:]:
            if char.isalnum():
                m += "_"
            else:
                m += char
        masked_words.append(m)
            
    return " ".join(masked_words)

def calculate_score(timer: int, max_timer: int, hints_used: int) -> int:
    """
    Base score depends on speed, reduced by hints used.
    """
    base_score = 100
    penalty = hints_used * 20
    
    time_factor = timer / max_timer if max_timer > 0 else 0
    score = int((base_score - penalty) * time_factor)
    
    return max(10, score)
