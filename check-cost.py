#!/usr/bin/env python3
"""
Cost monitor: checks accumulated token spend and notifies on every $1 threshold.
Runs as part of a cron job.
"""
import json, os, sys

COST_TRACKER = os.path.expanduser("~/.openclaw/workspace/memory/cost-tracker.json")
SESSIONS_FILE = os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json")

def get_total_cost():
    with open(SESSIONS_FILE) as f:
        data = json.load(f)
    total = 0.0
    for key, val in data.items():
        if isinstance(val, dict) and 'estimatedCostUsd' in val:
            total += float(val['estimatedCostUsd'])
    return total

def get_tracker():
    try:
        with open(COST_TRACKER) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"lastNotifiedDollar": 0, "accumulatedCost": 0.0, "lastChecked": ""}

def save_tracker(tracker):
    os.makedirs(os.path.dirname(COST_TRACKER), exist_ok=True)
    with open(COST_TRACKER, 'w') as f:
        json.dump(tracker, f, indent=2)

def main():
    tracker = get_tracker()
    total_cost = get_total_cost()
    tracker["accumulatedCost"] = round(total_cost, 6)
    tracker["lastChecked"] = __import__('datetime').datetime.now().isoformat()

    last_notified = tracker["lastNotifiedDollar"]
    current_dollar = int(total_cost)

    # Only notify if we've crossed at least $1 more than last notified
    if current_dollar > last_notified:
        for dollar in range(last_notified + 1, current_dollar + 1):
            # Write notification message to stdout for the cron delivery
            file_path = f"/tmp/openclaw-cost-alert-{dollar}.json"
            with open(file_path, 'w') as f:
                json.dump({
                    "type": "cost_alert",
                    "dollar": dollar,
                    "total_cost": round(total_cost, 4),
                    "message": f"💰 Token spend alert: crossed ${dollar}. Total: ${total_cost:.4f}"
                }, f)
        tracker["lastNotifiedDollar"] = current_dollar

    save_tracker(tracker)
    print(f"Cost check: ${total_cost:.4f} total, last notified: ${last_notified}, current: ${current_dollar}")

if __name__ == "__main__":
    main()
