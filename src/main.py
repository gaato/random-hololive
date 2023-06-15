import io
import logging
import os
import random
import sys

import googleapiclient.discovery
import isodate
import requests
import tweepy
from dotenv import load_dotenv

from playlist_ids import HOLOLIVE_EN, HOLOLIVE_ID, HOLOLIVE_JP
from libs import DiscordStream

load_dotenv()

arg = sys.argv[1] if len(sys.argv) > 1 else None
if arg is None:
    raise Exception("Please specify the argument.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=DiscordStream(os.getenv("DISCORD_WEBHOOK_URL")),
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
        try:
            youtube_response = youtube_query.execute()
        except Exception as e:
            logging.error(e)
            raise e
        all_videos += youtube_response["items"]
        youtube_query = youtube.playlistItems().list_next(
            youtube_query, youtube_response
        )

logging.info(f"Total: {len(all_videos)}")

sampled_videos = random.sample(all_videos, min(len(all_videos), 50))
youtube_query = youtube.videos().list(
    part="id,snippet,contentDetails,liveStreamingDetails",
    id=",".join([video["snippet"]["resourceId"]["videoId"] for video in sampled_videos]),
    maxResults=50,
)
try:
    youtube_response = youtube_query.execute()
except Exception as e:
    logging.error(e)
    raise e
filtered_videos = [
    video
    for video in youtube_response["items"]
    if isodate.parse_duration(video["contentDetails"]["duration"]) >= isodate.parse_duration("PT30M")
]
if len(filtered_videos) == 0:
    logging.warning("No videos longer than 30 minutes.")
    video = random.choice(youtube_response["items"])
video = random.choice(filtered_videos)
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

try:
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
except Exception as e:
    logging.error(e)
    raise e

# サムネイル画像をアップロード
try:
    thumbnail_url = video["snippet"]["thumbnails"]["maxres"]["url"]
    with requests.get(thumbnail_url) as r:
        media = api.media_upload(filename="thumbnail.jpg", file=io.BytesIO(r.content))
except Exception as e:
    logging.error(e)
    raise e

# ツイート
if "liveStreamingDetails" not in video.keys():
    tweet = f'{video["snippet"]["title"]}\n' \
        f'{video["snippet"]["publishedAt"]}\n' \
        f'https://youtu.be/{video["id"]}'
else:
    tweet = f'{video["snippet"]["title"]}\n' \
        f'{video["liveStreamingDetails"]["actualStartTime"]}\n' \
        f'https://youtu.be/{video["id"]}'

try:
    r = client.create_tweet(text=tweet, media_ids=[media.media_id])
except Exception as e:
    logging.error(e)
else:
    logging.info(f"Tweeted: {tweet}")
