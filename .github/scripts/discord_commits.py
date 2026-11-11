"""One Discord message per non-merge commit newly added to main; never ping."""

import json
import os
from pathlib import Path
import re

from discord_release import github, readable_subject, send


def push_commits(before, after):
    for sha in (before, after):
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or sha == '0' * 40:
            raise ValueError('Expected existing full commit SHAs; refusing to replay repository history')
    commits = []
    page = 1
    while True:
        comparison = github(f'compare/{before}...{after}?per_page=100&page={page}')
        if comparison['status'] in ('identical', 'behind'):
            return []
        if comparison['status'] not in ('ahead', 'diverged'):
            raise RuntimeError('Unexpected comparison status')
        batch = comparison['commits']
        commits.extend(batch)
        if len(batch) < 100:
            return commits
        page += 1


def make_commit_payload(commit):
    subject = readable_subject(commit)
    if subject is None:
        return None
    author = (commit.get('author') or {}).get('login')
    author = author or commit['commit']['author']['name']
    return {
        'username': 'Prima · Перевод',
        'allowed_mentions': {'parse': []},
        'embeds': [{
            'title': f"Prima · main · {commit['sha'][:7]}",
            'url': commit['html_url'],
            'description': subject,
            'author': {'name': author[:256]},
            'color': 5793266,
            'timestamp': commit['commit']['committer']['date'],
            'footer': {'text': 'Коммит · изменения в основной ветке'},
        }],
    }


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    if os.environ['GITHUB_EVENT_NAME'] == 'push':
        if event.get('deleted') or event.get('ref') != 'refs/heads/main':
            print('Not an update to main; skipped')
            return
        before, after = event['before'], event['after']
    else:
        before, after = os.environ['BEFORE_SHA'], os.environ['AFTER_SHA']
    dry_run = os.environ.get('DRY_RUN', 'false').lower() == 'true'
    announced = 0
    for commit in push_commits(before, after):
        payload = make_commit_payload(commit)
        if payload is None:
            continue
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not dry_run:
            send(payload)
        announced += 1
    print(f"{'Previewed' if dry_run else 'Announced'} {announced} non-merge commit(s)")


if __name__ == '__main__':
    main()
