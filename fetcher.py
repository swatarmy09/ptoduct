import os
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import firebase_admin
from firebase_admin import credentials, db
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # 👈 yaha tum apna generated session string env me daaloge

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_CRED_JSON = os.getenv("FIREBASE_CRED_JSON")

# Convert FIREBASE_CRED_JSON into dict and fix private_key newlines
cred_dict = json.loads(FIREBASE_CRED_JSON)
cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    "databaseURL": FIREBASE_DB_URL
})

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# ✅ Telegram client with StringSession
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

CHANNELS = ["Shopping_deal_offerss"]  # Telegram channel username list


@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    text = event.message.message or ""
    image_url = None

    # Handle images
    if event.message.photo:
        file_path = await client.download_media(event.message.photo)
        upload_result = cloudinary.uploader.upload(file_path)
        image_url = upload_result.get("secure_url")
        os.remove(file_path)

    # Save to Firebase
    ref = db.reference("products")
    ref.push({
        "text": text,
        "image": image_url,
        "postedAt": str(event.message.date)
    })

    print(f"✅ Saved: {text[:30]}... {image_url}")


if __name__ == "__main__":
    print("🚀 Telegram Fetcher Started with StringSession...")
    client.start()  # 👈 no OTP/phone prompt needed now
    client.run_until_disconnected()
