import os

from pytwitter import Api
from dotenv import load_dotenv

load_dotenv()

api = Api(
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_secret=os.getenv("ACCESS_SECRET")
)

api.create_tweet(text="Hello World")
