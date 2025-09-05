import os
import cloudinary
import cloudinary.uploader
from telethon import TelegramClient, events
import firebase_admin
from firebase_admin import credentials, db
import json

# ------------------------------
# 🔹 Load ENV variables
# ------------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CRED_JSON = os.getenv("FIREBASE_CRED_JSON")  # stored as env var in Render

CHANNEL = "Shopping_deal_offerss"

# ------------------------------
# 🔹 Init Cloudinary
# ------------------------------
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# ------------------------------
# 🔹 Init Firebase
# ------------------------------
cred_dict = json.loads(FIREBASE_CRED_JSON)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    "databaseURL": FIREBASE_DB_URL
})

# ------------------------------
# 🔹 Init Telegram Client
# ------------------------------
client = TelegramClient("session", API_ID, API_HASH)

# ------------------------------
# 🔹 Helper to save post
# ------------------------------
def save_to_firebase(text, img_url, posted_at):
    ref = db.reference("products")
    ref.push({
        "title": text,
        "image": img_url,
        "postedAt": str(posted_at)
    })
    print("✅ Saved:", text[:30], img_url)

# ------------------------------
# 🔹 Listen for new posts
# ------------------------------
@client.on(events.NewMessage(chats=CHANNEL))
async def handler(event):
    text = event.text or ""
    img_url = ""

    # agar photo hai → Cloudinary upload
    if event.photo:
        file_path = await event.download_media()
        upload_result = cloudinary.uploader.upload(file_path)
        img_url = upload_result["secure_url"]

    save_to_firebase(text, img_url, event.date)

# ------------------------------
# 🔹 Run client
# ------------------------------
print("🚀 Telegram Fetcher Started...")
client.start()
client.run_until_disconnected()
