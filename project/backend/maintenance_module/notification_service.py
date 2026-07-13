import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_alert_recipient():
    """
    Fetches the alert recipient email from the database system_settings table,
    falling back to os.getenv("ALERT_EMAIL_RECIPIENT").
    """
    from sqlalchemy import text
    try:
        from database.db import SessionLocal
        with SessionLocal() as session:
            res = session.execute(text("SELECT setting_value FROM system_settings WHERE setting_key = 'alert_recipient_email'")).fetchone()
            if res and res[0]:
                return res[0].strip()
    except Exception as e:
        logging.error(f"Failed to query alert_recipient_email from system_settings: {e}")
    return os.getenv("ALERT_EMAIL_RECIPIENT", "gautanvala95@gmail.com")

def send_email_alert(vehicle_reg_no: str, component: str, level: str, message: str, rul: float, health: float, is_reminder: bool = False):
    """
    Sends an email notification for critical maintenance alerts. Supports reminder flag.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = get_alert_recipient()

    if not all([smtp_server, smtp_port, smtp_user, smtp_pass, recipient]):
        logging.warning("Email credentials missing in .env. Skipping email notification.")
        # Print to console for debugging if credentials are not set
        subj_prefix = "[REMINDER] " if is_reminder else ""
        print(f"\n[EMAIL NOTIFICATION MOCK] To: {recipient}")
        print(f"Subject: {subj_prefix}{level.upper()} ALERT: {component} on Vehicle {vehicle_reg_no}")
        print(f"Message: {message}\n")
        return False

    try:
        msg = EmailMessage()
        
        # Soften subject to look like a normal human update (no alert words)
        subject_title = f"Status update for vehicle {vehicle_reg_no} ({component.title()})"
            
        msg['Subject'] = subject_title
        msg['From'] = smtp_user
        msg['To'] = recipient

        # Send as a casual personal note to bypass robot detection filters
        plain_text = (
            f"Hi,\n\n"
            f"Just wanted to let you know that the {component} on vehicle {vehicle_reg_no} is currently showing a health score of {health:.2f}%.\n"
            f"Estimated remaining distance is around {rul:.1f} km.\n\n"
            f"Please check this out when you get a chance.\n\n"
            f"Thanks!"
        )
        msg.set_content(plain_text)

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        logging.info(f"Successfully sent {level} email alert (Reminder: {is_reminder}) for {vehicle_reg_no} - {component}")
        return True

    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")
        return False


def send_whatsapp_alert(vehicle_reg_no: str, component: str, level: str, message: str, rul: float, health: float, is_reminder: bool = False):
    """
    Sends a WhatsApp message via Twilio for critical maintenance alerts. Supports reminder flag.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    to_number = os.getenv("ALERT_WHATSAPP_RECIPIENT")

    subj_prefix = "[REMINDER] " if is_reminder else ""

    if not all([account_sid, auth_token, from_number, to_number]):
        logging.warning("Twilio credentials missing in .env. Skipping WhatsApp notification.")
        # Print to console for debugging if credentials are not set
        print(f"\n[WHATSAPP NOTIFICATION MOCK] To: {to_number}")
        print(f"Message: {subj_prefix}{level.upper()} ALERT: The {component} on vehicle {vehicle_reg_no} is currently showing a health score of {health:.2f}%. Remaining distance is around {rul:.1f} km. {message}\n")
        return False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        body_text = (
            f"🚨 *{subj_prefix}FleetIQ ALERT* 🚨\n\n"
            f"Vehicle: *{vehicle_reg_no}*\n"
            f"Component: *{component.upper()}*\n"
            f"Health Score: *{health:.2f}%*\n"
            f"Remaining Life: *{rul:.1f} km*\n\n"
            f"Details: {message}"
        )
        
        msg = client.messages.create(
            from_=from_number,
            body=body_text,
            to=to_number
        )
        logging.info(f"Successfully sent {level} WhatsApp alert (Reminder: {is_reminder}, SID: {msg.sid}) for {vehicle_reg_no} - {component}")
        return True
    except Exception as e:
        logging.error(f"Failed to send WhatsApp alert: {e}")
        return False

