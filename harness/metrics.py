import json
from collections import defaultdict

from stats import percentile, bootstrap_confidence_interval


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

    ttfa_list = []

    print("=" * 40)
    print("TTFA REPORT")
    print("=" * 40)

    for turn_id in sorted(turns):

        events = turns[turn_id]

        user_end = None
        first_audio = None

        for event in events:

            if event["event"] == "user_end":
                user_end = event["time_ms"]

            elif event["event"] == "tts_first_audio":
                first_audio = event["time_ms"]

        if user_end is not None and first_audio is not None:

            ttfa = first_audio - user_end
            ttfa_list.append(ttfa)

            print(f"Turn {turn_id}")
            print(f"TTFA : {ttfa} ms\n")

    if not ttfa_list:
        print("No TTFA values found.")
        return

    average = sum(ttfa_list) / len(ttfa_list)

    print("-" * 40)
    print(f"Average TTFA : {average:.2f} ms")
    print(f"P95 TTFA     : {percentile(ttfa_list,95):.2f} ms")

    ci = bootstrap_confidence_interval(ttfa_list)

    if ci:
        print(f"95% CI       : ({ci[0]:.2f}, {ci[1]:.2f}) ms")


if __name__ == "__main__":
    main()
