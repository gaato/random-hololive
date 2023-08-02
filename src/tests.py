import os
from dotenv import load_dotenv

# Assuming the refactored code is in a file named "main_refactored.py"
from main import RandomHololive


load_dotenv()

if __name__ == "__main__":
    rh = RandomHololive()
    rh.arg = "jp"
    rh.load_env_and_args()
    rh.sample_videos()

    # Create tweet
    if "liveStreamingDetails" not in rh.video.keys():
        tweet = (
            f'{rh.video["snippet"]["title"]}\n'
            f'{rh.video["snippet"]["publishedAt"]}\n'
            f'https://youtu.be/{rh.video["id"]}'
        )
    else:
        tweet = (
            f'{rh.video["snippet"]["title"]}\n'
            f'{rh.video["liveStreamingDetails"]["actualStartTime"]}\n'
            f'https://youtu.be/{rh.video["id"]}'
        )

    print(f"Generated tweet:\n{tweet}")
