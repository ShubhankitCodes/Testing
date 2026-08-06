# Recall Report

## Objective

This report evaluates the retrieval performance of the hotel knowledge base using semantic search with FAISS and Sentence Transformers.

## Test Results
# Recall Report

| # | Question | Top Passage | Correct? |
|---|----------|-------------|----------|
| 1 | What time is check-in? | 01_checkin_policy.txt | Yes |
| 2 | What time is check-out? | 02_checkout_policy.txt | Yes |
| 3 | Can I check in early for free? | 03_early_checkin_free.txt | Yes |
| 4 | What is the charge for early check-in? |  52_early_checkin_paid.txt | Yes |
| 5 | Can I store my luggage after checkout? |06_luggage_storage.txt | Yes |
| 6 | Do you provide airport pickup and drop service? |  07_airport_transfer.txt| Yes |
| 7 | What time is breakfast served? | 58_breakfast_v2.txt or 21_breakfast_v1.txt | Yes |
| 8 | What are the swimming pool rules? | 31_pool_v1.txt or 59_pool_v2.txt | Yes |
| 9 | What are the gym timings? |  32_gym.txt | Yes |
|10 | Is Wi-Fi available for guests? | 43_wifi.txt| Yes |
|11 | Is parking available at the hotel? |  47_parking_v1.txt or 60_parking_v2.txt | Yes |
|12 | Are pets allowed in the hotel? |53_pet_policy_allowed.txt or 54_pet_policy_not_allowed.txt| Yes |
