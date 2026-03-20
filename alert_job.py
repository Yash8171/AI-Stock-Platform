import os
import time
import pytz
from datetime import datetime
from src.config import config
from src.ml_engine import generate_signals
from src.database import db
from src.notifier import send_signal_email, send_periodic_market_update_email

TICKER_NAMES = {
    'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.', 'TSLA': 'Tesla, Inc.', 'NVDA': 'NVIDIA Corp.',
    'META': 'Meta Platforms', 'SPY': 'S&P 500 ETF', 'QQQ': 'Nasdaq 100', 'JPM': 'JPMorgan Chase'
}

def is_trading_hours():
    """Checks if the current time is within US trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)."""
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    
    # Check if it's a weekday (0=Monday, 4=Friday)
    if now.weekday() > 4:
        return False
        
    # Check time range
    start_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    end_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return start_time <= now <= end_time

def run_alert_job(cycle_count=None):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting AI Stock Alert Job (Cycle #{cycle_count})...")
    
    # Check if it's trading hours (Optional: can be bypassed for testing)
    trading_hours_active = is_trading_hours()
    bypass = os.getenv("BYPASS_MARKET_CHECK") == "true"
    
    if not trading_hours_active and not bypass:
        print("Market is currently closed. Skipping alert cycle.")
        return

    # Check if we should even proceed with emails
    if not config.SENDER_EMAIL or not config.SENDER_PASSWORD:
        print("WARNING: SENDER_EMAIL or SENDER_PASSWORD not set in environment.")
        print("Emails will not be sent.")

    # ──────────────────────────────────────────────────────────────────────
    # STEP 1: Generate fresh signals for all tickers
    # ──────────────────────────────────────────────────────────────────────
    print(f"Processing {len(config.TARGET_TICKERS)} tickers...")
    current_signals = []   # For bulk periodic update
    signal_change_alerts = []  # For individual signal-change emails

    for ticker in config.TARGET_TICKERS:
        try:
            # Get previous signal to detect changes
            previous_signal = db.get_last_signal(ticker)
            
            result = generate_signals(ticker)
            if not result:
                print(f"  [{ticker}] Failed to generate signal.")
                continue
                
            current_signal = result['signal']
            price = result['latest_price']
            accuracy = result['accuracy']
            confidence_pct = result.get('confidence', 100.0)

            # Retrieve previous price to detect large moves
            last_pred = db.get_latest_predictions()
            p_entry = next((p for p in last_pred if p.get('_id') == ticker), None)
            prev_price = 0.0
            if p_entry and p_entry.get('latest_prediction'):
                prev_price = float(p_entry['latest_prediction'].get('metadata', {}).get('price', 0.0))
            
            price_moved_significantly = False
            if prev_price > 0:
                change_pct = abs((price - prev_price) / prev_price) * 100
                if change_pct >= 3.0:  # 3% threshold
                    price_moved_significantly = True
                    print(f"  [{ticker}] SIGNIFICANT PRICE MOVE detected: {change_pct:.2f}%")

            # Save to DB
            db.save_predictions(
                result['ticker'], 
                result['df_historical'].index[-1], 
                current_signal, 
                {
                    "accuracy": result['accuracy'],
                    "price": result['latest_price'],
                    "confidence": 100.0
                }
            )

            # Collect for bulk periodic update email
            current_signals.append({
                "ticker": ticker,
                "name": TICKER_NAMES.get(ticker, ticker),
                "signal": current_signal,
                "price": price,
                "accuracy": accuracy
            })

            # Detect signal-change alerts (individual urgent emails)
            # Threshold for urgent email alerts is 0.6 (60% confidence)
            if current_signal != previous_signal and current_signal in ["BUY", "SELL"] and confidence_pct >= 60.0:
                print(f"  [{ticker}] Signal change: {previous_signal} → {current_signal} (Conf: {confidence_pct:.1f}%)")
                signal_change_alerts.append({
                    "ticker": ticker,
                    "signal": current_signal,
                    "price": price,
                    "accuracy": accuracy
                })
            elif price_moved_significantly and current_signal in ["BUY", "SELL"] and confidence_pct >= 60.0:
                print(f"  [{ticker}] Significant price move + {current_signal} signal (Conf: {confidence_pct:.1f}%)")
                signal_change_alerts.append({
                    "ticker": ticker,
                    "signal": current_signal,
                    "price": price,
                    "accuracy": accuracy
                })
            else:
                print(f"  [{ticker}] {current_signal} @ ${price:.2f} (no change alert)")

        except Exception as e:
            print(f"  [{ticker}] Error: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # STEP 2: Send INDIVIDUAL SIGNAL-CHANGE alerts (urgent)
    # ──────────────────────────────────────────────────────────────────────
    if signal_change_alerts:
        all_recipients = []
        users = db.get_all_users()
        for u in users:
            if u.get('email'):
                all_recipients.append((u['email'], u.get('name', 'User')))
        for sub in db.get_all_subscribers():
            email = sub.get('email')
            if email and not any(r[0] == email for r in all_recipients):
                all_recipients.append((email, "Subscriber"))
        
        for alert in signal_change_alerts:
            for (email, name) in all_recipients:
                send_signal_email(email, name, alert['ticker'], alert['signal'], alert['price'], alert['accuracy'])

    # ──────────────────────────────────────────────────────────────────────
    # STEP 3: Send PERIODIC BULK UPDATE to ALL subscribers every cycle
    # (Only during trading hours - the whole job already respects this)
    # ──────────────────────────────────────────────────────────────────────
    if current_signals:
        print(f"\nSending periodic market update to all subscribers (cycle #{cycle_count})...")
        
        # Gather all unique recipient emails
        subscriber_emails = set()
        for u in db.get_all_users():
            if u.get('email'):
                subscriber_emails.add(u['email'])
        for sub in db.get_all_subscribers():
            if sub.get('email'):
                subscriber_emails.add(sub['email'])

        if subscriber_emails:
            for email in subscriber_emails:
                send_periodic_market_update_email(email, current_signals, cycle_count)
            print(f"  Periodic update sent to {len(subscriber_emails)} recipient(s).")
        else:
            print("  No subscribers yet — no periodic update sent.")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Alert Job Cycle #{cycle_count} Completed.\n")


if __name__ == "__main__":
    # Check for continuous run flag
    if os.getenv("RUN_CONTINUOUS") == "true":
        interval = int(os.getenv("ALERT_INTERVAL_SECONDS", 300))  # Default 5 mins
        print(f"Starting Alert Job in continuous mode. Interval: {interval}s ({interval//60} mins).")
        print(f"Will send periodic market updates EVERY cycle during trading hours (9:30 AM - 4:00 PM ET).")
        print(f"Signal-change alerts will also fire urgently when detected.\n")
        
        cycle = 1
        while True:
            run_alert_job(cycle_count=cycle)
            cycle += 1
            print(f"Waiting {interval}s ({interval//60} min) for next cycle...\n")
            time.sleep(interval)
    else:
        run_alert_job(cycle_count=1)
