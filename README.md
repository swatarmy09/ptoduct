# Telegram → Cloudinary → Firebase Fetcher

## 🔹 Setup
1. `git clone` this repo
2. Add your secrets in Render dashboard → Environment variables:
   - `API_ID` = your telegram api_id
   - `API_HASH` = your telegram api_hash
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `FIREBASE_DB_URL`
   - `FIREBASE_CRED_JSON` = paste entire Firebase serviceAccount.json as string

3. Deploy on Render as Worker (free plan).

## 🔹 Flow
- Listens to Telegram channel: `@Shopping_deal_offerss`
- Downloads new post images
- Uploads to Cloudinary
- Saves (text + image URL) into Firebase Realtime Database
- Android app listens to Firebase → auto update
