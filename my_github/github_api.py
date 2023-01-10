import logging
import requests
from datetime import datetime


class GitHubAPIException(Exception):
    pass


class GithubAPITimeout(GitHubAPIException):
    pass


class GitHubRestAPI:

    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.request_session = requests.Session()
        self.request_session.headers.update({
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        })

    def do_request(self, method, url, params=None, body=None):
        try:
            response = self.request_session.request(
                method=method, url=url, params=params, data=body,
                timeout=10
            )
        except requests.exceptions.Timeout:
            raise GithubAPITimeout('GitHub API timeout')

        return response

    def get_authenticated_user_created_events(self, page=1, per_page=100):
        # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-events-for-the-authenticated-user
        response = self.do_request(
            method='GET',
            url=f'https://api.github.com/users/{ self.username }/events',
            params={
                'page': page,
                'per_page': per_page
            }
        )
        if response.status_code >= 500:
            logging.error(f'Error: { response.status_code }')
            return []
        elif response.status_code == 422:
            # There is no more events
            return []
        return response.json()

    def get_authenticated_user_received_events(self, page=1, per_page=100):
        # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-events-for-the-authenticated-user
        response = self.do_request(
            method='GET',
            url=f'https://api.github.com/users/{ self.username }/received_events',
            params={
                'page': page,
                'per_page': per_page
            }
        )
        if response.status_code >= 500:
            logging.error(f'Error: { response.status_code }')
            return []
        elif response.status_code == 422:
            # There is no more events
            return []
        return response.json()

    def get_github_action_usage(self):
        # https://docs.github.com/en/rest/billing?apiVersion=2022-11-28#get-github-actions-billing-for-a-user
        response = self.do_request(
            method='GET',
            url=f'https://api.github.com/users/{ self.username }/settings/billing/actions'
        )
        return response.json()


def datetime_from_github_time(time_str):
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')


class GraphQLException(GitHubAPIException):
    pass


class GitHubGraphQLAPI:

    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.request_session = requests.Session()
        self.request_session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })

    def do_request(self, query, variables=None):
        # send graphql request to github
        try:
            response = self.request_session.post(
                'https://api.github.com/graphql',
                json={
                    'query': query,
                    'variables': variables
                },
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            raise GraphQLException(f'GitHub graphql request error: { e }')

        if response.status_code == 200:
            return response.json()

        raise GraphQLException(f'Github graphql error, status code: { response.status_code }')

    def get_user_stats(self):
        query = """
query {
  viewer {
    databaseId
    login
    followers {
      totalCount
    }
    following {
      totalCount
    }
    starredRepositories {
      totalCount
    }
    repos: repositories(ownerAffiliations: OWNER) {
      totalCount
    }
    publicRepos: repositories(ownerAffiliations: OWNER, privacy: PUBLIC) {
      totalCount
    }
    publicGists: gists(privacy: PUBLIC) {
      totalCount
    }
  }
}
        """
        return self.do_request(query=query, variables=None)['data']['viewer']
