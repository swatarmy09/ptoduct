import os
import json
import asyncio
import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import firebase_admin
from firebase_admin import credentials, db
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

# --- Telegram API ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # 👈 Must be set in ENV vars

# --- Cloudinary ---
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# --- Firebase ---
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CRED_JSON = os.getenv("FIREBASE_CRED_JSON")

# Convert FIREBASE_CRED_JSON into dict and fix private_key newlines
cred_dict = json.loads(FIREBASE_CRED_JSON)
cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# ✅ Use StringSession (No OTP prompt)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# Telegram channels to monitor
CHANNELS = ["Shopping_deal_offerss"]

# -------------------
# 🗑 Auto Delete Old (2 Days) Data + Images
# -------------------
def cleanup_old_products():
    ref = db.reference("products")
    data = ref.get()

    if data:
        now = datetime.datetime.now(datetime.timezone.utc)   # ✅ timezone-aware
        two_days_ago = now - datetime.timedelta(days=2)

        for key, item in data.items():
            try:
                postedAt = item.get("postedAt")
                if postedAt:
                    # postedAt is ISO format (timezone-aware)
                    post_time = datetime.datetime.fromisoformat(postedAt)

                    if post_time < two_days_ago:
                        # Delete Cloudinary image if exists
                        image_url = item.get("image")
                        if image_url:
                            try:
                                # Extract public_id from URL
                                public_id = image_url.split("/")[-1].split(".")[0]
                                cloudinary.uploader.destroy(public_id)
                                print(f"🗑 Deleted image from Cloudinary: {public_id}")
                            except Exception as e:
                                print(f"⚠️ Cloudinary delete error: {e}")

                        # Delete Firebase record
                        ref.child(key).delete()
                        print(f"🗑 Deleted old product: {item.get('text')[:40]}")

            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")

# -------------------
# 📩 Telegram Message Handler
# -------------------
@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    text = event.message.message or ""
    image_url = None

    # If message has image, upload to Cloudinary
    if event.message.photo:
        file_path = await client.download_media(event.message.photo)
        upload_result = cloudinary.uploader.upload(file_path)
        image_url = upload_result.get("secure_url")
        os.remove(file_path)

    # Save message to Firebase
    ref = db.reference("products")
    ref.push({
        "text": text,
        "image": image_url,
        "postedAt": event.message.date.astimezone(datetime.timezone.utc).isoformat()
    })

    print(f"✅ Saved: {text[:50]}... {image_url}")

    # Run cleanup after every insert
    cleanup_old_products()

# -------------------
# 🚀 Main Entry
# -------------------
async def main():
    print("🚀 Telegram Fetcher Started with StringSession...")
    await client.connect()

    if not await client.is_user_authorized():
        raise Exception("❌ Session string invalid or expired. Generate a new one.")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
