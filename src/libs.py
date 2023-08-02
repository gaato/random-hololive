import requests


USER_ID = 572432137035317249

class DiscordStream:
    def __init__(self, url):
        self.url = url

    def write(self, text):
        if 'ERROR' in text:
            content = f'<@!{USER_ID}>\n```diff\n- {text}\n```'
        elif 'WARNING' in text:
            content = f'```diff\n+ {text}\n```'
        else:
            content = f'```diff\n  {text}\n```'
        requests.post(self.url, json={'content': content})

    def read(self):
        pass
