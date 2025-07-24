import os
import time
from imapclient import IMAPClient
import mailparser
import pdfkit
import smtplib
from email.message import EmailMessage


IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TARGET = os.getenv("TARGET")

def process_mail(uid, raw):
    print(f"📄 Processing Email UID {uid}...")
    try:
        mail = mailparser.parse_from_bytes(raw)
        html = mail.body
        subject = mail.subject or "Unnamed"
        sender = mail.from_[0][1]

        filename = f"/tmp/{uid}.pdf"
        pdfkit.from_string(html, filename)

        # ✉️ Sending PDF via email
        msg = EmailMessage()
        msg["Subject"] = f"Archived: {subject}"
        msg["From"] = SMTP_USER
        msg["To"] = TARGET
        msg.set_content(f"Original sender: {sender}")

        with open(filename, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=f"{subject}.pdf")

        with smtplib.SMTP_SSL(SMTP_HOST, 465) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

        print(f"✅ E-Mail UID {uid} had been processed and forwarded")
        os.remove(filename)
    except Exception as e:
        print(f"❌ Error while processing email with UID {uid}: {e}")

def idle_loop():
    print("📥 Waiting for new emails (IMAP-IDLE)...")
    with IMAPClient(IMAP_HOST) as client:
        client.login(IMAP_USER, IMAP_PASS)
        client.select_folder("INBOX")

        while True:
            try:
                print("⏳ Waiting for new email...")
                client.idle()
                responses = client.idle_check(timeout=300)  # Waiting 5 minutes or push
                client.idle_done()

                if responses:
                    print("📬 Got a new email!")
                    messages = client.search(["UNSEEN"])
                    for uid in messages:
                        raw = client.fetch([uid], ["RFC822"])[uid][b"RFC822"]
                        process_mail(uid, raw)

                time.sleep(1)

            except Exception as e:
                print(f"❌ Error while running: {e}")
                time.sleep(5)

if __name__ == "__main__":
    idle_loop()