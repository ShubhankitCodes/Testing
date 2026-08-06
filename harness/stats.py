import math
import random


def percentile(data, p):
    """
    Returns the pth percentile using linear interpolation.
    """

    if not data:
        return None

    data = sorted(data)

    k = (len(data) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return data[int(k)]

    return data[f] + (k - f) * (data[c] - data[f])


def bootstrap_confidence_interval(data, num_samples=1000, confidence=95):
    """
    Returns a bootstrap confidence interval for the mean.
    """

    if not data:
        return None

    bootstrap_means = []

    for _ in range(num_samples):
        sample = random.choices(data, k=len(data))
        bootstrap_means.append(sum(sample) / len(sample))

    bootstrap_means.sort()

    lower = percentile(bootstrap_means, (100 - confidence) / 2)
    upper = percentile(bootstrap_means, 100 - (100 - confidence) / 2)

    return lower, upper
