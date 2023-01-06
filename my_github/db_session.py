from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


def create_session(database_url: str, echo: bool = False, use_ssl: bool = False) -> Session:
    connect_args = {}
    if use_ssl:
        connect_args['ssl'] = {
            "ca": "/etc/ssl/cert.pem"
        }
    engine = create_engine(
        database_url,
        echo=echo, connect_args=connect_args
    )
    Session = sessionmaker(bind=engine)
    return Session()
