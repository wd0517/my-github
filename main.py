import sys
import logging
import argparse
import environs
from collections import defaultdict
from sqlalchemy import sql

from my_github.db_session import create_session
from my_github.models import (
    GitHubEvent, EventSourceEnum, GitHubUserStats,
    GitHubUserDynamicStats
)
from my_github.github_api import GitHubRestAPI, GitHubGraphQLAPI, datetime_from_github_time
from my_github.event_parser import EventParser

logger = logging.getLogger(__name__)


env = environs.Env()
env.read_env(recurse=False)


DEBUG = env.bool('DEBUG', False)

session = create_session(
    env.str('DB_URL'),
    use_ssl=env.bool('DB_USE_SSL', True),
    ssl_ca_path=env.str('DB_SSL_CA_PATH', '/etc/ssl/cert.pem'),
)
github_login = {
    'username': env.str('MY_GITHUB_USERNAME'),
    'token': env.str('MY_GITHUB_TOKEN')
}
rest_api = GitHubRestAPI(**github_login)
graphql_api = GitHubGraphQLAPI(**github_login)


def save_github_events(event_source, raw_events):
    if not raw_events:
        return
    logger.debug(f'saving github events')
    for e in raw_events:
        session.merge(GitHubEvent(
            **EventParser(e).event_dict,
            event_source=event_source,
        ))
    session.commit()


def _sync_github_events(event_source, github_api_method):
    oldest_event = session.query(GitHubEvent).where(
        GitHubEvent.event_source == event_source).order_by(GitHubEvent.created_at.asc()).first()
    logger.debug(f'Oldest event: { oldest_event.created_at if oldest_event else None }')

    page = 1

    if not oldest_event:
        logger.info('No events in the database(should be first call), start to fetch all events...')
        while True:
            raw_events = github_api_method(page=page)
            if not raw_events:
                break
            save_github_events(event_source, raw_events)
            page += 1
        return

    while True:
        latest_event = session.query(GitHubEvent).order_by(GitHubEvent.created_at.desc()).first()
        raw_events = github_api_method(page=1)
        if not raw_events:
            # No more events
            break

        if latest_event.created_at < datetime_from_github_time(raw_events[0]['created_at']):
            save_github_events(event_source, raw_events)

        if latest_event.created_at < datetime_from_github_time(raw_events[-1]['created_at']):
            # There are more events
            page += 1
        else:
            logger.debug(f'there are no more events, latest_event: { latest_event.created_at }')
            break


def _sync_commit_info_for_push_events():
    while True:
        push_events = session.query(
            GitHubEvent.id,
            GitHubEvent.repo_id,
            GitHubEvent.repo_name,
            GitHubEvent.commit_sha
        ).where(
            GitHubEvent.event_type == 'PushEvent',
            GitHubEvent.node_id == None,
            GitHubEvent.event_source == EventSourceEnum.USER_CREATED.value,
        ).all()[:50]
        if not push_events:
            break
        event_ids = []
        repo_commit_shas = defaultdict(lambda: defaultdict(list))
        for event_id, repo_id, repo_fullname, commit_sha in push_events:
            event_ids.append(event_id)
            repo_owner, repo_name = repo_fullname.split('/')
            repo_commit_shas[repo_id]['owner'] = repo_owner
            repo_commit_shas[repo_id]['name'] = repo_name
            repo_commit_shas[repo_id]['shas'].append(commit_sha)

        for commit in graphql_api.get_commits_by_shas(repo_commit_shas):
            session.query(GitHubEvent).where(
                GitHubEvent.event_type == 'PushEvent',
                GitHubEvent.commit_sha == commit['sha'],
                GitHubEvent.repo_id == commit['repo_id']
            ).update({
                'additions': commit['additions'],
                'deletions': commit['deletions'],
                'changed_files': commit['changed_files'],
                'node_id': commit['node_id']
            })
        session.commit()

    # associate commit with merged pr
    session.execute(sql.text("""
        update github_events e1 left join github_events e2
        on e1.commit_sha = e2.commit_sha and
            e1.event_type = 'PushEvent' and
            e2.event_type = 'PullRequestEvent' and
            e2.action = 'closed'
        set e1.pr_number = e2.pr_number
        where e2.id is not null
    """))
    session.commit()


def sync_user_created_events():
    logger.info('🚀 Syncing user created events...')
    _sync_github_events(
        EventSourceEnum.USER_CREATED.value,
        rest_api.get_authenticated_user_created_events,
    )
    _sync_commit_info_for_push_events()
    logger.info(f'🎉 Syncing user created events done! 🎉')


def sync_user_received_events():
    logger.info('🚀 Syncing user received events...')
    _sync_github_events(
        EventSourceEnum.USER_RECEIVED.value,
        rest_api.get_authenticated_user_received_events,
    )
    logger.info(f'🎉 Syncing user received events done! 🎉')


def sycn_user_stats():
    logger.info('🚀 Syncing user stats...')
    data = graphql_api.get_user_stats()
    user_id = data['databaseId']
    user_login = data['login']
    session.add(GitHubUserStats(
        user_id=user_id,
        user_login=user_login,
        company=data['company'],
        follower_count=data['followers']['totalCount'],
        following_count=data['following']['totalCount'],
        starred_count=data['starredRepositories']['totalCount'],
        repo_count=data['repos']['totalCount'],
        public_repo_count=data['publicRepos']['totalCount'],
        public_gist_count=data['publicGists']['totalCount'],
    ))
    session.commit()
    logger.info('🎉 Syncing user stats done! 🎉')


def sync_billing_stats():
    logger.info('🚀 Syncing billing stats...')
    data = rest_api.get_github_action_usage()
    session.add(GitHubUserDynamicStats(
        dimension='total_minutes_used',
        int_value=data['total_minutes_used']
    ))
    session.add(GitHubUserDynamicStats(
        dimension='total_paid_minutes_used',
        int_value=data['total_paid_minutes_used']
    ))
    session.add(GitHubUserDynamicStats(
        dimension='minutes_used_breakdown',
        json_value=data['minutes_used_breakdown']
    ))
    session.commit()
    logger.info('🎉 Syncing billing stats done! 🎉')


def main():
    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(prog='my_github events sync tools')
    parser.add_argument('--sync-user-created-events', action='store_true')
    parser.add_argument('--sync-user-received-events', action='store_true')
    parser.add_argument('--sync-user-stats', action='store_true')
    parser.add_argument('--sync-billing-stats', action='store_true')
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    args = parser.parse_args()

    if args.sync_user_created_events:
        sync_user_created_events()

    if args.sync_user_received_events:
        sync_user_received_events()

    if args.sync_user_stats:
        sycn_user_stats()

    if args.sync_billing_stats:
        sync_billing_stats()


if __name__ == '__main__':
    main()
