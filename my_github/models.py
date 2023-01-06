import enum

from sqlalchemy import Column, String, DateTime, JSON, Boolean, BigInteger, Enum
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
    event_source = Column(String(16), nullable=False, default=EventSourceEnum.USER_CREATED)
    created_at = Column(DateTime, nullable=True)
