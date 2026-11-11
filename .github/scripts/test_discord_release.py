import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('notifier', Path(__file__).with_name('discord_release.py'))
notifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notifier)


def commit(subject, parents=1):
    return {'commit': {'message': subject}, 'parents': [{}] * parents}


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.release = {
            'tag_name': 'harmonia/2026.11.10.0001', 'draft': False,
            'prerelease': False, 'published_at': '2026-11-10T08:18:24Z',
            'html_url': 'https://github.com/AngelicaProject/ProjectPrima/releases/tag/harmonia/2026.11.10.0001',
        }

    def test_readable_subjects_and_merge_filter(self):
        self.assertIsNone(notifier.readable_subject(commit('Merge pull request #48', 2)))
        self.assertIsNone(notifier.readable_subject(commit('ci: configure Discord')))
        self.assertEqual(notifier.readable_subject(commit('fix(Addon): сократить подсказки\n\nInternal notes')),
                         'Исправления (Addon): сократить подсказки')
        self.assertEqual(notifier.readable_subject(commit('Update to game version 2026.11.03')),
                         'Адаптация к версии игры 2026.11.03')

    def test_untrusted_subjects_and_discord_limits(self):
        commits = [commit(f'fix: @everyone [link](https://example.com) {i} ' + '*' * 300)
                   for i in range(20)]
        payload = notifier.make_payload(self.release, commits)
        embed = payload['embeds'][0]
        self.assertEqual(payload['allowed_mentions'], {'parse': []})
        self.assertNotIn('@everyone', embed['description'])
        self.assertNotIn('[link]', embed['description'])
        self.assertLessEqual(len(embed['description']), 4096)
        self.assertLess(len(str(payload)), 6000)

    def test_subjects_are_deduplicated(self):
        payload = notifier.make_payload(self.release, [commit('fix: опечатки')] * 3)
        self.assertEqual(payload['embeds'][0]['description'].count('опечатки'), 1)

    def test_previous_release_uses_same_channel_not_api_order(self):
        old = dict(self.release, tag_name='harmonia/2026.11.05.0001', published_at='2026-11-05T00:00:00Z')
        testing = dict(old, prerelease=True, published_at='2026-11-09T00:00:00Z')
        future = dict(old, tag_name='harmonia/2026.11.11.0001', published_at='2026-11-11T00:00:00Z')
        with patch.object(notifier, 'github', return_value=[future, testing, self.release, old]):
            self.assertEqual(notifier.previous_release(self.release), old)

    def test_compare_fetches_all_pages(self):
        pages = [dict(status='ahead', commits=[commit('fix: a')] * 100, html_url='compare-url'),
                 dict(status='ahead', commits=[commit('fix: b')], html_url='compare-url')]
        with patch.object(notifier, 'github', side_effect=pages) as api:
            commits, url = notifier.compare(self.release, self.release)
            self.assertEqual(len(commits), 101)
            self.assertEqual(url, 'compare-url')
            self.assertIn('page=2', api.call_args.args[0])

    def test_diverged_history_does_not_announce_wrong_changes(self):
        with patch.object(notifier, 'github', return_value={'status': 'diverged'}):
            with self.assertRaises(RuntimeError):
                notifier.compare(self.release, self.release)


if __name__ == '__main__':
    unittest.main()
