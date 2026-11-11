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
        self.assertEqual(notifier.readable_subject(commit('fix(Addon): сократить подсказки\n\nInternal notes')),
                         'fix(Addon): сократить подсказки')
        self.assertEqual(notifier.readable_subject(commit('Update to game version 2026.11.03')),
                         'Update to game version 2026.11.03')

    def test_all_non_merge_commits_are_kept_regardless_of_convention(self):
        for subject in ['ci: configure Discord', 'build: update tools',
                        'chore: maintenance', 'test: add coverage', 'docs: installation',
                        'Поправили название предмета', 'Merge terminology lists']:
            with self.subTest(subject=subject):
                self.assertEqual(notifier.readable_subject(commit(subject)), subject)

    def test_card_has_automatic_update_note_without_recurring_slogan(self):
        description = notifier.make_payload(self.release, [commit('Исправлены опечатки')])['embeds'][0]['description']
        self.assertTrue(description.startswith('**Что изменилось:**'))
        self.assertNotIn('Продолжаем вычитку', description)
        self.assertIn('Перевод обновляется автоматически через Harmonia.', description)

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

    def test_separate_commits_with_identical_subjects_are_kept(self):
        payload = notifier.make_payload(self.release, [commit('fix: опечатки')] * 3)
        self.assertEqual(payload['embeds'][0]['description'].count('fix: опечатки'), 3)

    def test_only_configured_role_can_be_pinged(self):
        role_id = '1569985612352847902'
        payload = notifier.make_payload(self.release, [commit('fix: @everyone')], role_id=role_id)
        self.assertEqual(payload['content'], f'<@&{role_id}> — новый релиз Prima.')
        self.assertEqual(payload['allowed_mentions'], {'parse': [], 'roles': [role_id]})

    def test_missing_or_invalid_role_configuration(self):
        self.assertNotIn('content', notifier.make_payload(self.release, []))
        with self.assertRaises(ValueError):
            notifier.make_payload(self.release, [], role_id='@everyone')

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
