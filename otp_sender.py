# backend/otp_sender.py

import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_otp(receiver_email, otp):

    try:
        print("SENDER_EMAIL:", SENDER_EMAIL)
        print("PASSWORD LOADED:", APP_PASSWORD is not None)

        subject = "Your Resume AI OTP Code"

        body = f"""
Your OTP is: {otp}

This OTP is valid for 5 minutes.
Do not share this OTP with anyone.
"""

        message = f"Subject: {subject}\n\n{body}"

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(
            SENDER_EMAIL,
            receiver_email,
            message.encode("utf-8")
        )
        server.quit()

        print(f"OTP ({otp}) sent successfully to {receiver_email}")
        return True

    except Exception as e:
        print("Error sending email:", e)
        return False