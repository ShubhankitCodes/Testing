import json
import sys
from collections import defaultdict


def main():

    if len(sys.argv) != 2:
        print("Usage: python replay.py <log_file>")
        return

    log_file = sys.argv[1]

    turns = defaultdict(list)

    try:
        with open(log_file, "r") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                event = json.loads(line)
                turns[event["turn_id"]].append(event)

    except FileNotFoundError:
        print(f"Error: {log_file} not found.")
        return

    print("=" * 70)
    print("VOICE RAG TIMELINE")
    print("=" * 70)

    for turn_id in sorted(turns):

        print(f"\nTurn {turn_id}")
        print("-" * 70)

        events = sorted(turns[turn_id], key=lambda x: x["t_ms"])

        user_end = None
        first_audio = None

        for event in events:

            t = event["t_ms"]
            actor = event["actor"]
            event_type = event["event_type"]
            payload = event["payload"]

            if event_type in ("asr_partial", "asr_final"):
                print(f'[{t:>4} ms] {actor:<7} {event_type:<20} "{payload["text"]}"')

            elif event_type == "user_end":
                user_end = t
                print(f"[{t:>4} ms] {actor:<7} {event_type}")

            elif event_type == "controller_action":
                print(f"[{t:>4} ms] {actor:<7} {event_type:<20} {payload['action']}")

            elif event_type == "retrieval_launched":
                print(f'[{t:>4} ms] {actor:<7} {event_type:<20} "{payload["query"]}"')

            elif event_type == "retrieval_result":
                print(f"[{t:>4} ms] {actor:<7} {event_type:<20} ({len(payload['passages'])} passages)")

            elif event_type == "llm_first_token":
                print(f'[{t:>4} ms] {actor:<7} {event_type:<20} "{payload["token"]}"')

            elif event_type == "llm_final":
                print(f'[{t:>4} ms] {actor:<7} {event_type:<20} "{payload["text"]}"')

            elif event_type == "tts_first_audio":
                first_audio = t
                print(f"[{t:>4} ms] {actor:<7} {event_type}")

            elif event_type == "barge_in":
                print(f"[{t:>4} ms] {actor:<7} {event_type}")

        if user_end is not None and first_audio is not None:
            print(f"\nTTFA = {first_audio-user_end} ms")


if __name__ == "__main__":
    main()
