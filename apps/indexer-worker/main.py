import os
import time

SERVICE = os.getenv("SERVICE_NAME", "indexer-worker")


def run():
    i = 0
    while True:
        i += 1
        print(f"[{SERVICE}] heartbeat {i} - consuming events (stub)")
        time.sleep(5)


if __name__ == "__main__":
    run()

