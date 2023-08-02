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


class YouTubeDataFetcher:
    def __init__(self) -> None:
        """Initializes the YouTubeDataFetcher."""
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY")
        )

    def get_videos_from_playlist(self, playlist_ids: list[str]) -> list[dict]:
        """
        Retrieves all videos from specified playlists.

        Args:
            playlist_ids: List of playlist IDs.

        Returns:
            List of videos (each video is a dictionary).
        """
        all_videos = []
        for playlist_id in playlist_ids:
            youtube_query = self.youtube.playlistItems().list(
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
                youtube_query = self.youtube.playlistItems().list_next(
                    youtube_query, youtube_response
                )
        return all_videos

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """
        Retrieves details of specified videos.

        Args:
            video_ids: List of video IDs.

        Returns:
            List of video details (each video detail is a dictionary).
        """
        youtube_query = self.youtube.videos().list(
            part="id,snippet,contentDetails,liveStreamingDetails",
            id=",".join(video_ids),
            maxResults=50,
        )
        try:
            youtube_response = youtube_query.execute()
        except Exception as e:
            logging.error(e)
            raise e
        return youtube_response["items"]


class TwitterPoster:
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        """
        Initializes the TwitterPoster.

        Args:
            consumer_key: The consumer key for the Twitter API.
            consumer_secret: The consumer secret for the Twitter API.
            access_token: The access token for the Twitter API.
            access_token_secret: The access token secret for the Twitter API.
        """
        try:
            self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            self.auth.set_access_token(access_token, access_token_secret)
            self.api = tweepy.API(self.auth)
            self.client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
        except Exception as e:
            logging.error(e)
            raise e

    def post_tweet(self, text: str, media_ids: list[str]) -> bool:
        """
        Posts a tweet with specified text and media IDs.

        Args:
            text: The text of the tweet.
            media_ids: List of media IDs to attach to the tweet.

        Returns:
            True if the tweet was posted successfully, False otherwise.
        """
        try:
            r = self.client.create_tweet(text=text, media_ids=media_ids)
        except Exception as e:
            logging.error(e)
            return False
        else:
            logging.info(f"Tweeted: {text}")
            return True


class RandomHololive:
    def __init__(self) -> None:
        """Initializes the YouTubeDataFetcher."""
        load_dotenv()
        self.youtube_fetcher = YouTubeDataFetcher()

    def load_env_and_args(self) -> None:
        """Loads environment variables and command-line arguments."""
        self.arg = sys.argv[1] if len(sys.argv) > 1 else None
        if self.arg is None:
            raise Exception("Please specify the argument.")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s :%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=DiscordStream(os.getenv("DISCORD_WEBHOOK_URL")),
        )

        match self.arg.lower():
            case "jp":
                self.playlist_ids = random.choice(HOLOLIVE_JP)
                self.consumer_key = os.getenv("JP_CONSUMER_KEY")
                self.consumer_secret = os.getenv("JP_CONSUMER_SECRET")
                self.access_token = os.getenv("JP_ACCESS_TOKEN")
                self.access_token_secret = os.getenv("JP_ACCESS_SECRET")
            case "id":
                self.playlist_ids = random.choice(HOLOLIVE_ID)
                self.consumer_key = os.getenv("ID_CONSUMER_KEY")
                self.consumer_secret = os.getenv("ID_CONSUMER_SECRET")
                self.access_token = os.getenv("ID_ACCESS_TOKEN")
                self.access_token_secret = os.getenv("ID_ACCESS_SECRET")
            case "en":
                self.playlist_ids = random.choice(HOLOLIVE_EN)
                self.consumer_key = os.getenv("EN_CONSUMER_KEY")
                self.consumer_secret = os.getenv("EN_CONSUMER_SECRET")
                self.access_token = os.getenv("EN_ACCESS_TOKEN")
                self.access_token_secret = os.getenv("EN_ACCESS_SECRET")
            case _:
                raise Exception("Please specify the argument.")

        self.twitter_poster = TwitterPoster(
            self.consumer_key,
            self.consumer_secret,
            self.access_token,
            self.access_token_secret,
        )

    def sample_videos(self) -> None:
        """Samples videos."""
        logging.info(f"Playlist: {self.playlist_ids}")
        all_videos = self.youtube_fetcher.get_videos_from_playlist(self.playlist_ids)
        logging.info(f"Total: {len(all_videos)}")
        sampled_videos = random.sample(all_videos, min(len(all_videos), 50))
        video_ids = [
            video["snippet"]["resourceId"]["videoId"] for video in sampled_videos
        ]
        videos = self.youtube_fetcher.get_video_details(video_ids)
        filtered_videos = [
            video
            for video in videos
            if isodate.parse_duration(video["contentDetails"]["duration"])
            >= isodate.parse_duration("PT30M")
        ]
        if len(filtered_videos) == 0:
            logging.warning("No videos longer than 30 minutes.")
            self.video = random.choice(videos)
        else:
            self.video = random.choice(filtered_videos)
        logging.info(f"Selected: {self.video['snippet']['title']}")

    def run(self) -> None:
        """Executes the whole process from sampling to tweeting."""
        self.load_env_and_args()
        self.sample_videos()

        # Upload thumbnail image
        try:
            thumbnail_url = self.video["snippet"]["thumbnails"]["maxres"]["url"]
            with requests.get(thumbnail_url) as r:
                media = self.twitter_poster.api.media_upload(
                    filename="thumbnail.jpg", file=io.BytesIO(r.content)
                )
        except Exception as e:
            logging.error(e)
            raise e

        # Create tweet
        if "liveStreamingDetails" not in self.video.keys():
            tweet = (
                f'{self.video["snippet"]["title"]}\n'
                f'{self.video["snippet"]["publishedAt"]}\n'
                f'https://youtu.be/{self.video["id"]}'
            )
        else:
            tweet = (
                f'{self.video["snippet"]["title"]}\n'
                f'{self.video["liveStreamingDetails"]["actualStartTime"]}\n'
                f'https://youtu.be/{self.video["id"]}'
            )

        # Post tweet
        self.twitter_poster.post_tweet(tweet, [media.media_id])


if __name__ == "__main__":
    rh = RandomHololive()
    rh.run()
