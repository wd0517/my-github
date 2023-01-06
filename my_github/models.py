from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GitHubEvent(Base):
    __tablename__ = 'github_events'

    id = Column(BigInteger, primary_key=True)
    # https://docs.github.com/en/developers/webhooks-and-events/events/github-event-types
    # max length is 36
    event_type = Column(String(64), nullable=False)
    actor_id = Column(BigInteger, nullable=True)
    actor_login = Column(String(255), nullable=True)
    repo_id = Column(BigInteger, nullable=True)
    repo_name = Column(String(255), nullable=True)
    payload = Column(JSON, default=dict, nullable=True)
    public = Column(Boolean, default=False, nullable=True)
    org_id = Column(BigInteger, nullable=True)
    org_login = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)
