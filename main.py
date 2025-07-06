from flask import Flask, render_template, request
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
import requests
import os
import re

load_dotenv()
app = Flask(__name__)

# API Keys
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# Work hours & holiday setup
WORK_START = time(10, 30)  # 10:30 AM IST
WORK_END = time(19, 30)    # 7:30 PM IST
WORK_DAYS = {0, 1, 2, 3, 4}  # Monday to Friday

HOLIDAYS_2025 = {
    "2025-01-01": "New Year",
    "2025-01-14": "Makara Sankranti",
    "2025-03-31": "Qutub-e-Ramzan",
    "2025-05-01": "May Day",
    "2025-08-15": "Independence Day",
    "2025-08-27": "Ganesh Chaturthi",
    "2025-10-01": "Ayudha Puja / Mahanavami",
    "2025-10-02": "Gandhi Jayanthi",
    "2025-10-22": "Balipadyami/Deepawali",
    "2025-12-25": "Christmas"
}

OPTIONAL_HOLIDAYS = {
    "2025-02-26": "Maha Shivratri",
    "2025-03-13": "Holi Feast",
    "2025-04-10": "Mahaveer Jayanti",
    "2025-04-18": "Good Friday",
    "2025-09-05": "Id-Meelad / Tiru Onam"
}

# Offer handler
def get_offers_from_mistral(query):
    card_list = """Debit Cards:
- Canara Rupay Select Debit Card
- Jana Small Finance Rupay Select Debit Card
- Fi Bank Visa Debit Card
- Tide Prepaid Rupay
- Indusind Delights Debit Card
- SBM Niyo Visa Debit Card
- HDFC Millennia Debit Card
- BOB Rupay Select Debit Card

Prepaid Cards:
- Tide Rupay Card

Credit Cards:
- IDFC First Power Plus Credit Card
- Axis Bank Airtel Credit
- Axis Bank Neo Credit
- Canara Bank Rupay Select Credit Card
- Easydiner Indusind Bank Platinum Credit Card
- Tata Neu Infinity Rupay Select
- CSB Jupiter Rupay Card
- RBL Book My Show Credit Card
- HDFC Swiggy Credit Card
- IDFC First Select Credit Card
- Amazon Pay ICICI Credit Card
- HSBC Visa Platinum Credit Card
- SBI Cashback Credit Card
- PNB Rupay Select Credit Card
- IDFC WOW Credit Card"""

    prompt = f"""
You are a helpful assistant. Only consider the following user's card list:

{card_list}

Now, based on these cards, list current or typical offers relevant to the query: '{query}' — such as cashback, rewards, vouchers, discounts, etc., available in India. Do not include cards not listed above.
"""

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        response = requests.post(MISTRAL_API_URL, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error from Mistral: {str(e)}"

# DuckDuckGo and Google (SerpAPI) web fallback
def get_general_answer(query):
    fallback_link = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    try:
        serp_params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "hl": "en"
        }
        resp = requests.get("https://serpapi.com/search", params=serp_params)
        data = resp.json()

        if "answer_box" in data:
            abox = data["answer_box"]
            if "answer" in abox:
                return abox["answer"] + f"\n\n🔗 [Source]({fallback_link})"
            if "snippet" in abox:
                link = abox.get("link", fallback_link)
                snippet = abox["snippet"]
                return f"{snippet}\n\n🔗 [Read more]({link})"

        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            desc = kg.get("description", "")
            title = kg.get("title", "")
            link = kg.get("link", fallback_link)
            if desc:
                return f"**{title}**\n\n{desc}\n\n🔗 [Read more]({link})"

        if "organic_results" in data and data["organic_results"]:
            org = data["organic_results"][0]
            snippet = org.get("snippet", "")
            link = org.get("link", fallback_link)
            return f"{snippet}\n\n🔗 [Read more]({link})"

    except Exception as e:
        print("SerpAPI failed:", str(e))

    try:
        duck_params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        duck = requests.get("https://api.duckduckgo.com/", params=duck_params).json()

        if duck.get("Abstract"):
            link = duck.get("AbstractURL", fallback_link)
            return f"{duck['Abstract']}\n\n🔗 [Read more]({link})"

        if duck.get("RelatedTopics"):
            topic = duck["RelatedTopics"][0]
            text = topic.get("Text", "")
            url = topic.get("FirstURL", fallback_link)
            return f"{text}\n\n🔗 [Read more]({url})"

        return f"Couldn't find a complete answer.\n\n🔗 [Search yourself]({fallback_link})"

    except Exception as e:
        return f"Backup lookup failed: {str(e)}"

# Roy-specific answers
def get_roy_custom_answer(query):
    lower = query.lower()

    HOLIDAY_SYNONYMS = ["holiday", "leave", "off", "shutdown", "vacation"]

    if any(word in lower for word in HOLIDAY_SYNONYMS):
        if "next" in lower:
            return get_next_holiday()
        elif "last" in lower or "previous" in lower:
            return get_previous_holiday()
        elif "this week" in lower:
            return get_this_week_holidays()

    if any(x in lower for x in ["who are you", "your name", "who is roy", "who is pabitra roy", "who is mr. roy"]):
        return (
            "**Pabitra Roy** is an Information Security Engineer at Hy-Vee. "
            "He works on IAM and Security Engineering. "
            "He holds a Master’s Degree in Cybersecurity and is CompTIA and Okta Certified."
        )

    if "who are you" in lower or "your name" in lower:
        return "I am Roy, your assistant."

    elif "full name" in lower or "complete name" in lower:
        return "Pabitra Roy"

    elif "email" in lower:
        return "📧 Pab@h.com"

    elif "company" in lower:
        return "Hy-Vee"

    elif "team" in lower:
        return "IT Security"

    elif "manager" in lower:
        return "Person"

    elif "phone" in lower or "address" in lower or "partner" in lower:
        return "I cannot answer personal questions. Please email him at Pab@h.com"

    elif "working hours" in lower or "work time" in lower:
        return "Roy works Monday to Friday, from 10:30 AM to 7:30 PM IST."

    elif "calendar holidays" in lower or "holiday list" in lower:
        holidays = "\n".join([f"📅 {date} - {name}" for date, name in HOLIDAYS_2025.items()])
        return f"Here are Roy's 2025 holidays:\n\n{holidays}"

    elif "next holiday" in lower or "upcoming holiday" in lower:
        return get_next_holiday()

    elif "previous holiday" in lower or "last holiday" in lower:
        return get_previous_holiday()

    elif "this week holiday" in lower:
        return get_this_week_holidays()

    elif "is roy working" in lower or "working today" in lower or "is he available" in lower:
        status = check_roy_status()
        if "✅" in status:
            return status + "\nRoy is available on Microsoft Teams 💬"
        elif "🎉" in status:
            return status + "\nHe might not respond today 🎈"
        elif "🛌" in status:
            return status + "\nTry reaching him on the next working day!"
        elif "⏰" in status:
            return status + "\nTry again during working hours."
        else:
            return status

    elif "where is roy" in lower:
        return check_roy_status()

    return None

# Roy availability logic
def get_current_roy_status_message():
    now = datetime.now() + timedelta(hours=5, minutes=30)  # Convert to IST
    today = now.date()
    today_str = today.isoformat()

    if today_str in HOLIDAYS_2025:
        return f"🎉 Roy is on leave today for {HOLIDAYS_2025[today_str]}"
    if now.weekday() not in WORK_DAYS:
        return "🛌 Roy is away — it's a weekend"
    if time(13, 0) <= now.time() <= time(14, 0):
        return "🍱 Roy is on lunch break (1PM to 2PM IST)"
    if WORK_START <= now.time() <= WORK_END:
        return "🟢 Roy is currently available on Teams"
    return "⏰ Roy is currently outside working hours"



# App entry
@app.route("/", methods=["GET", "POST"])
def index():
    offers = None
    query = ""
    source = None

    # Always calculate Roy's availability
    status_message = get_current_roy_status_message()

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            custom = get_roy_custom_answer(query)
            if custom:
                offers = custom
                source = "roy"
            elif any(x in query.lower() for x in ["from my list", "from my cards", "with my cards", "from my debit", "from my credit"]):
                offers = get_offers_from_mistral(query)
                source = "roy"
            else:
                offers = get_general_answer(query)
                source = "web"

    return render_template("index.html", offers=offers, query=query, source=source, status_message=status_message)

def get_next_holiday():
    today = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()
    upcoming = sorted((datetime.strptime(date, "%Y-%m-%d").date(), name)
                      for date, name in HOLIDAYS_2025.items()
                      if datetime.strptime(date, "%Y-%m-%d").date() > today)
    if upcoming:
        next_date, name = upcoming[0]
        return f"📅 Next holiday is on {next_date.strftime('%A, %d %B %Y')} for *{name}* 🎉"
    return "There are no more holidays this year!"

def get_previous_holiday():
    today = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()
    past = sorted((datetime.strptime(date, "%Y-%m-%d").date(), name)
                  for date, name in HOLIDAYS_2025.items()
                  if datetime.strptime(date, "%Y-%m-%d").date() < today)
    if past:
        prev_date, name = past[-1]
        return f"🕰️ Last holiday was on {prev_date.strftime('%A, %d %B %Y')} for *{name}*"
    return "No past holidays found yet this year."

def get_this_week_holidays():
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    start = now.date()
    end = start + timedelta(days=6 - start.weekday())  # end of week (Sunday)
    this_week = [(date, name) for date, name in HOLIDAYS_2025.items()
                 if start <= datetime.strptime(date, "%Y-%m-%d").date() <= end]
    if this_week:
        return "📅 This week's holidays:\n" + "\n".join(
            [f"{datetime.strptime(date, '%Y-%m-%d').strftime('%A, %d %b')}: {name}" for date, name in this_week])
    return "No holidays this week!"

# Debug mode
if __name__ == "__main__":
    app.run(debug=True)
