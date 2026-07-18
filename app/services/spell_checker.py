import re
from typing import Tuple

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Standard Levenshtein distance calculation.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

JEWELLERY_VOCABULARY = {
    # metals / materials
    "gold", "silver", "diamond", "rose", "white", "platinum", "stone", "stones",
    # categories
    "ring", "rings", "necklace", "necklaces", "earring", "earrings",
    "bracelet", "bracelets", "bangle", "bangles", "chain", "chains",
    "pendant", "pendants", "bridal", "collection",
    # occasions / usage
    "wedding", "engagement", "gift", "gifts", "office", "wear", "daily", "party",
    "festival", "anniversary", "birthday", "proposal", "luxury", "minimal",
    "traditional", "modern", "surprise", "popular", "best", "seller", "sellers",
    # query words
    "under", "below", "above", "price", "budget", "show", "find", "search", "buy",
    "want", "need", "for", "my", "wife", "husband", "mother", "sister", "friend",
    "bride", "me", "some", "any", "please", "surprise", "popular", "only", "about",
    "approximate", "rs", "inr", "size", "sizes"
}

COMMON_TYPO_MAP = {
    "gol": "gold",
    "dimond": "diamond",
    "dimon": "diamond",
    "neklace": "necklace",
    "necklac": "necklace",
    "neklas": "necklace",
    "pendent": "pendant",
    "pendand": "pendant",
    "braclet": "bracelet",
    "braclets": "bracelets",
    "barclet": "bracelet",
    "earing": "earrings",
    "earin": "earrings",
    "erring": "earrings",
    "bangl": "bangles",
}

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
    "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", 
    "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", 
    "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", 
    "by", "for", "with", "about", "against", "between", "into", "through", "during", 
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", 
    "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", 
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", 
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", 
    "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "know", 
    "dont", "choose", "help", "buy", "order", "track", "status", "support", "ticket", 
    "email", "issue", "complaint", "delivery", "arrive", "when", "one", "first", "second", 
    "third", "open", "link", "view", "show", "find", "search", "get", "product", "image", "images"
}

def correct_token(token: str) -> str:
    token_lower = token.lower()
    if token_lower in STOP_WORDS:
        return token
    if token_lower in COMMON_TYPO_MAP:
        return COMMON_TYPO_MAP[token_lower]
    if token_lower in JEWELLERY_VOCABULARY:
        return token_lower
    # Try fuzzy match with Levenshtein distance
    best_match = None
    min_dist = 999
    for vocab_word in JEWELLERY_VOCABULARY:
        dist = levenshtein_distance(token_lower, vocab_word)
        # Thresholds:
        # if len <= 3: max distance 1
        # if len >= 4: max distance 2
        max_allowed = 2 if len(vocab_word) >= 4 else 1
        if dist <= max_allowed and dist < min_dist:
            min_dist = dist
            best_match = vocab_word
            
    if best_match:
        return best_match
    return token

def format_display_query(text: str) -> str:
    words = text.split()
    formatted_words = []
    lowercase_exceptions = {"under", "below", "above", "for", "my", "to", "in", "on", "at", "by", "of", "and", "or", "a", "an", "the", "only"}
    
    for word in words:
        if word.isdigit():
            try:
                price_val = int(word)
                formatted_words.append(f"₹{price_val:,}")
            except ValueError:
                formatted_words.append(word)
        elif word.startswith("₹") and word[1:].replace(",", "").isdigit():
            try:
                price_val = int(word[1:].replace(",", ""))
                formatted_words.append(f"₹{price_val:,}")
            except ValueError:
                formatted_words.append(word)
        else:
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean.lower() in lowercase_exceptions:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())
                
    return " ".join(formatted_words)

def process_spelling_correction(text: str) -> Tuple[str, str, bool]:
    tokens = text.strip().split()
    corrected_tokens = []
    is_corrected = False
    
    for token in tokens:
        # Strip punctuation from start/end of token to check spelling
        m = re.match(r'^([^\w]*)(.*?)([^\w]*)$', token)
        if m:
            prefix, core, suffix = m.groups()
            if core.isalpha():
                corrected_core = correct_token(core)
                if corrected_core.lower() != core.lower():
                    is_corrected = True
                corrected_tokens.append(f"{prefix}{corrected_core}{suffix}")
            else:
                corrected_tokens.append(token)
        else:
            corrected_tokens.append(token)
            
    corrected_raw = " ".join(corrected_tokens)
    display_text = format_display_query(corrected_raw)
    return corrected_raw, display_text, is_corrected
