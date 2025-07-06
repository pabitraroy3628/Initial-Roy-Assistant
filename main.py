from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
WEB_API_URL = "https://api.duckduckgo.com/"  # or use serpapi or any other free web info source


def is_general_query(text):
    general_keywords = ["who", "what", "where", "when", "how", "why", "current", "latest"]
    return any(word in text.lower() for word in general_keywords)




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


def is_valid_url(url):
    return url and url.startswith("http")


def get_general_answer(query):
    SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
    fallback_link = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    # Step 1: Try SerpAPI
    try:
        serp_params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "hl": "en"
        }
        resp = requests.get("https://serpapi.com/search", params=serp_params)
        data = resp.json()

        # 1A: Direct Answer Box
        if "answer_box" in data:
            abox = data["answer_box"]
            if "answer" in abox:
                return abox["answer"] + f"\n\n🔗 [Source]({fallback_link})"
            if "snippet" in abox:
                link = abox.get("link", fallback_link)
                snippet = abox["snippet"]
                return f"{snippet}\n\n🔗 [Read more]({link})"

        # 1B: Knowledge Graph
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            desc = kg.get("description", "")
            title = kg.get("title", "")
            link = kg.get("link", fallback_link)
            if desc:
                response = f"**{title}**\n\n{desc}"
                response += f"\n\n🔗 [Read more]({link})"
                return response

        # 1C: Organic Results
        if "organic_results" in data and data["organic_results"]:
            org = data["organic_results"][0]
            snippet = org.get("snippet", "")
            link = org.get("link", fallback_link)
            return f"{snippet}\n\n🔗 [Read more]({link})"

    except Exception as e:
        print("SerpAPI failed:", str(e))

    # Step 2: DuckDuckGo fallback
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

import re

def get_roy_custom_answer(query):
    q = query.lower().strip()

    # Roy's Identity / Bio
    if re.search(r"\b(who\s+is\s+roy|who\s+are\s+you|who\s+is\s+pabitra|about\s+you|about\s+pabitra|tell\s+me\s+about\s+roy|your\s+bio|introduce\s+yourself)\b", q):
        return (
            "Pabitra Roy is an Information Security Engineer at Hy-Vee. "
            "He focuses on Identity and Access Management (IAM) and Security Engineering. "
            "He holds a Master’s Degree in Cybersecurity and is certified by CompTIA and Okta."
        )

    # Ask who am I
    if re.search(r"\b(who\s+am\s+i|my\s+name)\b", q):
        return "You are Pabitra Roy."

    # Full name / complete name
    if re.search(r"\b(full|complete)\s+name\b", q):
        return "Pabitra Roy"

    # Email-related
    if "email" in q or "contact" in q:
        return "Pab@h.com"

    # Company-related
    if "company" in q or "organization" in q or "work for" in q:
        return "Hy-Vee"

    # Team
    if "team" in q or "department" in q:
        return "IT Security"

    # Manager
    if "manager" in q or "reporting manager" in q or "reports to" in q:
        return "Person"

    # Personal info
    if re.search(r"\b(phone|mobile|address|home|partner|wife|girlfriend|boyfriend|husband)\b", q):
        return "I cannot answer any personal questions. Please send an email to him at Pab@h.com."

    return None

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    offers = None
    query = ""
    source = None  # Track source: 'roy' or 'web'

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            custom = get_roy_custom_answer(query)
            if custom:
                offers = custom
                source = "roy"
            else:
                offers = get_general_answer(query)
                source = "web"

    return render_template("index.html", offers=offers, query=query, source=source)


if __name__ == "__main__":
    app.run(debug=True)
