# import os, re, difflib, datetime, sqlite3, threading, time
# from flask import Flask, render_template, request, jsonify, session
# from openai import OpenAI
# from nlp_utils import detect_intent, detect_language
# import pandas as pd
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# import pyttsx3  # voice engine

# # ---------------------------
# # Flask Config
# # ---------------------------
# app = Flask(__name__, static_folder="static", template_folder="templates")
# app.secret_key = os.environ.get("FLASK_SECRET_KEY", "joana-fastfood-secret")

# # Voice Engine (no file saving)
# engine = pyttsx3.init()
# engine.setProperty("rate", 175)
# engine.setProperty("volume", 1.0)

# # Constants
# PAYMENT_URL = "https://starlit-sopapillas-520aa2.netlify.app/?redirect=http://127.0.0.1:5000/thankyou"
# OPENROUTER_API_KEY = os.environ.get(
#     "OPENROUTER_API_KEY",
#     "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",
# )
# OPEN_HOUR, CLOSE_HOUR = 0, 24  # 24/7
# TAKEAWAY_ONLY = True
# CURRENCY = "SAR"  # Saudi Riyal
# CURRENCY_AR = "ريال سعودي"

# client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")


# # ---------------------------
# # Database Setup
# # ---------------------------
# def init_db():
#     os.makedirs("data", exist_ok=True)
#     conn = sqlite3.connect("data/orders.db")
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             item TEXT,
#             qty INTEGER,
#             spicy INTEGER,
#             nonspicy INTEGER,
#             price REAL,
#             subtotal REAL,
#             total REAL,
#             payment_method TEXT,
#             datetime TEXT
#         )
#     """
#     )
#     conn.commit()
#     conn.close()


# init_db()


# # ---------------------------
# # Excel Loaders
# # ---------------------------
# def load_menu():
#     try:
#         df_raw = pd.read_excel("data/Menu.xlsx", header=None)
#         header_row_index = None
#         for i, row in df_raw.iterrows():
#             if any("name_en" in str(c).lower() for c in row):
#                 header_row_index = i
#                 break
#         if header_row_index is None:
#             print("❌ Could not find header row containing 'name_en'")
#             return {}

#         df = pd.read_excel("data/Menu.xlsx", header=header_row_index)

#         def has(col, *keys):
#             c = str(col).strip().lower()
#             return any(k in c for k in keys)

#         english_col = next((c for c in df.columns if has(c, "name_en")), None)
#         arabic_col = next((c for c in df.columns if has(c, "name_ar")), None)
#         price_col = next((c for c in df.columns if has(c, "price")), None)
#         cat_col = next(
#             (c for c in df.columns if has(c, "category", "cat", "type")), None
#         )

#         if not english_col or not price_col:
#             raise Exception("Missing name_en or price column")

#         menu = {}
#         for _, row in df.iterrows():
#             en = str(row[english_col]).strip().lower()
#             if not en or en == "nan":
#                 continue
#             ar = str(row[arabic_col]).strip().lower() if arabic_col else en
#             category = str(row.get(cat_col, "")).strip().lower() if cat_col else ""
#             try:
#                 price = float(row[price_col])
#             except:
#                 continue
#             entry = {"price": price, "category": category}
#             menu[en] = entry
#             if ar:
#                 menu[ar] = entry
#         print(f"✅ Loaded {len(menu)} menu items.")
#         return menu
#     except Exception as e:
#         print("❌ Menu load failed:", e)
#         return {}


# def load_branches():
#     try:
#         df_raw = pd.read_excel("data/Branches.xlsx", header=None)
#         header_row_index = None
#         for i, row in df_raw.iterrows():
#             row_l = [str(c).lower() for c in row]
#             if any("branch" in c for c in row_l) and any("address" in c for c in row_l):
#                 header_row_index = i
#                 break
#         if header_row_index is None:
#             header_row_index = 0

#         df = pd.read_excel("data/Branches.xlsx", header=header_row_index)
#         name_col = next((c for c in df.columns if "branch" in str(c).lower()), None)
#         addr_col = next((c for c in df.columns if "address" in str(c).lower()), None)
#         phone_col = next(
#             (
#                 c
#                 for c in df.columns
#                 if "phone" in str(c).lower() or "number" in str(c).lower()
#             ),
#             None,
#         )

#         branches = []
#         for _, row in df.iterrows():
#             branches.append(
#                 {
#                     "Branch Name": str(row.get(name_col, "")).strip(),
#                     "Address / Area": str(row.get(addr_col, "")).strip(),
#                     "Phone Number": str(row.get(phone_col, "")).strip(),
#                 }
#             )

#         print(f"✅ Loaded {len(branches)} branches.")
#         return [
#             b
#             for b in branches
#             if (b["Branch Name"] or b["Address / Area"] or b["Phone Number"])
#         ]
#     except Exception as e:
#         print("❌ Branch load failed:", e)
#         return []


# MENU = load_menu()
# BRANCHES = load_branches()


# # ---------------------------
# # File Watcher
# # ---------------------------
# class FileChangeHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         global MENU, BRANCHES
#         if "menu.xlsx" in event.src_path.lower():
#             MENU = load_menu()
#         elif "branches.xlsx" in event.src_path.lower():
#             BRANCHES = load_branches()


# def start_watcher():
#     observer = Observer()
#     observer.schedule(FileChangeHandler(), path="data", recursive=False)
#     observer.start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()


# threading.Thread(target=start_watcher, daemon=True).start()


# # ---------------------------
# # Helpers
# # ---------------------------
# def detect_qty(msg):
#     nums = re.findall(r"\d+", msg)
#     if nums:
#         return int(nums[0])
#     return 1


# def polite_check(text):
#     bad = ["idiot", "stupid", "حرام", "لعنة", "غبي"]
#     return any(w in text.lower() for w in bad)


# def get_price_and_category(name):
#     entry = MENU.get(name.lower(), {})
#     return float(entry.get("price", 0)), entry.get("category", "")


# def speak_text(reply, lang):
#     try:
#         voices = engine.getProperty("voices")
#         if lang == "ar":
#             for v in voices:
#                 if "arab" in v.name.lower() or "ar" in v.id.lower():
#                     engine.setProperty("voice", v.id)
#                     break
#         else:
#             for v in voices:
#                 if "english" in v.name.lower() or "en" in v.id.lower():
#                     engine.setProperty("voice", v.id)
#                     break
#         engine.say(reply)
#         engine.runAndWait()
#     except Exception as e:
#         print("Voice error:", e)


# def parse_spice_split(msg):
#     """
#     Detect patterns like '1 spicy 1 non spicy' or '2 spicy 3 non'.
#     Returns (spicy_qty, non_qty) or None.
#     """
#     text = msg.lower().replace("-", " ")
#     nums = re.findall(r"\d+", text)
#     if len(nums) >= 2:
#         n1, n2 = int(nums[0]), int(nums[1])
#         if ("spicy" in text or "حار" in text) and (
#             "non" in text or "mild" in text or "عادي" in text or "بدون" in text
#         ):
#             spicy_first = (
#                 text.find("spicy") < text.find("non") if "non" in text else True
#             )
#             arab_spicy_first = (
#                 text.find("حار") < text.find("عادي") if "عادي" in text else True
#             )
#             if spicy_first or arab_spicy_first:
#                 return (n1, n2)
#             else:
#                 return (n2, n1)
#     return None


# def find_menu_item(msg):
#     """
#     More accurate item detection:
#     - uses word boundaries so 'ok' / 'yes' won't match any item
#     - if multiple items match, pick the longest (most specific) name
#     """
#     text = msg.lower()
#     candidates = []
#     for name in MENU.keys():
#         # word-boundary match (allow simple plural 's')
#         pattern = r"\b" + re.escape(name) + r"s?\b"
#         if re.search(pattern, text):
#             candidates.append(name)

#     if not candidates:
#         return None

#     # pick longest name → avoids 'burger' catching when 'beef burger' also exists
#     candidates.sort(key=len, reverse=True)
#     return candidates[0]


# # ---------------------------
# # LLM Reply
# # ---------------------------
# def get_llm_reply(msg, lang="en"):
#     lang_name = "English" if lang == "en" else "Arabic"

#     sys_prompt = (
#         "You are Joana Fast Food Assistant.\n"
#         "Your rules:\n"
#         "- Answer ANY user question correctly — not only restaurant questions.\n"
#         "- Always keep answers SHORT, CLEAR, and TO THE POINT.\n"
#         "- Never write long paragraphs.\n"
#         "- Be very polite and friendly.\n\n"
#         "Restaurant Knowledge:\n"
#         "- Joana Fast Food is open 24 hours, 7 days a week.\n"
#         "- Only takeaway service is available (no delivery).\n"
#         "- You can explain menu items, spicy preferences, and prices.\n"
#         "- You help with branches, timings, orders, and payment.\n\n"
#         "If user asks something NOT related to the restaurant:\n"
#         "- First give a SHORT and CORRECT answer.\n"
#         "- Then gently bring them back to Joana Fast Food.\n\n"
#         f"Always respond in {lang_name}.\n"
#     )

#     context = f"MENU: {', '.join(list(MENU.keys())[:30])}"

#     messages = [
#         {"role": "system", "content": sys_prompt},
#         {"role": "system", "content": context},
#     ]

#     for m in session.get("messages", []):
#         messages.append(m)

#     messages.append({"role": "user", "content": msg})

#     try:
#         res = client.chat.completions.create(
#             model="gpt-4o-mini", messages=messages, temperature=0.5, max_tokens=250
#         )
#         return res.choices[0].message.content.strip()

#     except Exception as e:
#         print("LLM error:", e)
#         return "Sorry, something went wrong." if lang == "en" else "عذراً، حدث خطأ ما."


# # ---------------------------
# # Routes
# # ---------------------------
# @app.route("/")
# def index():
#     return render_template("index.html")


# @app.route("/api/chat", methods=["POST"])
# def chat():
#     global MENU, BRANCHES
#     MENU = load_menu()
#     BRANCHES = load_branches()

#     s = session.get("state", {"stage": None, "order": [], "total": 0})
#     session["messages"] = session.get("messages", [])

#     data = request.get_json(force=True)
#     msg = (data.get("message") or "").strip()
#     is_voice = data.get("is_voice", False)
#     lang = detect_language(msg)
#     intent = detect_intent(msg)
#     session["messages"].append({"role": "user", "content": msg})

#     # ----------------- Politeness check -----------------
#     if polite_check(msg):
#         reply = "Please speak politely." if lang == "en" else "من فضلك تحدث بأدب."
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Greeting / Start -----------------
#     if intent == "greeting" or s["stage"] is None:
#         s = {
#             "stage": "branch",
#             "order": [],
#             "total": 0,
#             "last_item": None,
#             "last_qty": 0,
#         }
#         session["state"] = s

#         reply = (
#             "Welcome to JOANA Fast Food! 🍔<br>"
#             "Find your nearest branch and dial the number to order:<br><br>"
#             + "<br>".join(
#                 [
#                     f"<b>{b.get('Branch Name','')}</b> – {b.get('Address / Area','')}<br>"
#                     f"📞 <a href='tel:{b.get('Phone Number','')}'><b>{b.get('Phone Number','')}</b></a><br>"
#                     for b in BRANCHES
#                     if b.get("Phone Number")
#                 ][:6]
#             )
#             + "<br>Ready to order? Share your order via voice or chat!"
#         )

#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Menu intent -----------------
#     if intent == "menu":
#         reply = (
#             "Here’s our menu! Please place your order."
#             if lang == "en"
#             else "هذه قائمتنا! من فضلك ضع طلبك."
#         )
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "menu": "/static/menu.PNG", "lang": lang})

#     # ----------------- Awaiting spice selection -----------------
#     if s.get("stage") == "await_spice" and s.get("last_item"):
#         last_item = s["last_item"]
#         last_qty = s.get("last_qty", 1)
#         price, _category = get_price_and_category(last_item)
#         split = parse_spice_split(msg)

#         if split:
#             spicy_q, non_q = split
#         else:
#             lower_msg = msg.lower()
#             if any(k in lower_msg for k in ["spicy", "hot", "حار"]):
#                 spicy_q, non_q = last_qty, 0
#             elif any(k in lower_msg for k in ["non", "mild", "عادي", "بدون"]):
#                 spicy_q, non_q = 0, last_qty
#             else:
#                 spicy_q, non_q = 0, last_qty  # default all non-spicy

#         order_added_msgs = []
#         if spicy_q > 0:
#             s["order"].append(
#                 {
#                     "item": last_item,
#                     "qty": spicy_q,
#                     "spicy": 1,
#                     "nonspicy": 0,
#                     "price": price,
#                     "subtotal": spicy_q * price,
#                 }
#             )
#             order_added_msgs.append(f"{spicy_q} {'spicy' if lang=='en' else 'حار'}")
#         if non_q > 0:
#             s["order"].append(
#                 {
#                     "item": last_item,
#                     "qty": non_q,
#                     "spicy": 0,
#                     "nonspicy": 1,
#                     "price": price,
#                     "subtotal": non_q * price,
#                 }
#             )
#             order_added_msgs.append(
#                 f"{non_q} {'non-spicy' if lang=='en' else 'بدون حار'}"
#             )

#         s["stage"] = "add_more"
#         s["last_item"] = None
#         s["last_qty"] = 0
#         session["state"] = s

#         reply = (
#             f"Added {last_item.title()} — "
#             + " & ".join(order_added_msgs)
#             + ". Would you like to add anything else?"
#             if lang == "en"
#             else f"تمت إضافة {last_item} — "
#             + " و ".join(order_added_msgs)
#             + ". هل ترغب في إضافة شيء آخر؟"
#         )
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Order Detection -----------------
#     found = find_menu_item(msg)

#     if found:
#         qty = detect_qty(msg)
#         price, category = get_price_and_category(found)

#         s["last_item"] = found
#         s["last_qty"] = qty
#         session["state"] = s

#         incoming = msg.lower()
#         spicy_flag = any(x in incoming for x in ["spicy", "hot", "حار"])
#         nonspicy_flag = any(x in incoming for x in ["non", "mild", "عادي", "بدون"])

#         # If burger/sandwich and no spice info → ask spicy/non-spicy
#         if category in ["burgers", "sandwiches"] and not (spicy_flag or nonspicy_flag):
#             s["stage"] = "await_spice"
#             session["state"] = s
#             reply = (
#                 f"Would you like your {found.title()} spicy or non-spicy?"
#                 if lang == "en"
#                 else f"هل ترغب أن يكون {found} حارًا أم بدون حار؟"
#             )
#             if is_voice:
#                 speak_text(reply, lang)
#             return jsonify({"reply": reply, "lang": lang})

#         # Else directly add item
#         spicy = 1 if spicy_flag else 0
#         nonspicy = 0 if spicy_flag else 1
#         s["order"].append(
#             {
#                 "item": found,
#                 "qty": qty,
#                 "spicy": spicy,
#                 "nonspicy": nonspicy,
#                 "price": price,
#                 "subtotal": qty * price,
#             }
#         )
#         s["stage"] = "add_more"
#         s["last_item"] = None
#         s["last_qty"] = 0
#         session["state"] = s

#         reply = (
#             f"{found.title()} ×{qty} added! Would you like to add anything else?"
#             if lang == "en"
#             else f"تمت إضافة {found} ×{qty}! هل ترغب في إضافة شيء آخر؟"
#         )
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Check for order completion -----------------
#     if any(
#         x in msg.lower() for x in ["no", "done", "that's all", "that all", "خلص", "لا"]
#     ):
#         if s.get("order"):

#             total = sum(i.get("subtotal", 0) for i in s["order"])
#             summary = []

#             for i in s["order"]:
#                 item_name = i["item"]
#                 item_info = MENU.get(item_name.lower(), {})

#                 # Burgers / Sandwiches → show spicy in Arabic
#                 if item_info.get("category") in ["burgers", "sandwiches"]:
#                     if lang == "ar":
#                         kind = "حار" if i.get("spicy") else "بدون حار"
#                     else:
#                         kind = "spicy" if i.get("spicy") else "non-spicy"

#                     summary.append(f"{i['qty']} {kind} {item_name.title()}")
#                 else:
#                     summary.append(f"{i['qty']} {item_name.title()}")

#             reply = (
#                 f"Your order is confirmed! Here's a summary:<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
#                 + "Would you like to proceed with the payment?"
#                 if lang == "en"
#                 else "تم تأكيد طلبك!<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
#                 + "هل ترغب في المتابعة إلى الدفع؟"
#             )

#             s["stage"] = "payment"
#             s["total"] = total
#             session["state"] = s

#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Payment confirmation (yes/ok) -----------------
#     if s.get("stage") == "payment" and any(
#         x in msg.lower() for x in ["yes", "sure", "ok", "okay", "تمام", "نعم", "أكيد"]
#     ):
#         total = s.get("total", 0)
#         reply = (
#             "How would you like to pay?<br><b>Cash</b> or <b>Online Payment</b>?"
#             if lang == "en"
#             else "كيف ترغب في الدفع؟<br><b نقدي </b> أو <b> الدفع عبر الإنترنت</b>؟"
#         )
#         s["stage"] = "choose_payment"
#         session["state"] = s
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Handle payment type selection -----------------
#     if s.get("stage") == "choose_payment":
#         total = s.get("total", 0)
#         msg_l = msg.lower()

#         # Cash on Delivery
#         if any(x in msg_l for x in ["cash", "cod", "نقد", "نقدا"]):
#             reply = (
#                 "Thank you for your order! Your order will be ready in 20 to 30 minutes."
#                 if lang == "en"
#                 else "شكراً لطلبك! سيكون جاهزاً خلال 20 إلى 30 دقيقة."
#             )
#             # reset session
#             s = {
#                 "stage": None,
#                 "order": [],
#                 "total": 0,
#                 "last_item": None,
#                 "last_qty": 0,
#             }
#             session["state"] = s
#             if is_voice:
#                 speak_text(reply, lang)
#             return jsonify({"reply": reply, "lang": lang})

#         # Online payment
#         elif any(
#             x in msg_l
#             for x in [
#                 "online",
#                 "online payment",
#                 "pay online",
#                 "card",
#                 "visa",
#                 "master",
#                 "debit",
#                 "mada",
#                 "مدى",
#                 "إلكتروني",
#                 "دفع",
#                 "كرت",
#             ]
#         ):

#             reply = (
#                 f"Great! Your payment of {total:.2f} {CURRENCY} is being processed.<br>"
#                 f"<a href='{PAYMENT_URL}' target='_blank'><b>Click here to complete your payment</b></a>"
#                 if lang == "en"
#                 else f"رائع! يتم الآن معالجة دفعتك بمقدار {total:.2f} {CURRENCY_AR}.<br>"
#                 f"<a href='{PAYMENT_URL}' target='_blank'><b>اضغط هنا لإتمام الدفع</b></a>"
#             )
#             # reset session
#             s = {
#                 "stage": None,
#                 "order": [],
#                 "total": 0,
#                 "last_item": None,
#                 "last_qty": 0,
#             }
#             session["state"] = s
#             if is_voice:
#                 speak_text(reply, lang)
#             return jsonify({"reply": reply, "lang": lang})

#         # Invalid payment option
#         else:
#             reply = (
#                 "Please select a valid payment method — Cash or Online."
#                 if lang == "en"
#                 else "يرجى اختيار طريقة الدفع الصحيحة - نقدًا أو عبر الإنترنت"
#             )
#             if is_voice:
#                 speak_text(reply, lang)
#             return jsonify({"reply": reply, "lang": lang})

#     # ----------------- default → LLM -----------------
#     reply = get_llm_reply(msg, lang)
#     if is_voice:
#         speak_text(reply, lang)
#     return jsonify({"reply": reply, "lang": lang})


# # ---------------------------
# # Run App
# # ---------------------------
# if __name__ == "__main__":
#     app.run(debug=True)

# import datetime
# import os
# import re
# import sqlite3
# import threading
# import time
# import difflib  # (imported but not used – kept as in original)

# import pandas as pd
# import pyttsx3  # voice engine
# from flask import Flask, render_template, request, jsonify, session
# from nlp_utils import detect_intent, detect_language
# from openai import OpenAI
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

# # ---------------------------
# # Paths / Directories
# # ---------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR = os.path.join(BASE_DIR, "data")

# # Excel files (change only these if you rename/move them)
# MENU_FILE = os.path.join(DATA_DIR, "Menu.xlsx")
# BRANCHES_FILE = os.path.join(DATA_DIR, "Branches.xlsx")


# # ---------------------------
# # Flask Config
# # ---------------------------
# app = Flask(__name__, static_folder="static", template_folder="templates")
# app.secret_key = os.environ.get("FLASK_SECRET_KEY", "joana-fastfood-secret")

# # Voice Engine (no file saving)
# engine = pyttsx3.init()
# engine.setProperty("rate", 175)
# engine.setProperty("volume", 1.0)

# # Constants
# PAYMENT_URL = (
#     "https://starlit-sopapillas-520aa2.netlify.app/"
#     "?redirect=http://127.0.0.1:5000/thankyou"
# )
# OPENROUTER_API_KEY = os.environ.get(
#     "OPENROUTER_API_KEY",
#     "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",
# )
# OPEN_HOUR, CLOSE_HOUR = 0, 24  # 24/7
# TAKEAWAY_ONLY = True
# CURRENCY = "SAR"
# CURRENCY_AR = "ريال سعودي"

# client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")


# # ---------------------------
# # Database Setup
# # ---------------------------
# def init_db():
#     os.makedirs(DATA_DIR, exist_ok=True)
#     conn = sqlite3.connect(os.path.join(DATA_DIR, "orders.db"))
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             item TEXT,
#             qty INTEGER,
#             spicy INTEGER,
#             nonspicy INTEGER,
#             price REAL,
#             subtotal REAL,
#             total REAL,
#             payment_method TEXT,
#             datetime TEXT
#         )
#         """
#     )
#     conn.commit()
#     conn.close()


# init_db()


# # ---------------------------
# # Excel Loaders
# # ---------------------------
# def load_menu():
#     try:
#         df_raw = pd.read_excel(MENU_FILE, header=None)
#         header_row_index = None

#         for i, row in df_raw.iterrows():
#             if any("name_en" in str(c).lower() for c in row):
#                 header_row_index = i
#                 break

#         if header_row_index is None:
#             print("❌ Could not find header row containing 'name_en'")
#             return {}

#         df = pd.read_excel(MENU_FILE, header=header_row_index)

#         def has(col, *keys):
#             c = str(col).strip().lower()
#             return any(k in c for k in keys)

#         english_col = next((c for c in df.columns if has(c, "name_en")), None)
#         arabic_col = next((c for c in df.columns if has(c, "name_ar")), None)
#         price_col = next((c for c in df.columns if has(c, "price")), None)
#         cat_col = next(
#             (c for c in df.columns if has(c, "category", "cat", "type")), None
#         )

#         if not english_col or not price_col:
#             raise Exception("Missing name_en or price column")

#         menu = {}
#         for _, row in df.iterrows():
#             en = str(row[english_col]).strip().lower()
#             if not en or en == "nan":
#                 continue

#             ar = str(row[arabic_col]).strip().lower() if arabic_col else en
#             category = str(row.get(cat_col, "")).strip().lower() if cat_col else ""

#             try:
#                 price = float(row[price_col])
#             except Exception:
#                 continue

#             entry = {"price": price, "category": category}
#             menu[en] = entry
#             if ar:
#                 menu[ar] = entry

#         print(f"✅ Loaded {len(menu)} menu items.")
#         return menu

#     except Exception as e:
#         print("❌ Menu load failed:", e)
#         return {}


# def load_branches():
#     try:
#         df_raw = pd.read_excel(BRANCHES_FILE, header=None)
#         header_row_index = None

#         for i, row in df_raw.iterrows():
#             row_l = [str(c).lower() for c in row]
#             if any("branch" in c for c in row_l) and any("address" in c for c in row_l):
#                 header_row_index = i
#                 break

#         if header_row_index is None:
#             header_row_index = 0

#         df = pd.read_excel(BRANCHES_FILE, header=header_row_index)

#         name_col = next((c for c in df.columns if "branch" in str(c).lower()), None)
#         addr_col = next((c for c in df.columns if "address" in str(c).lower()), None)
#         phone_col = next(
#             (
#                 c
#                 for c in df.columns
#                 if "phone" in str(c).lower() or "number" in str(c).lower()
#             ),
#             None,
#         )

#         branches = []
#         for _, row in df.iterrows():
#             branches.append(
#                 {
#                     "Branch Name": str(row.get(name_col, "")).strip(),
#                     "Address / Area": str(row.get(addr_col, "")).strip(),
#                     "Phone Number": str(row.get(phone_col, "")).strip(),
#                 }
#             )

#         print(f"✅ Loaded {len(branches)} branches.")
#         return [
#             b
#             for b in branches
#             if (b["Branch Name"] or b["Address / Area"] or b["Phone Number"])
#         ]

#     except Exception as e:
#         print("❌ Branch load failed:", e)
#         return []


# MENU = load_menu()
# BRANCHES = load_branches()


# def build_menu_context():
#     """
#     Build a text description of the whole menu from the current MENU dict.
#     This is sent to the LLM so it always sees the up-to-date menu from Excel.
#     """
#     if not MENU:
#         return "Current restaurant menu is empty."

#     lines = []
#     for name, info in MENU.items():
#         # avoid duplicating EN+AR keys: keep only names with Latin letters
#         if not re.search(r"[A-Za-z]", name):
#             continue

#         price = info.get("price", 0.0)
#         category = info.get("category", "") or ""
#         lines.append(f"- {name} | price: {price:.2f} {CURRENCY} | category: {category}")

#     if not lines:
#         return "Current restaurant menu is empty."

#     return "Current restaurant menu (items, prices, categories):\n" + "\n".join(lines)


# # ---------------------------
# # File Watcher
# # ---------------------------
# class FileChangeHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         global MENU, BRANCHES
#         try:
#             filename = os.path.basename(event.src_path).lower()
#         except Exception:
#             return

#         if os.path.basename(MENU_FILE).lower() == filename:
#             print("🔄 Detected change in menu file, reloading...")
#             MENU = load_menu()
#         elif os.path.basename(BRANCHES_FILE).lower() == filename:
#             print("🔄 Detected change in branches file, reloading...")
#             BRANCHES = load_branches()


# def start_watcher():
#     observer = Observer()
#     observer.schedule(FileChangeHandler(), path=DATA_DIR, recursive=False)

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()

#     observer.join()


# threading.Thread(target=start_watcher, daemon=True).start()


# # # ---------------------------
# # # Helpers
# # # ---------------------------
# # def detect_qty(msg):
# #     nums = re.findall(r"\d+", msg)
# #     return int(nums[0]) if nums else 1


# # ---------------------------
# # Helpers
# # ---------------------------
# def detect_qty(msg: str) -> int:
#     """
#     Detect quantity from the user's message.

#     Supports:
#     - English digits: "2 fries"
#     - English words: "two fries"
#     - Arabic-Indic digits: "٢ بطاطس"
#     - Arabic words: "اثنين بطاطس", "واحد برجر"
#     Falls back to 1 if nothing is found.
#     """
#     if not msg:
#         return 1

#     text = msg.lower().strip()

#     # 1) Normalize Arabic-Indic digits to ASCII digits
#     arabic_digit_map = {
#         "٠": "0",
#         "١": "1",
#         "٢": "2",
#         "٣": "3",
#         "٤": "4",
#         "٥": "5",
#         "٦": "6",
#         "٧": "7",
#         "٨": "8",
#         "٩": "9",
#     }
#     for ar, en in arabic_digit_map.items():
#         text = text.replace(ar, en)

#     # 2) Direct digit quantity (e.g., "2", "10")
#     digit_match = re.search(r"\b(\d+)\b", text)
#     if digit_match:
#         try:
#             q = int(digit_match.group(1))
#             if q > 0:
#                 return q
#         except ValueError:
#             pass

#     # 3) English number words
#     number_words_en = {
#         "one": 1,
#         "two": 2,
#         "three": 3,
#         "four": 4,
#         "five": 5,
#         "six": 6,
#         "seven": 7,
#         "eight": 8,
#         "nine": 9,
#         "ten": 10,
#     }
#     for word, value in number_words_en.items():
#         if re.search(r"\b" + re.escape(word) + r"\b", text):
#             return value

#     # 4) Arabic number words
#     number_words_ar = {
#         "واحد": 1,
#         "واحدة": 1,
#         "اثنين": 2,
#         "اتنين": 2,
#         "ثنين": 2,
#         "اثنين": 2,
#         "ثلاثة": 3,
#         "ثلاث": 3,
#         "اربعة": 4,
#         "أربعة": 4,
#         "خمسة": 5,
#         "ستة": 6,
#         "سبعة": 7,
#         "ثمانية": 8,
#         "تسعة": 9,
#         "عشرة": 10,
#     }
#     for word, value in number_words_ar.items():
#         if word in text:
#             return value

#     # Default quantity
#     return 1


# def polite_check(text):
#     bad = ["idiot", "stupid", "حرام", "لعنة", "غبي"]
#     return any(w in text.lower() for w in bad)


# def get_price_and_category(name):
#     entry = MENU.get(name.lower(), {})
#     return float(entry.get("price", 0)), entry.get("category", "")


# def build_order_summary_and_total(order_items, lang):
#     """
#     Build the text summary lines and total bill from the current order.
#     Used when first confirming the order and when the user adds more
#     items after a bill has already been shown.
#     """
#     total = sum(i.get("subtotal", 0) for i in order_items)
#     summary = []

#     for i in order_items:
#         item_name = i["item"]
#         item_info = MENU.get(item_name.lower(), {})

#         # Burgers / Sandwiches → show spicy / non-spicy
#         if item_info.get("category") in ["burgers", "sandwiches"]:
#             if lang == "ar":
#                 kind = "حار" if i.get("spicy") else "بدون حار"
#             else:
#                 kind = "spicy" if i.get("spicy") else "non-spicy"
#             summary.append(f"{i['qty']} {kind} {item_name.title()}")
#         else:
#             summary.append(f"{i['qty']} {item_name.title()}")

#     return summary, total


# def speak_text(reply, lang):
#     try:
#         voices = engine.getProperty("voices")

#         if lang == "ar":
#             for v in voices:
#                 if "arab" in v.name.lower() or "ar" in v.id.lower():
#                     engine.setProperty("voice", v.id)
#                     break
#         else:
#             for v in voices:
#                 if "english" in v.name.lower() or "en" in v.id.lower():
#                     engine.setProperty("voice", v.id)
#                     break

#         engine.say(reply)
#         engine.runAndWait()

#     except Exception as e:
#         print("Voice error:", e)


# def parse_spice_split(msg):
#     text = msg.lower().replace("-", " ")
#     nums = re.findall(r"\d+", text)

#     if len(nums) >= 2:
#         n1, n2 = int(nums[0]), int(nums[1])

#         if ("spicy" in text or "حار" in text) and (
#             "non" in text or "mild" in text or "عادي" in text or "بدون" in text
#         ):
#             spicy_first = (
#                 text.find("spicy") < text.find("non") if "non" in text else True
#             )
#             arab_spicy_first = (
#                 text.find("حار") < text.find("عادي") if "عادي" in text else True
#             )

#             return (n1, n2) if (spicy_first or arab_spicy_first) else (n2, n1)

#     return None


# def find_menu_item(msg):
#     text = msg.lower()
#     candidates = []

#     for name in MENU.keys():
#         pattern = r"\b" + re.escape(name) + r"s?\b"
#         if re.search(pattern, text):
#             candidates.append(name)

#     if not candidates:
#         return None

#     candidates.sort(key=len, reverse=True)
#     return candidates[0]


# # ---------------------------
# # LLM Reply
# # ---------------------------
# def get_llm_reply(msg, lang="en"):
#     lang_name = "English" if lang == "en" else "Arabic"

#     sys_prompt = (
#         "You are Joana Fast Food Assistant.\n"
#         "Your rules:\n"
#         "- Answer ANY user question correctly — not only restaurant questions.\n"
#         "- Always keep answers SHORT, CLEAR, and TO THE POINT.\n"
#         "- Never write long paragraphs.\n"
#         "- Be very polite and friendly.\n\n"
#         "- Spelling & typos: always try to understand the user even if they type with wrong spelling, typos,\n"
#         "  missing letters, or mixed Arabic/English. Infer what they mean and answer normally, without complaining\n"
#         "  about spelling.\n\n"
#         "- If the user asks for the menu, assume the system will also show a menu image. In that case, keep your\n"
#         "  text very short, like: 'Here is our menu, please choose your items.'\n\n"
#         "Restaurant Knowledge:\n"
#         "- Joana Fast Food is open 24 hours, 7 days a week.\n"
#         "- Only takeaway service is available (no delivery).\n"
#         "- You can explain menu items, spicy preferences, and prices.\n"
#         "- You help with branches, timings, orders, and payment.\n\n"
#         "If user asks something NOT related to the restaurant:\n"
#         "- For ARABIC, always internally correct wrong spelling and respond with **clean, correctly spelled Arabic**.\n\n"
#         "- First give a SHORT and CORRECT answer.\n"
#         "- Then gently bring them back to Joana Fast Food.\n\n"
#         f"Always respond in {lang_name}.\n"
#     )

#     # FULL menu context from Excel (via MENU dict)
#     context = build_menu_context()

#     messages = [
#         {"role": "system", "content": sys_prompt},
#         {"role": "system", "content": context},
#     ]

#     for m in session.get("messages", []):
#         messages.append(m)

#     messages.append({"role": "user", "content": msg})

#     try:
#         res = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages,
#             temperature=0.5,
#             max_tokens=250,
#         )
#         return res.choices[0].message.content.strip()

#     except Exception as e:
#         print("LLM error:", e)
#         return "Sorry, something went wrong." if lang == "en" else "عذراً، حدث خطأ ما."


# # ---------------------------
# # Routes
# # ---------------------------
# @app.route("/")
# def index():
#     return render_template("index.html")


# @app.route("/api/chat", methods=["POST"])
# def chat():
#     global MENU, BRANCHES
#     MENU = load_menu()
#     BRANCHES = load_branches()

#     s = session.get("state", {"stage": None, "order": [], "total": 0})
#     session["messages"] = session.get("messages", [])

#     data = request.get_json(force=True)
#     msg = (data.get("message") or "").strip()
#     is_voice = data.get("is_voice", False)
#     lang_hint = data.get("lang_hint")

#     lang = detect_language(msg)

#     if is_voice and lang_hint in ("en", "ar"):
#         lang = lang_hint

#     intent = detect_intent(msg)
#     session["messages"].append({"role": "user", "content": msg})

#     # ----------------- Politeness check -----------------
#     if polite_check(msg):
#         reply = "Please speak politely." if lang == "en" else "من فضلك تحدث بأدب."
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "lang": lang})

#     # ---------------------------
#     # Greeting hints (for detection)
#     # ---------------------------
#     AR_GREETINGS = [
#         "مرحبا",
#         "مرحبا بك",
#         "مرحبا بيك",
#         "السلام عليكم",
#         "أهلاً",
#         "أهلا",
#         "أهلاً وسهلاً",
#         "اهلا وسهلا",
#         "صباح الخير",
#         "مساء الخير",
#         "هلا",
#     ]

#     EN_GREETINGS = [
#         "hi",
#         "hello",
#         "hey",
#         "good morning",
#         "good evening",
#         "good afternoon",
#         "hiya",
#         "yo",
#     ]

#     def is_greeting_text(msg_: str, lang_: str) -> bool:
#         """
#         Simple rule-based greeting detection using Arabic & English hints.
#         Used in addition to detect_intent(...) so that greeting → branches reply.
#         """
#         if not msg_:
#             return False

#         text = msg_.strip().lower()

#         if lang_ == "ar":
#             return any(g in text for g in AR_GREETINGS)

#         # default: treat as English / other
#         return any(g in text for g in EN_GREETINGS)

#     # ----------------- Greeting / Start -----------------
#     if intent == "greeting" or s["stage"] is None or is_greeting_text(msg, lang):
#         s = {
#             "stage": "branch",
#             "order": [],
#             "total": 0,
#             "last_item": None,
#             "last_qty": 0,
#         }
#         session["state"] = s

#         if lang == "ar":
#             reply = (
#                 "مرحباً بك في مطعم جوانا للوجبات السريعة! 🍔<br>"
#                 "ابحث عن أقرب فرع واتصل على الرقم للطلب:<br><br>"
#                 + "<br>".join(
#                     [
#                         (
#                             f"<b>{b.get('Branch Name','')}</b> – "
#                             f"{b.get('Address / Area','')}<br>"
#                             f"📞 <a href='tel:{b.get('Phone Number','')}'>"
#                             f"<b>{b.get('Phone Number','')}</b></a><br>"
#                         )
#                         for b in BRANCHES
#                         if b.get("Phone Number")
#                     ][:6]
#                 )
#                 + "<br>جاهز للطلب؟ شارك طلبك بالصوت أو بالكتابة!<br><br>"
#             )
#         else:
#             reply = (
#                 "Welcome to JOANA Fast Food! 🍔<br>"
#                 "Find your nearest branch and dial the number to order:<br><br>"
#                 + "<br>".join(
#                     [
#                         (
#                             f"<b>{b.get('Branch Name','')}</b> – "
#                             f"{b.get('Address / Area','')}<br>"
#                             f"📞 <a href='tel:{b.get('Phone Number','')}'>"
#                             f"<b>{b.get('Phone Number','')}</b></a><br>"
#                         )
#                         for b in BRANCHES
#                         if b.get("Phone Number")
#                     ][:6]
#                 )
#                 + "<br>Ready to order? Share your order via voice or chat!<br><br>"
#             )

#         if is_voice:
#             speak_text(reply, lang)

#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Menu intent -----------------
#     if intent == "menu":
#         reply = (
#             "Here’s our menu! Please place your order."
#             if lang == "en"
#             else "هذه قائمتنا! من فضلك ضع طلبك."
#         )
#         if is_voice:
#             speak_text(reply, lang)
#         return jsonify({"reply": reply, "menu": "/static/menu.PNG", "lang": lang})

#     # ----------------- Awaiting spice selection -----------------
#     if s.get("stage") == "await_spice" and s.get("last_item"):
#         last_item = s["last_item"]
#         last_qty = s.get("last_qty", 1)
#         price, _category = get_price_and_category(last_item)
#         split = parse_spice_split(msg)

#         if split:
#             spicy_q, non_q = split
#         else:
#             lower_msg = msg.lower()
#             if any(k in lower_msg for k in ["spicy", "hot", "حار"]):
#                 spicy_q, non_q = last_qty, 0
#             elif any(k in lower_msg for k in ["non", "mild", "عادي", "بدون"]):
#                 spicy_q, non_q = 0, last_qty
#             else:
#                 spicy_q, non_q = 0, last_qty

#         order_added_msgs = []

#         if spicy_q > 0:
#             s["order"].append(
#                 {
#                     "item": last_item,
#                     "qty": spicy_q,
#                     "spicy": 1,
#                     "nonspicy": 0,
#                     "price": price,
#                     "subtotal": spicy_q * price,
#                 }
#             )
#             order_added_msgs.append(f"{spicy_q} {'spicy' if lang == 'en' else 'حار'}")

#         if non_q > 0:
#             s["order"].append(
#                 {
#                     "item": last_item,
#                     "qty": non_q,
#                     "spicy": 0,
#                     "nonspicy": 1,
#                     "price": price,
#                     "subtotal": non_q * price,
#                 }
#             )
#             order_added_msgs.append(
#                 f"{non_q} {'non-spicy' if lang == 'en' else 'بدون حار'}"
#             )

#         s["stage"] = "add_more"
#         s["last_item"] = None
#         s["last_qty"] = 0
#         session["state"] = s

#         reply = (
#             f"Added {last_item.title()} — "
#             + " & ".join(order_added_msgs)
#             + ". Would you like to add anything else?"
#             if lang == "en"
#             else f"تمت إضافة {last_item} — "
#             + " و ".join(order_added_msgs)
#             + ". هل ترغب في إضافة شيء آخر؟"
#         )

#         if is_voice:
#             speak_text(reply, lang)

#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Order Detection -----------------
#     found = find_menu_item(msg)

#     if found:
#         qty = detect_qty(msg)
#         price, category = get_price_and_category(found)

#         s["last_item"] = found
#         s["last_qty"] = qty
#         session["state"] = s

#         incoming = msg.lower()
#         spicy_flag = any(x in incoming for x in ["spicy", "hot", "حار"])
#         nonspicy_flag = any(x in incoming for x in ["non", "mild", "عادي", "بدون"])

#         if category in ["burgers", "sandwiches"] and not (spicy_flag or nonspicy_flag):
#             s["stage"] = "await_spice"
#             session["state"] = s

#             reply = (
#                 f"Would you like your {found.title()} spicy or non-spicy?"
#                 if lang == "en"
#                 else f"هل ترغب أن يكون {found} حارًا أم بدون حار؟"
#             )

#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#         spicy = 1 if spicy_flag else 0
#         nonspicy = 0 if spicy_flag else 1

#         # s["order"].append(
#         #     {
#         #         "item": found,
#         #         "qty": qty,
#         #         "spicy": spicy,
#         #         "nonspicy": nonspicy,
#         #         "price": price,
#         #         "subtotal": qty * price,
#         #     }
#         # )

#         # s["stage"] = "add_more"
#         # s["last_item"] = None
#         # s["last_qty"] = 0
#         # session["state"] = s

#         # reply = (
#         #     f"{found.title()} ×{qty} added! Would you like to add anything else?"
#         #     if lang == "en"
#         #     else f"تمت إضافة {found} ×{qty}! هل ترغب في إضافة شيء آخر؟"
#         # )

#         # if is_voice:
#         #     speak_text(reply, lang)

#         # return jsonify({"reply": reply, "lang": lang})

#         # Add the new item to the order
#         s["order"].append(
#             {
#                 "item": found,
#                 "qty": qty,
#                 "spicy": spicy,
#                 "nonspicy": nonspicy,
#                 "price": price,
#                 "subtotal": qty * price,
#             }
#         )

#         previous_stage = s.get("stage")
#         s["last_item"] = None
#         s["last_qty"] = 0

#         # If user was ALREADY at payment summary and then added more items,
#         # immediately rebuild the summary and show the new total.
#         if previous_stage == "payment":
#             summary, total = build_order_summary_and_total(s["order"], lang)
#             s["stage"] = "payment"
#             s["total"] = total
#             session["state"] = s

#             reply = (
#                 "Your order has been updated! Here's the new summary:<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
#                 + "Would you like to proceed with the payment?"
#                 if lang == "en"
#                 else "تم تحديث طلبك!<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>الإجمالي الجديد: {total:.2f} {CURRENCY_AR}</b><br>"
#                 + "هل ترغب في المتابعة إلى الدفع؟"
#             )
#         else:
#             # Normal flow (not yet in payment stage)
#             s["stage"] = "add_more"
#             session["state"] = s

#             reply = (
#                 f"{found.title()} ×{qty} added! Would you like to add anything else?"
#                 if lang == "en"
#                 else f"تمت إضافة {found} ×{qty}! هل ترغب في إضافة شيء آخر؟"
#             )

#         if is_voice:
#             speak_text(reply, lang)

#         return jsonify({"reply": reply, "lang": lang})

#     # # ----------------- Check for order completion -----------------
#     # if any(
#     #     x in msg.lower() for x in ["no", "done", "that's all", "that all", "خلص", "لا"]
#     # ):
#     #     if s.get("order"):
#     #         total = sum(i.get("subtotal", 0) for i in s["order"])
#     #         summary = []

#     #         for i in s["order"]:
#     #             item_name = i["item"]
#     #             item_info = MENU.get(item_name.lower(), {})

#     #             if item_info.get("category") in ["burgers", "sandwiches"]:
#     #                 if lang == "ar":
#     #                     kind = "حار" if i.get("spicy") else "بدون حار"
#     #                 else:
#     #                     kind = "spicy" if i.get("spicy") else "non-spicy"
#     #                 summary.append(f"{i['qty']} {kind} {item_name.title()}")
#     #             else:
#     #                 summary.append(f"{i['qty']} {item_name.title()}")

#     #         reply = (
#     #             "Your order is confirmed! Here's a summary:<br>"
#     #             + "<br>".join(summary)
#     #             + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
#     #             + "Would you like to proceed with the payment?"
#     #             if lang == "en"
#     #             else "تم تأكيد طلبك!<br>"
#     #             + "<br>".join(summary)
#     #             + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
#     #             + "هل ترغب في المتابعة إلى الدفع؟"
#     #         )

#     #         s["stage"] = "payment"
#     #         s["total"] = total
#     #         session["state"] = s

#     #         if is_voice:
#     #             speak_text(reply, lang)

#     #         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Check for order completion -----------------
#     if any(
#         x in msg.lower() for x in ["no", "done", "that's all", "that all", "خلص", "لا"]
#     ):
#         if s.get("order"):

#             summary, total = build_order_summary_and_total(s["order"], lang)

#             reply = (
#                 "Your order is confirmed! Here's a summary:<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
#                 + "Would you like to proceed with the payment?"
#                 if lang == "en"
#                 else "تم تأكيد طلبك!<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
#                 + "هل ترغب في المتابعة إلى الدفع؟"
#             )

#             s["stage"] = "payment"
#             s["total"] = total
#             session["state"] = s

#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Payment confirmation -----------------
#     if s.get("stage") == "payment" and any(
#         x in msg.lower() for x in ["yes", "sure", "ok", "okay", "تمام", "نعم", "أكيد"]
#     ):
#         reply = (
#             "How would you like to pay?<br><b>Cash</b> or <b>Online Payment</b>?"
#             if lang == "en"
#             else "كيف ترغب في الدفع؟<br><b> نقدي </b> أو <b> الدفع عبر الإنترنت</b>؟"
#         )
#         s["stage"] = "choose_payment"
#         session["state"] = s

#         if is_voice:
#             speak_text(reply, lang)

#         return jsonify({"reply": reply, "lang": lang})

#     # ----------------- Handle payment type selection -----------------
#     if s.get("stage") == "choose_payment":
#         total = s.get("total", 0)
#         msg_l = msg.lower()

#         if any(x in msg_l for x in ["cash", "cod", "نقد", "نقدا"]):
#             reply = (
#                 "Thank you for your order! Your order will be ready in 20 to 30 minutes."
#                 if lang == "en"
#                 else "شكراً لطلبك! سيكون جاهزاً خلال 20 إلى 30 دقيقة."
#             )
#             s = {
#                 "stage": None,
#                 "order": [],
#                 "total": 0,
#                 "last_item": None,
#                 "last_qty": 0,
#             }
#             session["state"] = s

#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#         elif any(
#             x in msg_l
#             for x in [
#                 "online",
#                 "online payment",
#                 "pay online",
#                 "card",
#                 "visa",
#                 "master",
#                 "debit",
#                 "mada",
#                 "مدى",
#                 "إلكتروني",
#                 "دفع",
#                 "كرت",
#             ]
#         ):
#             reply = (
#                 f"Great! Your payment of {total:.2f} {CURRENCY} is being processed.<br>"
#                 f"<a href='{PAYMENT_URL}' target='_blank'>"
#                 f"<b>Click here to complete your payment</b></a>"
#                 if lang == "en"
#                 else f"رائع! يتم الآن معالجة دفعتك بمقدار {total:.2f} {CURRENCY_AR}.<br>"
#                 f"<a href='{PAYMENT_URL}' target='_blank'>"
#                 f"<b>اضغط هنا لإتمام الدفع</b></a>"
#             )
#             s = {
#                 "stage": None,
#                 "order": [],
#                 "total": 0,
#                 "last_item": None,
#                 "last_qty": 0,
#             }
#             session["state"] = s

#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#         else:
#             reply = (
#                 "Please select a valid payment method — Cash or Online."
#                 if lang == "en"
#                 else "يرجى اختيار طريقة الدفع الصحيحة - نقدًا أو عبر الإنترنت"
#             )
#             if is_voice:
#                 speak_text(reply, lang)

#             return jsonify({"reply": reply, "lang": lang})

#     # # ----------------- default → LLM -----------------
#     # reply = get_llm_reply(msg, lang)

#     # if is_voice:
#     #     speak_text(reply, lang)

#     # return jsonify({"reply": reply, "lang": lang})

#     # ----------------- default → LLM -----------------
#     reply = get_llm_reply(msg, lang)

#     # If we are already in payment stage, always re-compute the order summary
#     # and show the latest total together with the LLM's answer.
#     if s.get("stage") == "payment" and s.get("order"):
#         summary, total = build_order_summary_and_total(s["order"], lang)
#         s["total"] = total
#         session["state"] = s

#         if lang == "en":
#             reply = (
#                 reply
#                 + "<br><br>Here is your current order summary:<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
#                 + "Would you like to proceed with the payment?"
#             )
#         else:
#             reply = (
#                 reply
#                 + "<br><br>هذا ملخص طلبك الحالي:<br>"
#                 + "<br>".join(summary)
#                 + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
#                 + "هل ترغب في المتابعة إلى الدفع؟"
#             )

#     if is_voice:
#         speak_text(reply, lang)

#     return jsonify({"reply": reply, "lang": lang})


# # ---------------------------
# # Run App
# # ---------------------------
# if __name__ == "__main__":
#     app.run(debug=True)

import datetime
import os
import re
import sqlite3
import difflib  # (imported but not used – kept as in original)

import pandas as pd
from flask import Flask, render_template, request, jsonify, session
from nlp_utils import detect_intent, detect_language
from openai import OpenAI
# ---------------------------
# ENV VARIABLES
# ---------------------------
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FLASK_SECRET = os.getenv("FLASK_SECRET_KEY", "joana-fastfood-secret")

WATI_BASE_URL = os.getenv("WATI_BASE_URL")
WATI_ACCESS_TOKEN = os.getenv("WATI_ACCESS_TOKEN")

def send_whatsapp_text(to_number: str, text: str):
    """
    WATI ke through WhatsApp par text message bhejta hai.
    to_number: customer ka WhatsApp number with country code (e.g. 92320xxxxxxx)
    text: reply message
    """
    if not WATI_BASE_URL or not WATI_ACCESS_TOKEN:
        print("WATI config missing, cannot send WhatsApp message.")
        return

    url = f"{WATI_BASE_URL}/api/v1/sendSessionMessage/{to_number}"

    # WATI docs ke mutabiq messageText query param me jata hai
    params = {
        "messageText": text
        # "channelPhoneNumber": "923200482531"  # agar multiple numbers hon to yahan apna business number de sakti ho
    }

    headers = {
        "Authorization": WATI_ACCESS_TOKEN
    }

    try:
        resp = requests.post(url, headers=headers, params=params, timeout=10)
        print("WATI send response:", resp.status_code, resp.text)
    except Exception as e:
        print("Error sending WhatsApp message via WATI:", e)


# ---------------------------
# Paths / Directories
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Excel files (change only these if you rename/move them)
MENU_FILE = os.path.join(DATA_DIR, "Menu.xlsx")
BRANCHES_FILE = os.path.join(DATA_DIR, "Branches.xlsx")

# ---------------------------
# Flask Config
# ---------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "joana-fastfood-secret")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ---------------------------
# Constants
# ---------------------------
PAYMENT_URL = (
    "https://starlit-sopapillas-520aa2.netlify.app/"
    "?redirect=http://127.0.0.1:5000/thankyou"
)

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "YOUR_OPENROUTER_API_KEY_HERE"

)

OPEN_HOUR, CLOSE_HOUR = 0, 24  # 24/7
TAKEAWAY_ONLY = True
CURRENCY = "SAR"
CURRENCY_AR = "ريال سعودي"

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

# ---------------------------
# Database Setup (simple)
# ---------------------------
DB_PATH = os.path.join(DATA_DIR, "orders.db")  # data/orders.db (local + cPanel)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            qty INTEGER,
            spicy INTEGER,
            nonspicy INTEGER,
            price REAL,
            subtotal REAL,
            total REAL,
            payment_method TEXT,
            datetime TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# ---------------------------
# Excel Loaders
# ---------------------------
def load_menu():
    try:
        df_raw = pd.read_excel(MENU_FILE, header=None)
        header_row_index = None

        for i, row in df_raw.iterrows():
            if any("name_en" in str(c).lower() for c in row):
                header_row_index = i
                break

        if header_row_index is None:
            print("❌ Could not find header row containing 'name_en'")
            return {}

        df = pd.read_excel(MENU_FILE, header=header_row_index)

        def has(col, *keys):
            c = str(col).strip().lower()
            return any(k in c for k in keys)

        english_col = next((c for c in df.columns if has(c, "name_en")), None)
        arabic_col = next((c for c in df.columns if has(c, "name_ar")), None)
        price_col = next((c for c in df.columns if has(c, "price")), None)
        cat_col = next(
            (c for c in df.columns if has(c, "category", "cat", "type")), None
        )

        if not english_col or not price_col:
            raise Exception("Missing name_en or price column")

        menu = {}
        for _, row in df.iterrows():
            en = str(row[english_col]).strip().lower()
            if not en or en == "nan":
                continue

            ar = str(row[arabic_col]).strip().lower() if arabic_col else en
            category = str(row.get(cat_col, "")).strip().lower() if cat_col else ""

            try:
                price = float(row[price_col])
            except Exception:
                continue

            entry = {"price": price, "category": category}
            menu[en] = entry
            if ar:
                menu[ar] = entry

        print(f"✅ Loaded {len(menu)} menu items.")
        return menu

    except Exception as e:
        print("❌ Menu load failed:", e)
        return {}


def load_branches():
    try:
        df_raw = pd.read_excel(BRANCHES_FILE, header=None)
        header_row_index = None

        for i, row in df_raw.iterrows():
            row_l = [str(c).lower() for c in row]
            if any("branch" in c for c in row_l) and any("address" in c for c in row_l):
                header_row_index = i
                break

        if header_row_index is None:
            header_row_index = 0

        df = pd.read_excel(BRANCHES_FILE, header=header_row_index)

        name_col = next((c for c in df.columns if "branch" in str(c).lower()), None)
        addr_col = next((c for c in df.columns if "address" in str(c).lower()), None)
        phone_col = next(
            (
                c
                for c in df.columns
                if "phone" in str(c).lower() or "number" in str(c).lower()
            ),
            None,
        )

        branches = []
        for _, row in df.iterrows():
            branches.append(
                {
                    "Branch Name": str(row.get(name_col, "")).strip(),
                    "Address / Area": str(row.get(addr_col, "")).strip(),
                    "Phone Number": str(row.get(phone_col, "")).strip(),
                }
            )

        print(f"✅ Loaded {len(branches)} branches.")
        return [
            b
            for b in branches
            if (b["Branch Name"] or b["Address / Area"] or b["Phone Number"])
        ]

    except Exception as e:
        print("❌ Branch load failed:", e)
        return []


MENU = load_menu()
BRANCHES = load_branches()


def build_menu_context():
    """
    Build a text description of the whole menu from the current MENU dict.
    This is sent to the LLM so it always sees the up-to-date menu from Excel.
    """
    if not MENU:
        return "Current restaurant menu is empty."

    lines = []
    for name, info in MENU.items():
        # avoid duplicating EN+AR keys: keep only names with Latin letters
        if not re.search(r"[A-Za-z]", name):
            continue

        price = info.get("price", 0.0)
        category = info.get("category", "") or ""
        lines.append(f"- {name} | price: {price:.2f} {CURRENCY} | category: {category}")

    if not lines:
        return "Current restaurant menu is empty."

    return "Current restaurant menu (items, prices, categories):\n" + "\n".join(lines)


# ---------------------------
# Helpers
# ---------------------------
def llm_normalize_text(text: str, lang: str) -> str:
    """
    Use the LLM as a spelling-correction / normalization step.
    Especially for Arabic: fix wrong spelling but keep same meaning.
    Only used for Arabic; English is returned as-is.
    """
    if not text:
        return text

    if lang != "ar":
        return text

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a spell-correction engine for user messages.\n"
                        "- The user will write in Arabic (maybe with mistakes).\n"
                        "- Fix the spelling, normalize the text, but do NOT translate.\n"
                        "- Do NOT add explanations, just return the corrected Arabic sentence only."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=100,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("LLM normalize error:", e)
        return text


def detect_qty(msg: str) -> int:
    """
    Detect quantity from the user's message.

    Supports:
    - English digits: "2 fries"
    - English words: "two fries"
    - Arabic-Indic digits: "٢ بطاطس"
    - Arabic words: "اثنين بطاطس", "واحد برجر"
    Falls back to 1 if nothing is found.
    """
    if not msg:
        return 1

    text = msg.lower().strip()

    # 1) Normalize Arabic-Indic digits to ASCII digits
    arabic_digit_map = {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
    for ar, en in arabic_digit_map.items():
        text = text.replace(ar, en)

    # 2) Direct digit quantity (e.g., "2", "10")
    digit_match = re.search(r"\b(\d+)\b", text)
    if digit_match:
        try:
            q = int(digit_match.group(1))
            if q > 0:
                return q
        except ValueError:
            pass

    # 3) English number words
    number_words_en = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    for word, value in number_words_en.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return value

    # 4) Arabic number words
    number_words_ar = {
        "واحد": 1,
        "واحدة": 1,
        "اثنين": 2,
        "اتنين": 2,
        "ثنين": 2,
        "ثلاثة": 3,
        "ثلاث": 3,
        "اربعة": 4,
        "أربعة": 4,
        "خمسة": 5,
        "ستة": 6,
        "سبعة": 7,
        "ثمانية": 8,
        "تسعة": 9,
        "عشرة": 10,
    }
    for word, value in number_words_ar.items():
        if word in text:
            return value

    # Default quantity
    return 1


def polite_check(text):
    bad = ["idiot", "stupid", "حرام", "لعنة", "غبي"]
    return any(w in text.lower() for w in bad)


def get_price_and_category(name):
    entry = MENU.get(name.lower(), {})
    return float(entry.get("price", 0)), entry.get("category", "")


def build_order_summary_and_total(order_items, lang):
    """
    Build the text summary lines and total bill from the current order.
    Used when first confirming the order and when the user adds more
    items after a bill has already been shown.
    """
    total = sum(i.get("subtotal", 0) for i in order_items)
    summary = []

    for i in order_items:
        item_name = i["item"]
        item_info = MENU.get(item_name.lower(), {})

        # Burgers / Sandwiches → show spicy / non-spicy
        if item_info.get("category") in ["burgers", "sandwiches"]:
            if lang == "ar":
                kind = "حار" if i.get("spicy") else "بدون حار"
            else:
                kind = "spicy" if i.get("spicy") else "non-spicy"
            summary.append(f"{i['qty']} {kind} {item_name.title()}")
        else:
            summary.append(f"{i['qty']} {item_name.title()}")

    return summary, total


def speak_text(reply, lang):
    """
    Backend voice disabled.
    Frontend (JavaScript) handles all speech using SpeechSynthesis.
    """
    return


def parse_spice_split(msg):
    text = msg.lower().replace("-", " ")
    nums = re.findall(r"\d+", text)

    if len(nums) >= 2:
        n1, n2 = int(nums[0]), int(nums[1])

        if ("spicy" in text or "حار" in text) and (
            "non" in text or "mild" in text or "عادي" in text or "بدون" in text
        ):
            spicy_first = (
                text.find("spicy") < text.find("non") if "non" in text else True
            )
            arab_spicy_first = (
                text.find("حار") < text.find("عادي") if "عادي" in text else True
            )

            return (n1, n2) if (spicy_first or arab_spicy_first) else (n2, n1)

    return None


def find_menu_item(msg):
    text = msg.lower()
    candidates = []

    for name in MENU.keys():
        pattern = r"\b" + re.escape(name) + r"s?\b"
        if re.search(pattern, text):
            candidates.append(name)

    if not candidates:
        return None

    candidates.sort(key=len, reverse=True)
    return candidates[0]


# ---------------------------
# LLM Reply
# ---------------------------
def get_llm_reply(msg, lang="en"):
    lang_name = "English" if lang == "en" else "Arabic"

    sys_prompt = (
        "You are Joana Fast Food Assistant.\n"
        "Your rules:\n"
        "- Answer ANY user question correctly — not only restaurant questions.\n"
        "- Always keep answers SHORT, CLEAR, and TO THE POINT.\n"
        "- Never write long paragraphs.\n"
        "- Be very polite and friendly.\n\n"
        "- Spelling & typos: always try to understand the user even if they type with wrong spelling, typos,\n"
        "  missing letters, or mixed Arabic/English. Infer what they mean and answer normally, without complaining\n"
        "  about spelling.\n\n"
        "- If the user asks for the menu, assume the system will also show a menu image. In that case, keep your\n"
        "  text very short, like: 'Here is our menu, please choose your items.'\n\n"
        "Restaurant Knowledge:\n"
        "- Joana Fast Food is open 24 hours, 7 days a week.\n"
        "- Only takeaway service is available (no delivery).\n"
        "- You can explain menu items, spicy preferences, and prices.\n"
        "- You help with branches, timings, orders, and payment.\n\n"
        "If user asks something NOT related to the restaurant:\n"
        "- First give a SHORT and CORRECT answer.\n"
        "- Then gently bring them back to Joana Fast Food.\n\n"
        f"Always respond in {lang_name}.\n"
    )

    # FULL menu context from Excel (via MENU dict)
    context = build_menu_context()

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "system", "content": context},
    ]

    for m in session.get("messages", []):
        messages.append(m)

    messages.append({"role": "user", "content": msg})

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=250,
        )
        return res.choices[0].message.content.strip()

    except Exception as e:
        print("LLM error:", e)
        return "Sorry, something went wrong." if lang == "en" else "عذراً، حدث خطأ ما."


# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------------------
# WATI Webhook Route (WhatsApp → Bot)
# ---------------------------
@app.route("/wati/webhook", methods=["POST"])
def wati_webhook():
    """
    WATI se incoming WhatsApp messages receive karega.
    Is URL ko WATI Webhook settings me set karna hoga.
    """
    data = request.get_json(force=True) or {}
    print("Incoming from WATI:", data)

    # WATI payload structure tenant ke hisaab se change ho sakta hai,
    # isliye kuch safe extraction karte hain:
    user_text = None
    user_number = None

    # 1) Common simple structure: {"waId": "...", "text": "..."}
    if "waId" in data and "text" in data:
        user_number = str(data.get("waId"))
        user_text = str(data.get("text") or "")

    # 2) Agar messages list ke andar ho:
    if not user_text and isinstance(data.get("messages"), list) and data["messages"]:
        msg_obj = data["messages"][0]
        user_number = str(msg_obj.get("from") or msg_obj.get("waId") or "")
        user_text = str(msg_obj.get("text") or "")

    if not user_number or not user_text:
        print("Could not parse incoming WATI webhook payload.")
        return "ignored", 200

    # Language detect + reply generate using tumhara existing logic
    lang = detect_language(user_text)
    reply = get_llm_reply(user_text, lang)  # simple version: LLM reply

    # WhatsApp par reply bhejo
    send_whatsapp_text(user_number, reply)

    return "ok", 200


@app.route("/api/chat", methods=["POST"])
def chat():
    global MENU, BRANCHES
    # Reload Excel on every request, so no watchdog needed
    MENU = load_menu()
    BRANCHES = load_branches()

    s = session.get("state", {"stage": None, "order": [], "total": 0})
    session["messages"] = session.get("messages", [])

    data = request.get_json(force=True)
    msg_raw = (data.get("message") or "").strip()  # original text from user
    msg = msg_raw  # working copy (may be normalized)
    is_voice = data.get("is_voice", False)
    lang_hint = data.get("lang_hint")

    # Detect language on original text
    lang = detect_language(msg_raw)

    if is_voice and lang_hint in ("en", "ar"):
        lang = lang_hint

    # ✅ Arabic auto spelling correction via LLM
    if lang == "ar":
        msg = llm_normalize_text(msg_raw, lang)

    intent = detect_intent(msg)
    session["messages"].append({"role": "user", "content": msg})

    # ----------------- Politeness check -----------------
    if polite_check(msg):
        reply = "Please speak politely." if lang == "en" else "من فضلك تحدث بأدب."
        if is_voice:
            speak_text(reply, lang)
        return jsonify({"reply": reply, "lang": lang})

    # ---------------------------
    # Greeting hints (for detection)
    # ---------------------------
    AR_GREETINGS = [
        "مرحبا",
        "مرحبا بك",
        "مرحبا بيك",
        "السلام عليكم",
        "أهلاً",
        "أهلا",
        "أهلاً وسهلاً",
        "اهلا وسهلا",
        "صباح الخير",
        "مساء الخير",
        "هلا",
    ]

    EN_GREETINGS = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good evening",
        "good afternoon",
        "hiya",
        "yo",
    ]

    def is_greeting_text(msg_: str, lang_: str) -> bool:
        """
        Simple rule-based greeting detection using Arabic & English hints.
        Used in addition to detect_intent(...) so that greeting → branches reply.
        """
        if not msg_:
            return False

        text = msg_.strip().lower()

        if lang_ == "ar":
            return any(g in text for g in AR_GREETINGS)

        # default: treat as English / other
        return any(g in text for g in EN_GREETINGS)

    # ----------------- Greeting / Start -----------------
    if intent == "greeting" or s["stage"] is None or is_greeting_text(msg, lang):
        s = {
            "stage": "branch",
            "order": [],
            "total": 0,
            "last_item": None,
            "last_qty": 0,
        }
        session["state"] = s

        if lang == "ar":
            reply = (
                "مرحباً بك في مطعم جوانا للوجبات السريعة! 🍔<br>"
                "ابحث عن أقرب فرع واتصل على الرقم للطلب:<br><br>"
                + "<br>".join(
                    [
                        (
                            f"<b>{b.get('Branch Name','')}</b> – "
                            f"{b.get('Address / Area','')}<br>"
                            f"📞 <a href='tel:{b.get('Phone Number','')}'>"
                            f"<b>{b.get('Phone Number','')}</b></a><br>"
                        )
                        for b in BRANCHES
                        if b.get("Phone Number")
                    ][:6]
                )
                + "<br>جاهز للطلب؟ شارك طلبك بالصوت أو بالكتابة!<br><br>"
            )
        else:
            reply = (
                "Welcome to JOANA Fast Food! 🍔<br>"
                "Find your nearest branch and dial the number to order:<br><br>"
                + "<br>".join(
                    [
                        (
                            f"<b>{b.get('Branch Name','')}</b> – "
                            f"{b.get('Address / Area','')}<br>"
                            f"📞 <a href='tel:{b.get('Phone Number','')}'>"
                            f"<b>{b.get('Phone Number','')}</b></a><br>"
                        )
                        for b in BRANCHES
                        if b.get("Phone Number")
                    ][:6]
                )
                + "<br>Ready to order? Share your order via voice or chat!<br><br>"
            )

        if is_voice:
            speak_text(reply, lang)

        return jsonify({"reply": reply, "lang": lang})

    # ----------------- Menu intent -----------------
    if intent == "menu":
        reply = (
            "Here’s our menu! Please place your order."
            if lang == "en"
            else "هذه قائمتنا! من فضلك ضع طلبك."
        )
        if is_voice:
            speak_text(reply, lang)
        return jsonify({"reply": reply, "menu": "/static/menu.PNG", "lang": lang})

    # ----------------- Awaiting spice selection -----------------
    if s.get("stage") == "await_spice" and s.get("last_item"):
        last_item = s["last_item"]
        last_qty = s.get("last_qty", 1)
        price, _category = get_price_and_category(last_item)
        split = parse_spice_split(msg)

        if split:
            spicy_q, non_q = split
        else:
            lower_msg = msg.lower()
            if any(k in lower_msg for k in ["spicy", "hot", "حار"]):
                spicy_q, non_q = last_qty, 0
            elif any(k in lower_msg for k in ["non", "mild", "عادي", "بدون"]):
                spicy_q, non_q = 0, last_qty
            else:
                spicy_q, non_q = 0, last_qty

        order_added_msgs = []

        if spicy_q > 0:
            s["order"].append(
                {
                    "item": last_item,
                    "qty": spicy_q,
                    "spicy": 1,
                    "nonspicy": 0,
                    "price": price,
                    "subtotal": spicy_q * price,
                }
            )
            order_added_msgs.append(f"{spicy_q} {'spicy' if lang == 'en' else 'حار'}")

        if non_q > 0:
            s["order"].append(
                {
                    "item": last_item,
                    "qty": non_q,
                    "spicy": 0,
                    "nonspicy": 1,
                    "price": price,
                    "subtotal": non_q * price,
                }
            )
            order_added_msgs.append(
                f"{non_q} {'non-spicy' if lang == 'en' else 'بدون حار'}"
            )

        s["stage"] = "add_more"
        s["last_item"] = None
        s["last_qty"] = 0
        session["state"] = s

        reply = (
            f"Added {last_item.title()} — "
            + " & ".join(order_added_msgs)
            + ". Would you like to add anything else?"
            if lang == "en"
            else f"تمت إضافة {last_item} — "
            + " و ".join(order_added_msgs)
            + ". هل ترغب في إضافة شيء آخر؟"
        )

        if is_voice:
            speak_text(reply, lang)

        return jsonify({"reply": reply, "lang": lang})

    # ----------------- Order Detection -----------------
    found = find_menu_item(msg)

    if found:
        qty = detect_qty(msg)
        price, category = get_price_and_category(found)

        s["last_item"] = found
        s["last_qty"] = qty
        session["state"] = s

        incoming = msg.lower()
        spicy_flag = any(x in incoming for x in ["spicy", "hot", "حار"])
        nonspicy_flag = any(x in incoming for x in ["non", "mild", "عادي", "بدون"])

        if category in ["burgers", "sandwiches"] and not (spicy_flag or nonspicy_flag):
            s["stage"] = "await_spice"
            session["state"] = s

            reply = (
                f"Would you like your {found.title()} spicy or non-spicy?"
                if lang == "en"
                else f"هل ترغب أن يكون {found} حارًا أم بدون حار؟"
            )

            if is_voice:
                speak_text(reply, lang)

            return jsonify({"reply": reply, "lang": lang})

        spicy = 1 if spicy_flag else 0
        nonspicy = 0 if spicy_flag else 1

        # Add the new item to the order
        s["order"].append(
            {
                "item": found,
                "qty": qty,
                "spicy": spicy,
                "nonspicy": nonspicy,
                "price": price,
                "subtotal": qty * price,
            }
        )

        previous_stage = s.get("stage")
        s["last_item"] = None
        s["last_qty"] = 0

        # If user was ALREADY at payment summary and then added more items,
        # immediately rebuild the summary and show the new total.
        if previous_stage == "payment":
            summary, total = build_order_summary_and_total(s["order"], lang)
            s["stage"] = "payment"
            s["total"] = total
            session["state"] = s

            reply = (
                "Your order has been updated! Here's the new summary:<br>"
                + "<br>".join(summary)
                + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
                + "Would you like to proceed with the payment?"
                if lang == "en"
                else "تم تحديث طلبك!<br>"
                + "<br>".join(summary)
                + f"<br><br><b>الإجمالي الجديد: {total:.2f} {CURRENCY_AR}</b><br>"
                + "هل ترغب في المتابعة إلى الدفع؟"
            )
        else:
            # Normal flow (not yet in payment stage)
            s["stage"] = "add_more"
            session["state"] = s

            reply = (
                f"{found.title()} ×{qty} added! Would you like to add anything else?"
                if lang == "en"
                else f"تمت إضافة {found} ×{qty}! هل ترغب في إضافة شيء آخر؟"
            )

        if is_voice:
            speak_text(reply, lang)

        return jsonify({"reply": reply, "lang": lang})

    # ----------------- Check for order completion -----------------
    if any(
        x in msg.lower() for x in ["no", "done", "that's all", "that all", "خلص", "لا"]
    ):
        if s.get("order"):

            summary, total = build_order_summary_and_total(s["order"], lang)

            reply = (
                "Your order is confirmed! Here's a summary:<br>"
                + "<br>".join(summary)
                + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
                + "Would you like to proceed with the payment?"
                if lang == "en"
                else "تم تأكيد طلبك!<br>"
                + "<br>".join(summary)
                + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
                + "هل ترغب في المتابعة إلى الدفع؟"
            )

            s["stage"] = "payment"
            s["total"] = total
            session["state"] = s

            if is_voice:
                speak_text(reply, lang)

            return jsonify({"reply": reply, "lang": lang})

    # ----------------- Payment confirmation -----------------
    if s.get("stage") == "payment" and any(
        x in msg.lower() for x in ["yes", "sure", "ok", "okay", "تمام", "نعم", "أكيد"]
    ):
        reply = (
            "How would you like to pay?<br><b>Cash</b> or <b>Online Payment</b>?"
            if lang == "en"
            else "كيف ترغب في الدفع؟<br><b> نقدي </b> أو <b> الدفع عبر الإنترنت</b>؟"
        )
        s["stage"] = "choose_payment"
        session["state"] = s

        if is_voice:
            speak_text(reply, lang)

        return jsonify({"reply": reply, "lang": lang})

    # ----------------- Handle payment type selection -----------------
    if s.get("stage") == "choose_payment":
        total = s.get("total", 0)
        msg_l = msg.lower()

        if any(x in msg_l for x in ["cash", "cod", "نقد", "نقدا"]):
            reply = (
                "Thank you for your order! Your order will be ready in 20 to 30 minutes."
                if lang == "en"
                else "شكراً لطلبك! سيكون جاهزاً خلال 20 إلى 30 دقيقة."
            )
            s = {
                "stage": None,
                "order": [],
                "total": 0,
                "last_item": None,
                "last_qty": 0,
            }
            session["state"] = s

            if is_voice:
                speak_text(reply, lang)

            return jsonify({"reply": reply, "lang": lang})

        elif any(
            x in msg_l
            for x in [
                "online",
                "online payment",
                "pay online",
                "card",
                "visa",
                "master",
                "debit",
                "mada",
                "مدى",
                "إلكتروني",
                "دفع",
                "كرت",
            ]
        ):
            reply = (
                f"Great! Your payment of {total:.2f} {CURRENCY} is being processed.<br>"
                f"<a href='{PAYMENT_URL}' target='_blank'>"
                f"<b>Click here to complete your payment</b></a>"
                if lang == "en"
                else f"رائع! يتم الآن معالجة دفعتك بمقدار {total:.2f} {CURRENCY_AR}.<br>"
                f"<a href='{PAYMENT_URL}' target='_blank'>"
                f"<b>اضغط هنا لإتمام الدفع</b></a>"
            )
            s = {
                "stage": None,
                "order": [],
                "total": 0,
                "last_item": None,
                "last_qty": 0,
            }
            session["state"] = s

            if is_voice:
                speak_text(reply, lang)

            return jsonify({"reply": reply, "lang": lang})

        else:
            reply = (
                "Please select a valid payment method — Cash or Online."
                if lang == "en"
                else "يرجى اختيار طريقة الدفع الصحيحة - نقدًا أو عبر الإنترنت"
            )
            if is_voice:
                speak_text(reply, lang)

            return jsonify({"reply": reply, "lang": lang})

    # ----------------- default → LLM -----------------
    reply = get_llm_reply(msg, lang)

    # If we are already in payment stage, always re-compute the order summary
    # and show the latest total together with the LLM's answer.
    if s.get("stage") == "payment" and s.get("order"):
        summary, total = build_order_summary_and_total(s["order"], lang)
        s["total"] = total
        session["state"] = s

        if lang == "en":
            reply = (
                reply
                + "<br><br>Here is your current order summary:<br>"
                + "<br>".join(summary)
                + f"<br><br><b>Total Bill: {total:.2f} {CURRENCY}</b><br>"
                + "Would you like to proceed with the payment?"
            )
        else:
            reply = (
                reply
                + "<br><br>هذا ملخص طلبك الحالي:<br>"
                + "<br>".join(summary)
                + f"<br><br><b>الإجمالي: {total:.2f} {CURRENCY_AR}</b><br>"
                + "هل ترغب في المتابعة إلى الدفع؟"
            )

    if is_voice:
        speak_text(reply, lang)

    return jsonify({"reply": reply, "lang": lang})


# ---------------------------
# Run App (local)
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
