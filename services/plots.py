
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

def _set_dark_theme(fig, ax):
    """Applies a consistent dark theme to the plot."""
    fig.patch.set_facecolor('#303134')
    ax.set_facecolor('#303134')
    ax.spines['bottom'].set_color('#5f6368')
    ax.spines['top'].set_color('#5f6368')
    ax.spines['left'].set_color('#5f6368')
    ax.spines['right'].set_color('#5f6368')
    ax.tick_params(axis='x', colors='#e8eaed')
    ax.tick_params(axis='y', colors='#e8eaed')
    ax.yaxis.label.set_color('#e8eaed')
    ax.xaxis.label.set_color('#e8eaed')
    ax.title.set_color('#e8eaed')

def _handle_empty_data(ax, message="No Data Available"):
    """Displays a message on the plot if no data is available."""
    ax.text(0.5, 0.5, message, 
            horizontalalignment='center', 
            verticalalignment='center', 
            transform=ax.transAxes,
            color='#9aa0a6',
            fontsize=14)
    ax.set_xticks([])
    ax.set_yticks([])

def generate_review_length_plot(reviews):
    fig, ax = plt.subplots(figsize=(10, 6))
    _set_dark_theme(fig, ax)
    
    if not reviews:
        _handle_empty_data(ax)
    else:
        lengths = [len(r["review_text"]) for r in reviews if r.get("review_text")]
        if not lengths:
            _handle_empty_data(ax)
        else:
            ax.hist(lengths, bins=20, color='#8ab4f8', edgecolor='#202124')
            ax.set_title('Distribution of Review Lengths', pad=20)
            ax.set_xlabel('Review Length (characters)')
            ax.set_ylabel('Number of Reviews')
            ax.grid(axis='y', alpha=0.1, color='#e8eaed')

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    img.seek(0)
    return img

def generate_sentiment_polarity_plot(reviews):
    fig, ax = plt.subplots(figsize=(10, 6))
    _set_dark_theme(fig, ax)
    
    if not reviews:
        _handle_empty_data(ax)
    else:
        polarities = [r["polarity"] for r in reviews if r.get("polarity") is not None]
        if not polarities:
            _handle_empty_data(ax)
        else:
            ax.hist(polarities, bins=20, range=(-1, 1), color='#34a853', edgecolor='#202124')
            ax.set_title('Distribution of Sentiment Polarity', pad=20)
            ax.set_xlabel('Polarity Score (-1 to 1)')
            ax.set_ylabel('Number of Reviews')
            ax.axvline(0, color='#f28b82', linestyle='dashed', linewidth=1.5)
            ax.grid(axis='y', alpha=0.1, color='#e8eaed')

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    img.seek(0)
    return img

def generate_length_by_rating_plot(reviews):
    fig, ax = plt.subplots(figsize=(10, 6))
    _set_dark_theme(fig, ax)
    
    # Organize data by rating
    data = [[] for _ in range(5)] # 1 to 5 stars
    has_data = False
    
    for r in reviews:
        try:
            rating = int(r["rating"])
            if 1 <= rating <= 5 and r.get("review_text"):
                data[rating-1].append(len(r["review_text"]))
                has_data = True
        except (ValueError, TypeError):
            continue
            
    if not has_data:
        _handle_empty_data(ax)
    else:
        # Filter out empty categories for boxplot but keep labels
        bp = ax.boxplot(data, labels=['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'], 
                    patch_artist=True,
                    boxprops=dict(facecolor='#8ab4f8', color='#8ab4f8', alpha=0.4),
                    capprops=dict(color='#e8eaed'),
                    whiskerprops=dict(color='#e8eaed'),
                    flierprops=dict(markeredgecolor='#f28b82'),
                    medianprops=dict(color='#f28b82', linewidth=2))
        
        ax.set_title('Review Length vs. Rating', pad=20)
        ax.set_xlabel('Rating')
        ax.set_ylabel('Review Length (characters)')
        ax.grid(axis='y', alpha=0.1, color='#e8eaed', linestyle='--')

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    img.seek(0)
    return img

