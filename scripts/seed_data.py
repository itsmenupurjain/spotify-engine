"""
Seed Data Generator — creates realistic synthetic review data across all 5 sources.

Generates 500+ entries covering all complaint categories, user segments, sentiments,
and discovery-related themes for development and demo purposes.
"""

import uuid
import random
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# --- Data pools ---

SOURCES = ["app_store", "play_store", "reddit", "spotify_community", "twitter_x"]

COMPLAINT_CATEGORIES = [
    "algorithm_staleness",
    "choice_overload",
    "trust_erosion",
    "mood_mismatch",
    "interface_friction",
    "lack_of_context",
    "genre_bubble",
    "social_disconnect",
    "no_complaint",
    "other",
]

USER_SEGMENTS = [
    "active_explorer_stuck",
    "background_listener",
    "mood_regulator",
    "identity_listener",
    "socially_led_discoverer",
    "new_user",
    "unclear",
]

SENTIMENTS = ["very_negative", "negative", "neutral", "positive", "very_positive"]
DISCOVERY_INTENTS = ["high", "medium", "low", "none"]

# Realistic review templates per complaint category
REVIEWS_BY_CATEGORY = {
    "algorithm_staleness": [
        "My Discover Weekly has been recommending the same type of songs for months now. I've been listening to completely different genres but Spotify doesn't seem to care. It's like the algorithm is stuck in 2023.",
        "I keep getting the same artists over and over in my recommendations. I've listened to hundreds of different songs but Discover Weekly still thinks I only listen to indie rock. So frustrating.",
        "The algorithm never evolves. I started listening to jazz 3 months ago but all my recommendations are still the same electronic music. How long does it take to learn?",
        "Used to love Discover Weekly, now it's just recycled songs I've already heard or artists I already know. There's nothing 'discover' about it anymore.",
        "Spotify recommended me a song I listened to literally yesterday as a 'new discovery'. The staleness of these recommendations is unbearable.",
        "Every week it's the same vibe, same energy, same boring suggestions. I pay premium for THIS? The algorithm has completely stagnated.",
        "My Release Radar used to be exciting. Now it's just the same 5 artists releasing mid singles. Algorithm is definitely broken.",
        "I actively try to listen to new genres but Spotify keeps pulling me back to my comfort zone. It's like the algorithm WANTS me to be bored.",
        "Haven't found a single new artist through Spotify recommendations in over 6 months. The algorithm needs a complete overhaul.",
        "The suggestions are SO predictable now. I can guess every song before I even open Discover Weekly. That's not discovery, that's repetition.",
    ],
    "choice_overload": [
        "There are SO many playlists on Spotify I don't even know where to start. Daily Mix 1 through 6, Discover Weekly, Release Radar, genre mixes... it's overwhelming.",
        "I open the app wanting to find something new and I'm hit with 50 different playlists and recommendations. I just end up playing the same old stuff because choosing is exhausting.",
        "Too many options, not enough curation. I wish Spotify would just give me ONE playlist that's perfect instead of 20 that are mediocre.",
        "The browse page is a mess. So many categories, so many playlists, no clear path to actually discovering something I'd love. Analysis paralysis is real.",
        "I spend more time scrolling through recommendations than actually listening to music. The paradox of choice is killing my discovery.",
        "Every time I open the app there are new sections, new playlists, new features. Just give me good music recommendations, I don't need 15 different ways to find it.",
    ],
    "trust_erosion": [
        "I've given Discover Weekly so many chances and it keeps disappointing. I've completely stopped checking it. Trust is gone.",
        "Listened to 10 recommendations in a row — didn't like a single one. Why would I waste my time trying more? Spotify's lost my trust.",
        "I used to religiously check DW every Monday. After months of bad suggestions I just stopped. Now I find music on TikTok instead.",
        "Every time I try what Spotify suggests I regret it. The recommendations are so off that I've lost all faith in the algorithm.",
        "Spotify recommended me a podcast in my Discover Weekly. A PODCAST. In a music discovery playlist. That's when I knew the algorithm was completely broken.",
        "I thumbs-down songs and they STILL show up in my playlists. What's the point of giving feedback if Spotify ignores it? Zero trust left.",
        "The algorithm recommended my own playlist back to me as a 'discovery'. I can't make this up. Completely lost faith.",
    ],
    "mood_mismatch": [
        "I'm trying to study and Spotify recommends high-energy dance tracks. Read the room, algorithm.",
        "Late night chill session and Spotify hits me with heavy metal recommendations. The mood detection is completely broken.",
        "I wish Spotify understood that my music taste changes based on my mood. Morning me and evening me are different people.",
        "The recommendations don't match my vibe AT ALL. I'm going through a breakup and it's recommending happy pop songs. Tone deaf algorithm.",
        "Context matters! I listen to different music at the gym vs at work vs relaxing. Spotify treats it all the same.",
        "Played some calming music while working and now ALL my recommendations are lo-fi. I have a whole other side of my music taste that's being ignored.",
    ],
    "interface_friction": [
        "Where did the 'Discover' tab go? I can't find any way to actively browse new music anymore. The UI keeps changing.",
        "The app redesign made it harder to find new music. The old interface was so much better for discovery.",
        "I can't figure out how to tell Spotify I don't like something. The dislike button is hidden in a submenu. Make it easier!",
        "Why is there no 'surprise me' button? I just want to hear something completely random and new without navigating 5 screens.",
        "The home page is cluttered with podcasts and audiobooks. I'm here for MUSIC. Stop hiding music discovery behind podcast ads.",
        "Had to scroll past 10 podcast recommendations to find actual music suggestions. The interface priorities are completely wrong.",
    ],
    "lack_of_context": [
        "Spotify doesn't understand WHY I listen to certain songs. I played 'Bohemian Rhapsody' at a party once and now it thinks I'm a Queen superfan.",
        "I listened to baby shark for my kid and now my entire recommendation feed is children's music. Context collapse is real.",
        "The algorithm can't tell the difference between songs I play because I love them and songs I play as background noise. Not the same thing!",
        "I share my account with my partner sometimes and now my recommendations are a confusing mess of both our tastes.",
        "Played one Christmas song in December and got Christmas recommendations until March. The algorithm has no concept of seasonal context.",
        "I listened to a language learning podcast once and now Spotify thinks I speak Spanish. All my music recs changed. So annoying.",
    ],
    "genre_bubble": [
        "I'm stuck in an indie rock bubble. I listen to other genres too but Spotify only recommends variations of the same thing.",
        "The filter bubble is SO real on Spotify. Every recommendation is within the same narrow genre. Where's the diversity?",
        "I want to explore K-pop but all I get is more of the same Western pop I already listen to. Breaking out of the genre bubble is impossible.",
        "Spotify created an echo chamber of my own taste. I need it to push me OUTSIDE my comfort zone sometimes, not keep reinforcing it.",
        "All my Daily Mixes sound the same. Mix 1 through 6 are basically identical. That's not variety, that's an illusion of choice.",
        "Tried to get into classical music but Spotify keeps dragging me back to hip-hop. The bubble effect is suffocating.",
    ],
    "social_disconnect": [
        "I discover most of my music from friends and TikTok, not from Spotify. The social features on Spotify are basically dead.",
        "Why can't I see what my friends are listening to easily? The social discovery features are buried and broken.",
        "Spotify used to have a social feed. Now there's no way to discover music through my network. I use Instagram for that instead.",
        "My friends have great taste but Spotify makes it impossible to actually discover music through them. The collaborative playlist feature is clunky.",
        "I find more new music from Twitter threads than from Spotify's algorithm. That's sad.",
        "The 'Friend Activity' sidebar on desktop was removed from mobile. Social discovery is dead on Spotify mobile.",
    ],
    "no_complaint": [
        "Love Discover Weekly! Found some great artists this week. Keep it up Spotify!",
        "The algorithm really gets me. My Daily Mix is always on point. Best music streaming service hands down.",
        "Just discovered an amazing new artist through Release Radar. Spotify's recommendations are actually getting better.",
        "Premium is worth every penny. The curated playlists are perfect for my taste. No complaints!",
        "Spotify's blend feature with my girlfriend is honestly so fun. We discover new music together every week.",
    ],
    "other": [
        "The app crashes every time I try to download music. Fix your app Spotify!",
        "Premium prices keep going up but the quality stays the same. Not worth it anymore.",
        "The offline mode is broken again. Can't listen to my downloaded songs without internet. What's the point?",
        "Why does Spotify have a 10,000 song library limit? I'm a music hoarder and I need MORE.",
    ],
}

REDDIT_POST_TITLES = [
    "Discover Weekly has been terrible lately — anyone else?",
    "How to actually find new music on Spotify?",
    "The algorithm is completely broken [rant]",
    "DAE feel like Spotify recommendations never change?",
    "Switching from Spotify because of bad recommendations",
    "My Discover Weekly is just songs I already know",
    "Spotify algorithm stuck in a loop",
    "Tips for getting better recommendations?",
    "Why does Spotify keep recommending the same artists?",
    "Is Release Radar useless for anyone else?",
    "Spotify recommended me my own playlist LOL",
    "The discovery problem: why I can't find new music",
]

SUBREDDITS = ["spotify", "Music", "ifyoulikeblank", "SpotifyPlaylists", "audiophile"]

UNMET_NEEDS = [
    "Music recommendations that actually evolve with my changing taste",
    "A way to break out of my genre bubble without random noise",
    "Context-aware recommendations based on time and mood",
    "Better feedback mechanism to tell the algorithm what I like",
    "More diverse recommendations across genres and eras",
    "Social discovery features that actually work",
    "A single curated playlist instead of choice overload",
    "Recommendations that distinguish between active and passive listening",
    "Fresh discoveries every week, not recycled familiar songs",
    "An algorithm that learns from negative feedback",
    "Mood-based discovery that reads the room",
    "Cross-genre recommendations for adventurous listeners",
    "A surprise me button for spontaneous discovery",
    "Recommendations based on my mood, not just my history",
    "Better handling of shared accounts and mixed listening",
]

JTBD_TEMPLATES = [
    "When I want to explore new music, I want fresh recommendations that match my evolving taste, so that I can discover artists I'd never find on my own",
    "When I'm tired of my usual playlist, I want to easily break out of my genre bubble, so that I can experience new styles of music",
    "When I'm in a specific mood, I want context-aware music suggestions, so that the music enhances rather than disrupts my current state",
    "When I open Spotify, I want a simple clear path to discovery, so that I don't feel overwhelmed and give up",
    "When I dislike a recommendation, I want the algorithm to learn immediately, so that I don't waste time on bad suggestions",
    "When I share music with friends, I want seamless social discovery features, so that I can find music through people I trust",
    "When I've been listening to the same songs for weeks, I want a push toward something different, so that I reignite my passion for music",
]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _random_date(days_back: int = 365) -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def _compute_source_weight(source: str) -> float:
    weights = {
        "app_store": 1.0,
        "play_store": 1.0,
        "reddit": 0.9,
        "spotify_community": 0.8,
        "twitter_x": 0.7,
    }
    return weights.get(source, 0.5)


def _compute_recency_score(published_at: datetime) -> float:
    days_ago = (datetime.now(timezone.utc) - published_at).days
    if days_ago <= 30:
        return 1.0
    elif days_ago <= 90:
        return 0.8
    elif days_ago <= 180:
        return 0.6
    else:
        return 0.4


def _sentiment_score_from_label(sentiment: str) -> float:
    scores = {
        "very_negative": random.uniform(-1.0, -0.7),
        "negative": random.uniform(-0.7, -0.3),
        "neutral": random.uniform(-0.2, 0.2),
        "positive": random.uniform(0.3, 0.7),
        "very_positive": random.uniform(0.7, 1.0),
    }
    return round(scores.get(sentiment, 0.0), 3)


def generate_raw_review(category: str, source: str, index: int) -> Dict[str, Any]:
    """Generate a single raw review entry."""
    reviews = REVIEWS_BY_CATEGORY.get(category, REVIEWS_BY_CATEGORY["other"])
    body = random.choice(reviews)
    published_at = _random_date()
    author_hash = _hash_text(f"user_{index}_{source}")[:16]

    review = {
        "id": str(uuid.uuid4()),
        "source": source,
        "external_id": f"{source}_{uuid.uuid4().hex[:12]}",
        "body": body,
        "author_hash": author_hash,
        "published_at": published_at.isoformat(),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "language": "en",
        "is_relevant": category != "other",
        "body_hash": _hash_text(body + str(index)),
        "source_weight": _compute_source_weight(source),
        "recency_score": _compute_recency_score(published_at),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Source-specific fields
    if source in ("app_store", "play_store"):
        review["rating"] = random.choice([1, 1, 2, 2, 3, 4, 5]) if category != "no_complaint" else random.choice([4, 5])
        review["title"] = body[:60] + "..." if len(body) > 60 else body
        review["app_version"] = f"8.{random.randint(8, 9)}.{random.randint(0, 99)}"
        review["country_code"] = random.choice(["US", "GB", "CA", "AU", "DE", "FR", "IN"])
        review["engagement_score"] = random.randint(0, 150)
    elif source == "reddit":
        review["subreddit"] = random.choice(SUBREDDITS)
        review["post_title"] = random.choice(REDDIT_POST_TITLES)
        review["post_score"] = random.randint(5, 500)
        review["is_comment"] = random.choice([True, False])
        review["engagement_score"] = review["post_score"]
        if review["is_comment"]:
            review["comment_score"] = random.randint(1, 100)
            review["parent_post_id"] = f"reddit_post_{uuid.uuid4().hex[:8]}"
    elif source == "spotify_community":
        review["title"] = random.choice(REDDIT_POST_TITLES)
        review["reply_count"] = random.randint(1, 50)
        review["kudos_count"] = random.randint(0, 200)
        review["thread_status"] = random.choice(["Not Right Now", "Under Consideration", "Good Idea", None])
        review["engagement_score"] = review["kudos_count"]
    elif source == "twitter_x":
        review["like_count"] = random.randint(0, 500)
        review["retweet_count"] = random.randint(0, 100)
        review["engagement_score"] = review["like_count"]

    return review


def generate_classified_review(raw_review: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Generate AI classification for a raw review."""
    # Determine segment based on category
    segment_weights = {
        "algorithm_staleness": ["active_explorer_stuck", "active_explorer_stuck", "mood_regulator"],
        "choice_overload": ["active_explorer_stuck", "new_user", "background_listener"],
        "trust_erosion": ["active_explorer_stuck", "active_explorer_stuck", "identity_listener"],
        "mood_mismatch": ["mood_regulator", "mood_regulator", "active_explorer_stuck"],
        "interface_friction": ["new_user", "active_explorer_stuck", "background_listener"],
        "lack_of_context": ["active_explorer_stuck", "mood_regulator", "identity_listener"],
        "genre_bubble": ["active_explorer_stuck", "active_explorer_stuck", "socially_led_discoverer"],
        "social_disconnect": ["socially_led_discoverer", "socially_led_discoverer", "active_explorer_stuck"],
        "no_complaint": ["background_listener", "active_explorer_stuck", "unclear"],
        "other": ["unclear", "background_listener", "new_user"],
    }

    sentiment = random.choice(["very_negative", "negative", "negative"]) if category not in ("no_complaint", "other") else random.choice(["positive", "very_positive", "neutral"])
    segment = random.choice(segment_weights.get(category, ["unclear"]))

    # Extract key phrase from body
    body = raw_review["body"]
    sentences = body.split(". ")
    key_phrase = sentences[0] if sentences else body[:100]

    classified = {
        "id": str(uuid.uuid4()),
        "raw_review_id": raw_review["id"],
        "is_discovery_relevant": category not in ("other",),
        "primary_complaint_category": category,
        "secondary_complaint_category": random.choice([c for c in COMPLAINT_CATEGORIES if c != category and c != "no_complaint"]) if random.random() > 0.6 else None,
        "user_segment_signal": segment,
        "sentiment": sentiment,
        "sentiment_score": _sentiment_score_from_label(sentiment),
        "discovery_intent": random.choice(["high", "high", "medium"]) if category not in ("no_complaint", "other") else random.choice(["low", "none"]),
        "repetition_behavior_mentioned": category in ("algorithm_staleness", "genre_bubble") or random.random() > 0.7,
        "key_frustration_phrase": key_phrase if category not in ("no_complaint",) else None,
        "unmet_need": random.choice(UNMET_NEEDS) if category not in ("no_complaint", "other") else None,
        "jtbd_statement": random.choice(JTBD_TEMPLATES) if category not in ("no_complaint", "other") and random.random() > 0.3 else None,
        "confidence_score": round(random.uniform(0.7, 0.98), 3),
        "detected_language": "en",
        "source_weight": raw_review["source_weight"],
        "recency_score": raw_review["recency_score"],
        "classified_at": datetime.now(timezone.utc).isoformat(),
        "classification_model": "claude-sonnet-4-6",
        "classification_failed": False,
        "embedding_pending": True,
    }

    return classified


THEME_DEFINITIONS = {
    "algorithm_staleness": {
        "theme_name": "Algorithm Never Evolves",
        "theme_description": "Users feel recommendations stagnate despite changing listening behavior and exploring new genres",
        "representative_quote": "My Discover Weekly has been recommending the same type of songs for months now",
        "trend_direction": "growing",
    },
    "genre_bubble": {
        "theme_name": "Genre Echo Chamber",
        "theme_description": "Users trapped in narrow genre bubbles, unable to discover music across different styles",
        "representative_quote": "I'm stuck in an indie rock bubble. I listen to other genres too but Spotify only recommends variations of the same thing",
        "trend_direction": "growing",
    },
    "trust_erosion": {
        "theme_name": "Lost Trust in Recommendations",
        "theme_description": "Repeated bad suggestions have eroded user confidence in the algorithm over time",
        "representative_quote": "I've given Discover Weekly so many chances and it keeps disappointing. Trust is gone.",
        "trend_direction": "stable",
    },
    "mood_mismatch": {
        "theme_name": "Mood Context Blindness",
        "theme_description": "Algorithm ignores situational and emotional context for music selection",
        "representative_quote": "I'm trying to study and Spotify recommends high-energy dance tracks",
        "trend_direction": "stable",
    },
    "choice_overload": {
        "theme_name": "Overwhelming Choice Paralysis",
        "theme_description": "Too many playlists and options lead to decision fatigue and defaulting to familiar music",
        "representative_quote": "I open the app wanting to find something new and I'm hit with 50 different playlists",
        "trend_direction": "declining",
    },
    "interface_friction": {
        "theme_name": "Discovery UI Buried",
        "theme_description": "Discovery surfaces are hard to find, navigate, or use within the app interface",
        "representative_quote": "Where did the Discover tab go? I can't find any way to actively browse new music anymore",
        "trend_direction": "stable",
    },
    "lack_of_context": {
        "theme_name": "Context Collapse Problem",
        "theme_description": "Algorithm doesn't understand WHY users listen to certain songs, mixing contexts",
        "representative_quote": "I listened to baby shark for my kid and now my entire recommendation feed is children's music",
        "trend_direction": "stable",
    },
    "social_disconnect": {
        "theme_name": "Dead Social Discovery",
        "theme_description": "Users discover music through friends and social media rather than the algorithm",
        "representative_quote": "I discover most of my music from friends and TikTok, not from Spotify",
        "trend_direction": "growing",
    },
}


def generate_themes_and_mappings(
    classified_reviews: list,
) -> tuple:
    """
    Generate themes from classified reviews and create review-theme mappings.

    Returns (themes_list, mappings_list)
    """
    themes = []
    mappings = []

    # Group classified reviews by primary complaint category
    category_groups = {}
    for cr in classified_reviews:
        cat = cr["primary_complaint_category"]
        if cat not in category_groups:
            category_groups[cat] = []
        category_groups[cat].append(cr)

    cluster_id = 0
    for category, definition in THEME_DEFINITIONS.items():
        reviews_in_cat = category_groups.get(category, [])
        if not reviews_in_cat:
            continue

        # Count distinct sources
        sources_in_cat = set(
            cr.get("source_from_raw", random.choice(SOURCES))
            for cr in reviews_in_cat
        )

        theme_id = str(uuid.uuid4())
        theme = {
            "id": theme_id,
            "cluster_id": cluster_id,
            "theme_name": definition["theme_name"],
            "theme_description": definition["theme_description"],
            "representative_quote": definition["representative_quote"],
            "review_count": len(reviews_in_cat),
            "cross_source_count": min(len(sources_in_cat), 5),
            "confidence_level": (
                "high" if len(sources_in_cat) >= 3
                else "medium" if len(sources_in_cat) >= 2
                else "low"
            ),
            "trend_direction": definition["trend_direction"],
        }
        themes.append(theme)

        # Create review-theme mappings
        for cr in reviews_in_cat:
            mappings.append({
                "review_id": cr["id"],
                "theme_id": theme_id,
                "similarity_score": round(random.uniform(0.7, 0.99), 3),
            })

        cluster_id += 1

    return themes, mappings


def generate_synthesis_cache(
    raw_reviews: list,
    classified_reviews: list,
    themes: list,
) -> list:
    """Generate pre-computed synthesis cache entries for the dashboard."""
    cache_entries = []
    now = datetime.now(timezone.utc).isoformat()

    # 1. Theme frequency by source
    theme_freq_by_source = {}
    cat_to_theme = {
        cat: defn["theme_name"]
        for cat, defn in THEME_DEFINITIONS.items()
    }
    for raw, cr in zip(raw_reviews, classified_reviews):
        cat = cr["primary_complaint_category"]
        theme_name = cat_to_theme.get(cat)
        if theme_name:
            if theme_name not in theme_freq_by_source:
                theme_freq_by_source[theme_name] = {}
            src = raw["source"]
            theme_freq_by_source[theme_name][src] = (
                theme_freq_by_source[theme_name].get(src, 0) + 1
            )
    cache_entries.append({
        "cache_key": "theme_frequency_by_source",
        "data": theme_freq_by_source,
        "generated_at": now,
    })

    # 2. Theme frequency by segment
    theme_freq_by_seg = {}
    for cr in classified_reviews:
        cat = cr["primary_complaint_category"]
        theme_name = cat_to_theme.get(cat)
        seg = cr.get("user_segment_signal", "unclear")
        if theme_name:
            if theme_name not in theme_freq_by_seg:
                theme_freq_by_seg[theme_name] = {}
            theme_freq_by_seg[theme_name][seg] = (
                theme_freq_by_seg[theme_name].get(seg, 0) + 1
            )
    cache_entries.append({
        "cache_key": "theme_frequency_by_segment",
        "data": theme_freq_by_seg,
        "generated_at": now,
    })

    # 3. Top unmet needs
    need_counts = {}
    for cr in classified_reviews:
        need = cr.get("unmet_need")
        if need:
            need_counts[need] = need_counts.get(need, 0) + 1
    top_needs = sorted(need_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    cache_entries.append({
        "cache_key": "top_unmet_needs",
        "data": [{"need": n, "count": c} for n, c in top_needs],
        "generated_at": now,
    })

    # 4. Sentiment by source
    sentiment_by_src = {}
    for raw, cr in zip(raw_reviews, classified_reviews):
        src = raw["source"]
        sent = cr.get("sentiment", "neutral")
        if src not in sentiment_by_src:
            sentiment_by_src[src] = {}
        sentiment_by_src[src][sent] = sentiment_by_src[src].get(sent, 0) + 1
    cache_entries.append({
        "cache_key": "sentiment_by_source",
        "data": sentiment_by_src,
        "generated_at": now,
    })

    # 5. Segment distribution
    seg_dist = {}
    for cr in classified_reviews:
        seg = cr.get("user_segment_signal", "unclear")
        seg_dist[seg] = seg_dist.get(seg, 0) + 1
    cache_entries.append({
        "cache_key": "segment_distribution",
        "data": seg_dist,
        "generated_at": now,
    })

    # 6. Full dashboard summary
    source_counts = {}
    for raw in raw_reviews:
        src = raw["source"]
        source_counts[src] = source_counts.get(src, 0) + 1

    total_classified = sum(
        1 for cr in classified_reviews if not cr.get("classification_failed", False)
    )

    dashboard_summary = {
        "total_raw_reviews": len(raw_reviews),
        "total_classified_reviews": total_classified,
        "sources_active": len(source_counts),
        "source_counts": source_counts,
        "last_updated": now,
        "top_themes": [
            {
                "id": t["id"],
                "name": t["theme_name"],
                "description": t["theme_description"],
                "review_count": t["review_count"],
                "cross_source_count": t["cross_source_count"],
                "confidence_level": t["confidence_level"],
                "trend_direction": t["trend_direction"],
                "representative_quote": t["representative_quote"],
            }
            for t in sorted(themes, key=lambda x: x["review_count"], reverse=True)[:6]
        ],
        "top_unmet_needs": [{"need": n, "count": c} for n, c in top_needs],
        "segment_distribution": seg_dist,
        "sentiment_by_source": sentiment_by_src,
    }
    cache_entries.append({
        "cache_key": "dashboard_summary",
        "data": dashboard_summary,
        "generated_at": now,
    })

    return cache_entries


def generate_seed_data(count: int = 600) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate complete seed dataset.

    Returns dict with 'raw_reviews', 'classified_reviews', 'themes',
    'review_theme_mappings', and 'synthesis_cache' lists.

    Distribution:
    - ~25% algorithm_staleness (primary complaint)
    - ~15% genre_bubble
    - ~12% trust_erosion
    - ~10% mood_mismatch
    - ~10% choice_overload
    - ~8% interface_friction
    - ~7% lack_of_context
    - ~5% social_disconnect
    - ~5% no_complaint
    - ~3% other
    """
    distribution = {
        "algorithm_staleness": 0.25,
        "genre_bubble": 0.15,
        "trust_erosion": 0.12,
        "mood_mismatch": 0.10,
        "choice_overload": 0.10,
        "interface_friction": 0.08,
        "lack_of_context": 0.07,
        "social_disconnect": 0.05,
        "no_complaint": 0.05,
        "other": 0.03,
    }

    raw_reviews = []
    classified_reviews = []

    idx = 0
    for category, pct in distribution.items():
        cat_count = max(1, int(count * pct))
        for _ in range(cat_count):
            source = random.choice(SOURCES)
            raw = generate_raw_review(category, source, idx)
            classified = generate_classified_review(raw, category)
            # Carry source forward for theme generation
            classified["source_from_raw"] = source
            raw_reviews.append(raw)
            classified_reviews.append(classified)
            idx += 1

    # Shuffle to mix categories
    combined = list(zip(raw_reviews, classified_reviews))
    random.shuffle(combined)
    raw_reviews, classified_reviews = zip(*combined)
    raw_reviews = list(raw_reviews)
    classified_reviews = list(classified_reviews)

    # Generate themes and mappings from classified reviews
    themes, review_theme_mappings = generate_themes_and_mappings(classified_reviews)

    # Generate synthesis cache
    synthesis_cache = generate_synthesis_cache(raw_reviews, classified_reviews, themes)

    # Clean up temp field
    for cr in classified_reviews:
        cr.pop("source_from_raw", None)

    print(f"✅ Generated {len(raw_reviews)} raw reviews")
    print(f"✅ Generated {len(classified_reviews)} classified reviews")
    print(f"✅ Generated {len(themes)} themes")
    print(f"✅ Generated {len(review_theme_mappings)} review-theme mappings")
    print(f"✅ Generated {len(synthesis_cache)} synthesis cache entries")
    print(f"📊 Source distribution: {dict(sorted({r['source']: sum(1 for x in raw_reviews if x['source'] == r['source']) for r in raw_reviews}.items()))}")
    print(f"📊 Category distribution: {dict(sorted({c['primary_complaint_category']: sum(1 for x in classified_reviews if x['primary_complaint_category'] == c['primary_complaint_category']) for c in classified_reviews}.items()))}")

    return {
        "raw_reviews": raw_reviews,
        "classified_reviews": classified_reviews,
        "themes": themes,
        "review_theme_mappings": review_theme_mappings,
        "synthesis_cache": synthesis_cache,
    }


def save_seed_data(output_path: str = "seed_data.json", count: int = 600):
    """Generate and save seed data to a JSON file."""
    data = generate_seed_data(count)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"💾 Saved to {output_path}")
    return data


if __name__ == "__main__":
    save_seed_data()
