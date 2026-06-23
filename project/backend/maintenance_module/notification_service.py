import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email_alert(vehicle_reg_no: str, component: str, level: str, message: str, rul: float, health: float, is_reminder: bool = False):
    """
    Sends an email notification for critical maintenance alerts. Supports reminder flag.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL_RECIPIENT")

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
        subject_title = f"{level.upper()} Maintenance Alert: Vehicle {vehicle_reg_no} - {component}"
        if is_reminder:
            subject_title = f"[REMINDER] {subject_title}"
            
        msg['Subject'] = subject_title
        msg['From'] = smtp_user
        msg['To'] = recipient

        # Reminder banner in HTML
        reminder_banner = ""
        if is_reminder:
            reminder_banner = """
            <div style="background-color: #fcf8e3; border: 1px solid #faebcc; color: #8a6d3b; padding: 12px; margin-bottom: 20px; border-radius: 4px; font-size: 14px;">
                <strong>⚠️ Friendly Reminder:</strong> This issue has not been resolved yet. Please schedule maintenance as soon as possible.
            </div>
            """

        # Create a nice HTML formatted email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: {'#d9534f' if level == 'urgent' else '#f0ad4e'};">
                Predictive Maintenance Alert ({level.upper()})
            </h2>
            {reminder_banner}
            <p>A maintenance alert is active for your fleet.</p>
            <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Vehicle Reg No:</strong></td>
                    <td>{vehicle_reg_no}</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Component:</strong></td>
                    <td style="text-transform: uppercase;">{component}</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Severity Level:</strong></td>
                    <td style="color: {'#d9534f' if level == 'urgent' else '#f0ad4e'}; font-weight: bold;">{level.upper()}</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Health Score:</strong></td>
                    <td>{health:.2f}%</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Estimated RUL:</strong></td>
                    <td>{rul:.1f} km</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Message:</strong></td>
                    <td>{message}</td>
                </tr>
                <tr>
                    <td style="background-color: #f9f9f9;"><strong>Time:</strong></td>
                    <td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                </tr>
            </table>
            <br>
            <p>Please take appropriate action via the Navigatto Dashboard.</p>
        </body>
        </html>
        """
        
        msg.set_content("Please enable HTML to view this message.")
        msg.add_alternative(html_content, subtype='html')

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        logging.info(f"Successfully sent {level} email alert (Reminder: {is_reminder}) for {vehicle_reg_no} - {component}")
        return True

    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")
        return False
