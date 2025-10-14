import os
import smtplib
from email.message import EmailMessage

# Get environment variables
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_TO = os.getenv('EMAIL_TO')

if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
    raise ValueError("Please set EMAIL_USER, EMAIL_PASS, and EMAIL_TO environment variables.")

# Read the file to send
FILE_PATH = 'cs2_prices.csv'
with open(FILE_PATH, 'r') as f:
    file_content = f.read()

msg = EmailMessage()
msg['Subject'] = f'CS2 Inventory File: {FILE_PATH}'
msg['From'] = EMAIL_USER
msg['To'] = EMAIL_TO
msg.set_content(f'Attached is the file {FILE_PATH} from your CS2 inventory tracker project.')
msg.add_attachment(file_content, filename=FILE_PATH)

# Send the email (using Gmail SMTP)
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_USER, EMAIL_PASS)
    smtp.send_message(msg)

print(f"Email sent to {EMAIL_TO} with {FILE_PATH} attached.")
