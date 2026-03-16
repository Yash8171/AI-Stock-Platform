import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from src.notifier import send_detailed_market_report_email
from src.config import config

print(f"DEBUG: SENDER_EMAIL = {config.SENDER_EMAIL}")
print(f"DEBUG: SMTP_SERVER = {config.SMTP_SERVER}")
print(f"DEBUG: SMTP_PORT = {config.SMTP_PORT}")
print(f"DEBUG: PASSWORD_SET = {bool(config.SENDER_PASSWORD)}")

# Mock data
stocks_data = [
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "signal": "BUY",
        "price": 225.50,
        "accuracy": 89.2,
        "confidence": 95.0
    }
]

recipient = "sanju373679@gmail.com"
print(f"Testing report email to: {recipient}")

try:
    success = send_detailed_market_report_email(recipient, stocks_data)
    if success:
        print("✅ Success! Email sent.")
    else:
        print("❌ Failed! (Check prints above)")
except Exception as e:
    print(f"💥 CRASH: {e}")
