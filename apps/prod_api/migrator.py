import os, json, time
from apps.prod_api.db import save_decision
from apps.prod_api.alerts import send_alert_if_needed

SAVE_PATH = os.getenv("IOA_SAVE_PATH", "/tmp/ioa_saved.jsonl")
POSITION_FILE = "/tmp/ioa_migrator_pos.txt"

def read_position():
    try:
        with open(POSITION_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0

def write_position(pos):
    with open(POSITION_FILE, "w") as f:
        f.write(str(pos))

def migrate_loop():
    pos = read_position()
    while True:
        try:
            if not os.path.exists(SAVE_PATH):
                time.sleep(2)
                continue
            with open(SAVE_PATH, "r") as f:
                lines = f.readlines()
            if pos < len(lines):
                new_lines = lines[pos:]
                for line in new_lines:
                    try:
                        rec = json.loads(line.strip())
                        # enrich standard keys so DB expects them
                        record = {
                            "symbol": rec.get("symbol"),
                            "price": rec.get("price"),
                            "sentiment": rec.get("sentiment"),
                            "reason": rec.get("reason"),
                            "score": rec.get("score"),
                            "boosted_score": rec.get("score"),
                            "decision": rec.get("decision"),
                            "saved": True,
                            "raw": rec
                        }
                        save_decision(record)
                        # trigger alerts if needed
                        send_alert_if_needed(record)
                    except Exception as e:
                        print("migrator error:", e)
                pos = len(lines)
                write_position(pos)
            time.sleep(2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("migrator outer:", e)
            time.sleep(3)

if __name__ == "__main__":
    migrate_loop()
