import requests


class DiscordStream:
    def __init__(self, url):
        self.url = url

    def write(self, text):
        if 'ERROR' in text:
            content = f'```diff\n- {text}\n```'
        elif 'WARNING' in text:
            content = f'```diff\n+ {text}\n```'
        else:
            content = f'```diff\n  {text}\n```'
        requests.post(self.url, json={'content': content})

    def read(self):
        pass
