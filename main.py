import os
import json
import requests 

# এনভায়রনমেন্ট ভেরিয়েবল থেকে টোকেনগুলো নিন
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

# Gemini API এর URL সেট করুন
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Webhook অনুরোধ হ্যান্ডেল করার মূল ফাংশন
# যখন Vercel বা অন্য সার্ভারলেস প্ল্যাটফর্মে ডিপ্লয় করা হবে, তখন এই ফাংশনটিই রান করবে
def telegram_webhook_handler(request):
    # শুধুমাত্র POST অনুরোধ গ্রহণ করা হবে 
    if request.method != 'POST':
        return 'Method not allowed', 405

    try:
        # টেলিগ্রাম থেকে পাঠানো JSON ডেটা গ্রহণ করা
        update = request.get_json(silent=True)
        
        # মেসেজ থেকে মূল টেক্সট এবং চ্যাট আইডি বের করা
        chat_id = update['message']['chat']['id']
        user_message = update['message']['text']
        
        # [১] Gemini API কল করার জন্য পেলোড তৈরি করা
        payload = {
            'contents': [{'role': 'user', 'parts': [{'text': user_message}]}],
            'config': {'temperature': 0.8} # উত্তরের বৈচিত্র্য নিয়ন্ত্রণের জন্য
        }

        # [২] Gemini API কল করা (requests লাইব্রেরি ব্যবহার করে)
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Gemini API Key হেডার-এর বদলে URL-এ পাঠানো হয়
        gemini_url_with_key = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        ai_res = requests.post(
            gemini_url_with_key, 
            headers=headers, 
            json=payload
        )
        
        # Gemini রেসপন্স থেকে টেক্সট বের করা
        ai_response = ai_res.json()['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        # কোনো ত্রুটি হলে জেনেরিক মেসেজ পাঠানো
        if 'update' in locals() and 'message' in update:
            chat_id = update['message']['chat']['id']
        else:
            return 'Error processing message: No Chat ID', 500

        ai_response = f"দুঃখিত, বর্তমানে একটি সমস্যা হয়েছে। Error: {e}"

    # [৩] টেলিগ্রামে উত্তরটি ফেরত পাঠানো
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    requests.post(telegram_url, json={
        'chat_id': chat_id,
        'text': ai_response
    })

    return 'OK', 200 # সফলভাবে অনুরোধ প্রক্রিয়া করা হয়েছে
