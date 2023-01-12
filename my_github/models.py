import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Boolean, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EventSourceEnum(enum.Enum):
    # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-events-for-the-authenticated-user
    USER_CREATED = 'user_created'
    # https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-events-received-by-the-authenticated-user
    USER_RECEIVED = 'user_received'

class GitHubEvent(Base):
    __tablename__ = 'github_events'

    id = Column(BigInteger, primary_key=True)
    # https://docs.github.com/en/developers/webhooks-and-events/events/github-event-types
    event_type = Column(String(64), nullable=False)
    actor_id = Column(BigInteger, nullable=True)
    actor_login = Column(String(255), nullable=True)
    repo_id = Column(BigInteger, nullable=True)
    repo_name = Column(String(255), nullable=True)
    payload = Column(JSON, default=dict, nullable=True)
    public = Column(Boolean, default=False, nullable=True)
    org_id = Column(BigInteger, nullable=True)
    org_login = Column(String(255), nullable=True)
    action = Column(String(255), nullable=True)
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    changed_files = Column(Integer, nullable=True)
    commit_sha = Column(String(64), nullable=True)
    pr_number = Column(
        String(255), nullable=True,
        doc='In PullRequestEvent, this is the pull request number; '
        'In PushEvent, it also may not null if the push is a merge.'
    )
    node_id = Column(
        String(255), nullable=True,
        doc='Is PullRequestEvent, it means the node_id of the pull request; '
        'In PushEvent, it means the node_id of the commit, and so on.'
    )
    event_source = Column(String(16), nullable=False, default=EventSourceEnum.USER_CREATED)
    created_at = Column(DateTime, nullable=True)


class GitHubRepo(Base):
    __tablename__ = 'github_repos'

    id = Column(BigInteger, primary_key=True)
    node_id = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    language = Column(JSON, default=list, nullable=True)
    star_count = Column(Integer, nullable=True)
    fork_count = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class GitHubUserStats(Base):
    __tablename__ = 'github_user_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=True)
    user_login = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    follower_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    starred_count = Column(
        Integer, nullable=True, doc='Number of repositories starred by the user'
    )
    repo_count = Column(
        Integer, nullable=True, doc='Total number of public and private repositories'
    )
    public_repo_count = Column(Integer, nullable=True)
    public_gist_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class GitHubUserDynamicStats(Base):
    __tablename__ = 'github_user_dynamic_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=True)
    user_login = Column(String(255), nullable=True)
    dimension = Column(String(255), nullable=True)
    int_value = Column(Integer, nullable=True)
    str_value = Column(String(255), nullable=True)
    json_value = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, nullable=True,  default=datetime.utcnow)
