import json
from collections import defaultdict


def main():

    turns = defaultdict(list)

    try:
        with open("sample.jsonl", "r") as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                event = json.loads(line)

                turns[event["turn_id"]].append(event)

    except FileNotFoundError:
        print("Error: sample.jsonl not found.")
        return

    print("=" * 60)
    print("VOICE RAG TIMELINE")
    print("=" * 60)

    for turn_id in sorted(turns):

        print(f"\nTurn {turn_id}")
        print("-" * 60)

        events = sorted(turns[turn_id], key=lambda x: x["time_ms"])

        user_end = None
        first_audio = None

        for event in events:

            time = event["time_ms"]
            name = event["event"]

            if name == "asr_partial":
                print(f"[{time:>4} ms] ASR Partial : \"{event['text']}\"")

            elif name == "asr_final":
                print(f"[{time:>4} ms] ASR Final   : \"{event['text']}\"")

            elif name == "user_end":
                user_end = time
                print(f"[{time:>4} ms] User finished speaking")

            elif name == "controller_action":
                print(f"[{time:>4} ms] Controller Action : {event['action']}")

            elif name == "retrieval_result":
                print(f"[{time:>4} ms] Retrieved {event['passages']} passages")

            elif name == "tts_first_audio":
                first_audio = time
                print(f"[{time:>4} ms] First TTS Audio")

        if user_end is not None and first_audio is not None:
            print(f"\nTTFA = {first_audio - user_end} ms")

        print()

if __name__ == "__main__":
    main()
