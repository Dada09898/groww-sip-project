"""Comments from Indian personal-finance videos about SIPs (needs YOUTUBE_API_KEY, free quota).
If YOUTUBE_VIDEO_IDS is empty, finds videos with YOUTUBE_SEARCH_QUERIES.
Search costs 100 quota units per query; the free daily quota is 10,000."""
import requests, pandas as pd
from config import (YOUTUBE_API_KEY, YOUTUBE_VIDEO_IDS, YOUTUBE_SEARCH_QUERIES,
                    YOUTUBE_VIDEOS_PER_QUERY)

API = "https://www.googleapis.com/youtube/v3"

def _search_videos():
    ids = []
    for q in YOUTUBE_SEARCH_QUERIES:
        js = requests.get(f"{API}/search", params={
            "part": "snippet", "q": q, "type": "video", "regionCode": "IN",
            "maxResults": YOUTUBE_VIDEOS_PER_QUERY, "order": "relevance", "key": YOUTUBE_API_KEY},
            timeout=20).json()
        if "error" in js:
            print("  youtube search error:", js["error"].get("message"))
            continue
        for it in js.get("items", []):
            vid = it["id"]["videoId"]
            if vid not in ids:
                ids.append(vid)
                print(f"  youtube: {vid}  {it['snippet']['title'][:70]}")
    return ids

def fetch(max_per_video=300):
    if not YOUTUBE_API_KEY:
        print("  youtube: skipped, add YOUTUBE_API_KEY to .env")
        return pd.DataFrame()
    vids = YOUTUBE_VIDEO_IDS or _search_videos()
    rows = []
    for vid in vids:
        token, got = None, 0
        while got < max_per_video:
            params = {"part": "snippet", "videoId": vid, "maxResults": 100,
                      "key": YOUTUBE_API_KEY, "textFormat": "plainText", "order": "relevance"}
            if token:
                params["pageToken"] = token
            js = requests.get(f"{API}/commentThreads", params=params, timeout=20).json()
            if "error" in js:   # comments disabled etc.
                break
            for it in js.get("items", []):
                s = it["snippet"]["topLevelComment"]["snippet"]
                rows.append({"source": "youtube", "id": f"yt_{it['id']}", "date": s["publishedAt"],
                             "rating": None, "text": s["textDisplay"],
                             "url": f"https://www.youtube.com/watch?v={vid}"})
                got += 1
            token = js.get("nextPageToken")
            if not token:
                break
    return pd.DataFrame(rows)
