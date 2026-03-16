import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.notifier import send_market_summary_email, send_signal_email

def test_email_system():
    load_dotenv()
    print("🚀 AlgoSignal AI: Email Diagnostic Tool")
    print("-" * 40)
    
    email = config.SENDER_EMAIL
    pwd = "*** masked ***" if config.SENDER_PASSWORD else "NOT SET"
    
    print(f"SMTP Config:")
    print(f"  Sender: {email}")
    print(f"  Password: {pwd}")
    print(f"  Server: {config.SMTP_SERVER}:{config.SMTP_PORT}")
    print("-" * 40)

    if not config.SENDER_EMAIL or not config.SENDER_PASSWORD:
        print("❌ ERROR: Email credentials not found in .env file.")
        return

    test_dest = input("Enter a destination email to send a test to: ")
    if not test_dest:
        print("Test cancelled.")
        return

    print(f"\n1. Testing Subscription Summary Email...")
    mock_summary = [
        {"ticker": "AAPL", "name": "Apple Inc.", "signal": "BUY", "price": 225.45},
        {"ticker": "TSLA", "name": "Tesla, Inc.", "signal": "SELL", "price": 175.20}
    ]
    success = send_market_summary_email(test_dest, mock_summary)
    
    if success:
        print("✅ Success: Subscription summary sent.")
    else:
        print("❌ Failed: Could not send subscription summary.")

    print(f"\n2. Testing Signal Alert Email...")
    success_alert = send_signal_email(test_dest, "Tester", "NVDA", "BUY", 124.50, 98.2)
    
    if success_alert:
        print("✅ Success: Signal alert sent.")
    else:
        print("❌ Failed: Could not send signal alert.")

    print("\n--- Diagnostic Complete ---")
    if success and success_alert:
        print("🌟 Your email system is working perfectly. Check your spam folder if you don't see it!")
    else:
        print("⚠️ Issues detected. Please verify your Google App Password and SMTP settings.")

if __name__ == "__main__":
    test_email_system()
