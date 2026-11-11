import os
import unittest
from unittest.mock import patch

import discord_commits as notifier


def commit(subject='fix: опечатки', parents=1):
    return {
        'sha': 'b' * 40,
        'html_url': 'https://github.com/AngelicaProject/ProjectPrima/commit/' + 'b' * 40,
        'parents': [{}] * parents,
        'author': {'login': 'translator'},
        'commit': {'message': subject + '\n\nInternal notes',
                   'author': {'name': 'Translator Name'},
                   'committer': {'date': '2026-11-11T08:00:00Z'}},
    }


class CommitTests(unittest.TestCase):
    def test_original_subject_author_and_link(self):
        data = commit('Без конвенции: исправили название')
        payload = notifier.make_commit_payload(data)
        self.assertEqual(payload['embeds'][0]['description'], 'Без конвенции: исправили название')
        self.assertEqual(payload['embeds'][0]['author']['name'], 'translator')
        self.assertEqual(payload['embeds'][0]['url'], data['html_url'])

    def test_merge_skipped_but_merge_word_is_allowed(self):
        self.assertIsNone(notifier.make_commit_payload(commit(parents=2)))
        self.assertIsNotNone(notifier.make_commit_payload(commit('Merge terminology lists')))

    def test_commits_never_ping_even_with_release_role_configured(self):
        with patch.dict(os.environ, {'DISCORD_RELEASE_ROLE_ID': '1569985612352847902'}):
            payload = notifier.make_commit_payload(commit('@everyone <@&1569985612352847902>'))
        self.assertEqual(payload['allowed_mentions'], {'parse': []})
        self.assertNotIn('content', payload)
        self.assertNotIn('@everyone', payload['embeds'][0]['description'])

    def test_author_falls_back_to_git_name(self):
        data = commit()
        data['author'] = None
        self.assertEqual(notifier.make_commit_payload(data)['embeds'][0]['author']['name'], 'Translator Name')

    def test_all_push_commits_are_paginated_and_not_deduplicated(self):
        pages = [{'status': 'ahead', 'commits': [commit()] * 100},
                 {'status': 'ahead', 'commits': [commit()]}]
        with patch.object(notifier, 'github', side_effect=pages) as api:
            commits = notifier.push_commits('a' * 40, 'b' * 40)
        self.assertEqual(len(commits), 101)
        self.assertIn('page=2', api.call_args.args[0])

    def test_no_new_commits_on_rewind_and_no_initial_history_replay(self):
        with patch.object(notifier, 'github', return_value={'status': 'behind'}):
            self.assertEqual(notifier.push_commits('a' * 40, 'b' * 40), [])
        with self.assertRaises(ValueError):
            notifier.push_commits('0' * 40, 'b' * 40)


if __name__ == '__main__':
    unittest.main()
