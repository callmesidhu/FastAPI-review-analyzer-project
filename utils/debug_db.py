from configs.database import get_db

conn = get_db()
cursor = conn.cursor()

print("--- Product Count ---")
cursor.execute("SELECT COUNT(*) FROM products")
print(cursor.fetchone()[0])

print("\n--- Review Count ---")
cursor.execute("SELECT COUNT(*) FROM reviews")
print(cursor.fetchone()[0])

print("\n--- Sample Reviews (ID, Rating, Sentiment, Polarity) ---")
cursor.execute("SELECT id, rating, sentiment, polarity, review_text FROM reviews LIMIT 5")
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Rating: {row['rating']}, Sentiment: {row['sentiment']}, Polarity: {row['polarity']}")
    print(f"Text: {row['review_text'][:50]}...")

conn.close()
