"""Run once on your own computer to create the TG_SESSION secret.

    pip install telethon
    python make_session.py

It asks for api_id / api_hash (from my.telegram.org), your phone and the
login code Telegram sends you, then prints a long session string.
Paste that string into GitHub -> Settings -> Secrets -> Actions -> TG_SESSION.
Keep it private: it gives full access to the Telegram account.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("api_id: ").strip())
api_hash = input("api_hash: ").strip()
with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nTG_SESSION =\n")
    print(client.session.save())
