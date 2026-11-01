def rolling_average(values, window=7):
    result = []
    window_sum = 0
    for i, v in enumerate(values):
        window_sum += v
        if i >= window:
            window_sum -= values[i - window]
        result.append(window_sum / min(i + 1, window))
    return result


def current_streak(flags):
    streak = 0
    for f in reversed(flags):
        if not f:
            break
        streak += 1
    return streak