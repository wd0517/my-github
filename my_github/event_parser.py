import enum

from datetime import datetime

class ACTION_ENUM(enum.Enum):
    OPENED = 'opened'
    CLOSED = 'closed'
    STARTED = 'started'
    PUBLISHED = 'published'
    CREATED = 'created'
    ADDED = 'added'


class EventParser:
    def __init__(self, raw_event):
        self.raw_event = raw_event
        self.event_dict = dict()
        self.transform()
    
    def transform(self):
        # implement in subclass
        e = self.raw_event
        self.event_dict = {
            'id': e['id'],
            'event_type': e['type'],
            'actor_id': e['actor']['id'],
            'actor_login': e['actor']['login'],
            'repo_id': e['repo']['id'],
            'repo_name': e['repo']['name'],
            'payload': e['payload'],
            'public': e['public'],
            'org_id': e['org']['id'] if 'org' in e else None,
            'org_login': e['org']['login'] if 'org' in e else None,
            'action': e['payload'].get('action'),
            'created_at': datetime.strptime(e['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        }
        transform_method = f'transform_{ e["type"] }'.lower()
        if hasattr(self, transform_method):
            e = getattr(self, transform_method)()
            self.event_dict.update(e)
    
    def transform_pushevent(self):
        self.event_dict['commit_sha'] = self.raw_event['payload']['head']
        return {}

    def transform_pullrequestevent(self):
        payload = self.raw_event['payload']
        pr_info = payload['pull_request']
        _e = {
            'pr_number': payload['number'],
            'node_id': pr_info['node_id'],
            'additions': pr_info['additions'],
            'deletions': pr_info['deletions'],
            'changed_files': pr_info['changed_files'],
        }
        if self.action == ACTION_ENUM.CLOSED:
            _e['commit_sha'] = pr_info['merge_commit_sha']
        return _e
    
    def transform_issuesevent(self):
        return {
            'node_id': self.raw_event['payload']['issue']['node_id'],
        }

    def transform_issuecommentevent(self):
        return {
            'node_id': self.raw_event['payload']['comment']['node_id'],
        }
    
    def transform_commitcommentevent(self):
        return {
            'node_id': self.raw_event['payload']['comment']['node_id'],
        }

    def __getattr__(self, name):
        try:
            return self.event_dict[name]
        except KeyError:
            raise AttributeError(f'No such attribute: { name }')
