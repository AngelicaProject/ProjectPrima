"""Announce Harmonia releases using commit subjects, without editing the release."""

import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request


def github(path):
    request = urllib.request.Request(
        f"{os.environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/"
        f"{os.environ['GITHUB_REPOSITORY']}/{path}",
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Prima-Release-Notifier",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def previous_release(current):
    candidates = []
    page = 1
    while True:
        batch = github(f"releases?per_page=100&page={page}")
        candidates.extend(
            release for release in batch
            if not release['draft']
            and release['tag_name'].startswith('harmonia/')
            and release['prerelease'] == current['prerelease']
            and release['tag_name'] != current['tag_name']
            and release['published_at'] < current['published_at']
        )
        if len(batch) < 100:
            break
        page += 1
    return max(candidates, key=lambda r: r['published_at'], default=None)


def compare(previous, current):
    base = urllib.parse.quote(previous['tag_name'], safe='')
    head = urllib.parse.quote(current['tag_name'], safe='')
    commits = []
    page = 1
    while True:
        comparison = github(f"compare/{base}...{head}?per_page=100&page={page}")
        if comparison['status'] not in ('ahead', 'identical'):
            raise RuntimeError('Release histories diverged; cannot determine release changes safely')
        batch = comparison['commits']
        commits.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return commits, comparison['html_url']


def readable_subject(commit):
    if len(commit.get('parents', [])) > 1:
        return None
    subject = commit['commit']['message'].splitlines()[0].strip()
    # Commit subjects are data: prevent formatting, links and mentions in the card.
    subject = subject.replace('@', '@\u200b')
    subject = re.sub(r'([\\`*_~<>\[\]|])', r'\\\1', subject)
    return subject[:240]


def make_payload(release, commits, comparison_url=None, previous=None, role_id=''):
    subjects = list(filter(None, map(readable_subject, commits)))
    lines = [f'• {subject}' for subject in subjects[:10]]
    if len(subjects) > 10:
        lines.append(f'…и ещё {len(subjects) - 10} изменений — по ссылке ниже.')
    if not lines:
        lines = ['• Опубликована новая сборка перевода.']
    description = ('Перевод обновляется автоматически через Harmonia.\n\n'
                   + '**Что изменилось:**\n' + '\n'.join(lines))
    fields = [{
        'name': 'Обновление перевода',
        'value': f"[Открыть релиз]({release['html_url']})",
    }]
    if comparison_url:
        fields.append({'name': 'Полный список изменений',
                       'value': f'[Смотреть на GitHub]({comparison_url})'})
    version = release['tag_name'].removeprefix('harmonia/')
    testing = ' · тестовая версия' if release['prerelease'] else ''
    footer = 'Автоматическая сводка по коммитам'
    if previous:
        footer += ' · с ' + previous['tag_name'].removeprefix('harmonia/')
    payload = {
        'username': 'Prima · Перевод',
        'allowed_mentions': {'parse': []},
        'embeds': [{
            'title': f'Новый релиз Prima · {version}{testing}'[:256],
            'url': release['html_url'],
            'description': description,
            'color': 15844367 if release['prerelease'] else 5763719,
            'fields': fields,
            'timestamp': release['published_at'],
            'footer': {'text': footer[:2048]},
        }],
    }
    if role_id:
        if not re.fullmatch(r'[0-9]{17,20}', role_id):
            raise ValueError('DISCORD_RELEASE_ROLE_ID must be a Discord role ID')
        payload['content'] = f'<@&{role_id}> — новый релиз Prima.'
        payload['allowed_mentions']['roles'] = [role_id]
    return payload


def send(payload):
    url = os.environ.get('DISCORD_WEBHOOK_URL', '').strip().rstrip('/')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'discord.com' or not re.fullmatch(
        r'/api/webhooks/\d+/[A-Za-z0-9_.-]+', parsed.path
    ):
        raise RuntimeError('DISCORD_WEBHOOK_URL is missing or invalid')
    request = urllib.request.Request(
        url + '?wait=true', data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Prima-Release-Notifier'},
        method='POST',
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                message = json.load(response)
            print(f"Discord message sent: {message['id']}")
            return
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 2:
                delay = float(json.loads(error.read()).get('retry_after', 2))
                time.sleep(min(max(delay, 1), 60))
                continue
            raise RuntimeError(f'Discord rejected the message (HTTP {error.code})') from None
        except urllib.error.URLError:
            # Never print the webhook URL/token in failure logs.
            raise RuntimeError('Could not reach Discord') from None


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    release = event.get('release')
    if release is None:
        tag = os.environ.get('RELEASE_TAG', '').strip()
        endpoint = 'releases/tags/' + urllib.parse.quote(tag, safe='') if tag else 'releases/latest'
        release = github(endpoint)
    if release['draft'] or not release['tag_name'].startswith('harmonia/'):
        raise RuntimeError('Only published harmonia/ releases can be announced')
    previous = previous_release(release)
    commits, comparison_url = compare(previous, release) if previous else ([], None)
    role_id = os.environ.get('DISCORD_RELEASE_ROLE_ID', '').strip()
    payload = make_payload(release, commits, comparison_url, previous, role_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if os.environ.get('DRY_RUN', 'false').lower() != 'true':
        send(payload)


if __name__ == '__main__':
    main()
