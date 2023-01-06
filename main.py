import logging
from datetime import datetime
import environs

from my_github.db_session import create_session
from my_github.models import GitHubEvent
from my_github.github_api import GitHubAPI

env = environs.Env()
env.read_env(recurse=False)


DEBUG = env.bool('DEBUG', False)

session = create_session(
    env.str('DB_URL'),
    use_ssl=env.bool('DB_USE_SSL', True),
)
api = GitHubAPI(env.str('MY_GITHUB_USERNAME'), env.str('MY_GITHUB_TOKEN'))


def datetime_from_github_time(time_str):
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')


def save_github_events(raw_events):
    if not raw_events:
        return
    logging.debug(f'saving github events, count: { len(raw_events) }')
    for e in raw_events:
        session.merge(GitHubEvent(
            id=e['id'],
            event_type=e['type'],
            actor_id=e['actor']['id'],
            actor_login=e['actor']['login'],
            repo_id=e['repo']['id'],
            repo_name=e['repo']['name'],
            payload=e['payload'],
            public=e['public'],
            org_id=e['org']['id'] if 'org' in e else None,
            org_login=e['org']['login'] if 'org' in e else None,
            created_at=e['created_at']
        ))
    session.commit()


def main():
    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    oldest_event = session.query(GitHubEvent).order_by(GitHubEvent.created_at.asc()).first()
    logging.debug(f'Oldest event: { oldest_event.created_at }')

    page = 1

    if not oldest_event:
        logging.info('No events in the database(should be first call), start to fetch all events...')
        while True:
            raw_events = api.get_authenticated_user_events(page=page)
            if not raw_events:
                break
            save_github_events(raw_events)
            page += 1
        return

    while True:
        latest_event = session.query(GitHubEvent).order_by(GitHubEvent.created_at.desc()).first()
        raw_events = api.get_authenticated_user_events(page=1)
        if not raw_events:
            # No more events
            break

        if latest_event.created_at < datetime_from_github_time(raw_events[0]['created_at']):
            save_github_events(raw_events)

        if latest_event.created_at < datetime_from_github_time(raw_events[-1]['created_at']):
            # There are more events
            page += 1
        else:
            logging.debug(f'there are no more events, latest_event: { latest_event.created_at }')
            break


if __name__ == '__main__':
    main()
        