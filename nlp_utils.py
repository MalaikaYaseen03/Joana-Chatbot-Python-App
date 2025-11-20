# -----------------------------
# Joana Fast Food Chatbot — NLP Utility Functions (Final Updated)
# -----------------------------
import re
import pandas as pd
from difflib import get_close_matches

# --- Intent Dictionary (Improved + Clean) ---
INTENTS = {
    "greeting": [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good evening",
        "مرحبا",
        "أهلاً",
        "اهلا",
        "هلا",
        "السلام",
        "السلام عليكم",
    ],
    "menu": ["menu", "show menu", "list", "قائمة", "القائمة"],
    "order_start": ["order", "buy", "أريد الطلب", "أطلب", "طلب", "ابغى", "أبغى"],
    "add_item": [
        "add",
        "zinger",
        "burger",
        "fries",
        "drink",
        "زنجر",
        "برغر",
        "بطاطس",
        "مشروب",
    ],
    "confirm": ["confirm", "ok", "تمام", "خلاص", "اعتمد", "اكيد", "نعم"],
    "payment": [
        "pay",
        "payment",
        "cash",
        "online",
        "card",
        "دفع",
        "بطاقة",
        "كاش",
        "نقد",
        "مدى",
    ],
    "branch": [
        "branch",
        "call",
        "address",
        "location",
        "فرع",
        "موقع",
        "مكان",
        "رقم",
        "اتصل",
    ],
    "timing": ["time", "open", "timing", "closing", "متى", "وقت", "ساعات العمل"],
    "abuse": ["stupid", "idiot", "fuck", "shit", "غبي", "تافه", "لعنة", "اخرس"],
}


# --- Load Menu Items from Excel ---
def load_menu_items():
    try:
        df = pd.read_excel("data/menu.xlsx")

        english_col = next(
            (
                c
                for c in df.columns
                if "english" in str(c).lower() or "item" in str(c).lower()
            ),
            None,
        )
        if not english_col:
            return []

        # Lowercase item names for matching
        items = [str(x).strip().lower() for x in df[english_col].dropna()]
        return items

    except Exception as e:
        print("⚠️ Menu load failed in nlp_utils:", e)
        return []


MENU_ITEMS = load_menu_items()


# --- Intent Detection (smart + safe) ---
def detect_intent(text):
    """
    Detects user intent:
    - First checks if sentence looks like a menu item
    - Then matches known intent keywords
    - Falls back to unknown
    """
    text_lower = text.lower().strip()

    # 1) Check if message closely matches a menu item
    match = get_close_matches(text_lower, MENU_ITEMS, n=1, cutoff=0.65)
    if match:
        return "add_item"

    # 2) Keyword-based intent detection
    for intent, keywords in INTENTS.items():
        for kw in keywords:
            if kw in text_lower:
                return intent

    return "unknown"


def detect_language(text):
    """
    Detect Arabic or English.
    Supports TRUE Arabic letters + roman-Arabic speech words.
    """

    text = text.strip().lower()

    # 1️⃣ Detect true Arabic letters
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"

    # # 2️⃣ Detect Roman Arabic (Chrome Voice Output)
    # roman_arabic_words = [
    #     "مرحبًا",
    #     "mar7aba",
    #     "salam",
    #     "assalam",
    #     "alsalam",
    #     "kaif",
    #     "keif",
    #     "kif",
    #     "keef",
    #     "hal",
    #     "shlon",
    #     "shlonek",
    #     "esh",
    #     "eshlo",
    #     "akl",
    #     "akil",
    #     "tamam",
    #     "tayeb",
    #     "zain",
    #     "naam",
    #     "na3am",
    #     "la",
    #     "mafi",
    #     "hadi",
    #     "hatha",
    #     "hade",
    #     "abgha",
    #     "abghi",
    #     "abga",
    #     "bghe",
    #     "joana",
    # ]

    # for word in roman_arabic_words:
    #     if word in text:
    #         return "ar"

    # 3️⃣ Default English
    return "en"
