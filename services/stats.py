def calculate_stats(reviews):
    total = len(reviews)
    pos = sum(1 for r in reviews if r["sentiment"] == "Positive")
    neg = sum(1 for r in reviews if r["sentiment"] == "Negative")
    neu = sum(1 for r in reviews if r["sentiment"] == "Neutral")

    avg_rating = round(sum(r["rating"] for r in reviews) / total, 2) if total else 0

    return {
        "total": total,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "avg_rating": avg_rating
    }
