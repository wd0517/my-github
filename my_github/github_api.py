import logging
import requests

class GitHubAPI:
    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.request_session = requests.Session()
        self.request_session.headers.update({
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        })
    
    def get_authenticated_user_events(self, page=1, per_page=100):
        # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-events-for-the-authenticated-user
        url = f'https://api.github.com/users/{ self.username }/events'
        response = self.request_session.get(url, params={
            'page': page,
            'per_page': per_page,
        })
        if response.status_code >= 500:
            logging.error(f'Error: { response.status_code }')
            return []
        elif response.status_code == 422:
            # There is no more events
            return []
        return response.json()
