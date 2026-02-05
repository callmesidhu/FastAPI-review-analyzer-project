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

def calculate_correlations(reviews):
    if not reviews:
        default_val = {"r": 0, "p": 0, "text": "No data available"}
        return {
            "rating_sentiment": default_val,
            "rating_length": default_val
        }
    
    from scipy.stats import pearsonr
    def get_description(r):
        if abs(r) > 0.7: return "Strong"
        if abs(r) > 0.4: return "Moderate"
        if abs(r) > 0.1: return "Weak"
        return "Negligible"

    try:
        ratings = [r["rating"] for r in reviews]
        polarities = [r["polarity"] for r in reviews]
        lengths = [len(r["review_text"]) for r in reviews]
        
        # Rating vs Sentiment
        if len(set(ratings)) > 1 and len(set(polarities)) > 1:
            r_s, p_s = pearsonr(ratings, polarities)
            rating_sentiment = {
                "r": round(r_s, 2),
                "p": round(p_s, 4),
                "text": f"{get_description(r_s)} {'positive' if r_s > 0 else 'negative'} relationship"
            }
        else:
            rating_sentiment = {"r": 0, "p": 0, "text": "Insufficient variance"}

        # Rating vs Length
        if len(set(ratings)) > 1 and len(set(lengths)) > 1:
            r_l, p_l = pearsonr(ratings, lengths)
            rating_length = {
                "r": round(r_l, 2),
                "p": round(p_l, 4),
                "text": f"{get_description(r_l)} {'positive' if r_l > 0 else 'negative'} relationship"
            }
        else:
            rating_length = {"r": 0, "p": 0, "text": "Insufficient variance"}

        return {
            "rating_sentiment": rating_sentiment,
            "rating_length": rating_length
        }
    except Exception as e:
        print(f"Correlation error: {e}")
        err_val = {"r": 0, "p": 0, "text": "Calculation error"}
        return {
            "rating_sentiment": err_val,
            "rating_length": err_val
        }

