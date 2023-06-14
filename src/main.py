import os
import io
import sys
import random
import logging

import googleapiclient.discovery
import tweepy
import requests
from dotenv import load_dotenv

from playlist_ids import HOLOLIVE_JP, HOLOLIVE_ID, HOLOLIVE_EN

load_dotenv()

arg = sys.argv[1] if len(sys.argv) > 0 else None
if arg is None:
    raise Exception("Please specify the argument.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

match arg.lower():
    case "jp":
        playlist_ids = random.choice(HOLOLIVE_JP)
    case "id":
        playlist_ids = random.choice(HOLOLIVE_ID)
    case "en":
        playlist_ids = random.choice(HOLOLIVE_EN)
    case _:
        raise Exception("Please specify the argument.")

logging.info(f"Playlist: {playlist_ids}")
all_videos = []

youtube = googleapiclient.discovery.build(
    "youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY")
)
for playlist_id in playlist_ids:
    # playlist 内の動画を全て videos に追加（ページング対応）
    youtube_query = youtube.playlistItems().list(
        part="snippet,status",
        playlistId=playlist_id,
        maxResults=50,
    )
    while youtube_query:
        youtube_response = youtube_query.execute()
        all_videos += youtube_response["items"]
        youtube_query = youtube.playlistItems().list_next(
            youtube_query, youtube_response
        )

logging.info(f"Total: {len(all_videos)}")

# 動画の中からランダムに選択（公開済みの配信アーカイブのみ）
# 配信アーカイブかどうかは youtube.videos().list() で取得できる liveStreamingDetails で判定
videos = random.sample(all_videos, min(len(all_videos), 50))
youtube_query = youtube.videos().list(
    part="id,snippet,liveStreamingDetails,status",
    id=",".join([video["snippet"]["resourceId"]["videoId"] for video in videos]),
    maxResults=50,
)
youtube_response = youtube_query.execute()
videos = [
    video
    for video in youtube_response["items"]
    if video["status"]["privacyStatus"] == "public" \
]
archives = [
    video
    for video in videos
    if "liveStreamingDetails" in video.keys() \
        and "activeLiveChatId" not in video["liveStreamingDetails"].keys()
]

if len(archives) == 0:
    video = random.choice(videos)
else:
    video = random.choice(archives)

logging.info(f"Selected: {video['snippet']['title']}")

match arg.lower():
    case "jp":
        consumer_key = os.getenv("JP_CONSUMER_KEY")
        consumer_secret = os.getenv("JP_CONSUMER_SECRET")
        access_token = os.getenv("JP_ACCESS_TOKEN")
        access_token_secret = os.getenv("JP_ACCESS_SECRET")
    case "id":
        consumer_key = os.getenv("ID_CONSUMER_KEY")
        consumer_secret = os.getenv("ID_CONSUMER_SECRET")
        access_token = os.getenv("ID_ACCESS_TOKEN")
        access_token_secret = os.getenv("ID_ACCESS_SECRET")
    case "en":
        consumer_key = os.getenv("EN_CONSUMER_KEY")
        consumer_secret = os.getenv("EN_CONSUMER_SECRET")
        access_token = os.getenv("EN_ACCESS_TOKEN")
        access_token_secret = os.getenv("EN_ACCESS_SECRET")
    case _:
        raise Exception("Please specify the argument.")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

# サムネイル画像をアップロード
thumbnail_url = video["snippet"]["thumbnails"]["maxres"]["url"]
with requests.get(thumbnail_url) as r:
    media = api.media_upload(filename="thumbnail.jpg", file=io.BytesIO(r.content))

# ツイート
if "liveStreamingDetails" not in video.keys():
    tweet = f'{video["snippet"]["title"]}\n{video["snippet"]["publishedAt"]}\nhttps://youtu.be/{video["id"]}'
else:
    tweet = f'{video["snippet"]["title"]}\n{video["liveStreamingDetails"]["actualStartTime"]}\nhttps://youtu.be/{video["id"]}'
r = client.create_tweet(text=tweet, media_ids=[media.media_id])
logging.info(f"Tweeted: {r}")
