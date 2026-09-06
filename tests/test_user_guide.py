"""The standalone guide preserves the authoritative content safely."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from html import escape
from html.parser import HTMLParser

from tools.build_user_guide import render_guide


def guide():
    return {'schema_version': 1, 'title': 'Studio help', 'articles': [
        {'id': 'first-steps', 'section': 'Getting started', 'title': 'Start here',
         'summary': 'Open your project.', 'status': 'Available',
         'steps': ['Choose a project.', 'Read the result.'], 'notes': ['Keep originals.'],
         'prompt': 'Please review my sources.'},
        {'id': 'review-output', 'section': 'Review', 'title': 'Review output',
         'summary': 'Inspect the result.', 'status': 'Requires a project',
         'steps': ['Play the output.'], 'notes': []}]}


class GuideTests(unittest.TestCase):
    def test_retains_every_article_field_and_anchor(self):
        data = guide()
        result = render_guide(data)
        for article in data['articles']:
            self.assertIn(f'<article id="{article["id"]}"', result)
            self.assertIn(f'href="#{article["id"]}"', result)
            for field in ('title', 'summary', 'section', 'status', 'prompt'):
                if field in article:
                    self.assertIn(escape(article[field], quote=True), result)
            for value in article['steps'] + article['notes']:
                self.assertIn(escape(value, quote=True), result)
        self.assertIn('<ol class="steps">', result)

    def test_article_ids_cannot_collide_with_ui_or_generated_ids(self):
        class Identifiers(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []

            def handle_starttag(self, tag, attrs):
                self.ids.extend(value for key, value in attrs if key == 'id')

        data = guide()
        for identifier in ('guide-search', 'guide-content', 'topics',
                           'topic-title-first-steps', 'example-first-steps'):
            article = copy.deepcopy(data['articles'][0])
            article['id'] = identifier
            data['articles'].append(article)
        parser = Identifiers()
        parser.feed(render_guide(data))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_escapes_all_source_text_including_attributes(self):
        data = guide()
        hostile = '\"><script>alert("x")</script>&\''
        data['title'] = hostile
        for field in ('section', 'title', 'summary', 'status', 'prompt'):
            data['articles'][0][field] = hostile
        data['articles'][0]['steps'] = [hostile]
        data['articles'][0]['notes'] = [hostile]
        result = render_guide(data)
        self.assertNotIn(hostile, result)
        self.assertNotIn('<script>alert', result)
        self.assertIn(escape(hostile, quote=True), result)

    def test_rejects_malformed_guides(self):
        invalid = [None, [], {}, {**guide(), 'schema_version': 2},
                   {**guide(), 'schema_version': True}, {**guide(), 'title': ' '},
                   {**guide(), 'articles': []}, {**guide(), 'articles': 'bad'}]
        for field, value in [('id', 'Bad ID'), ('id', 'a--b'), ('id', 'a\" onclick=\"x'),
                             ('section', ''), ('title', None), ('summary', []),
                             ('status', ' '), ('steps', []), ('steps', [' ']),
                             ('steps', 'bad'), ('notes', None), ('notes', [3]),
                             ('prompt', 3), ('prompt', '')]:
            data = guide()
            data['articles'][0][field] = value
            invalid.append(data)
        for field in ('id', 'section', 'title', 'summary', 'status', 'steps', 'notes'):
            data = guide()
            del data['articles'][0][field]
            invalid.append(data)
        duplicate = guide()
        duplicate['articles'].append(copy.deepcopy(duplicate['articles'][0]))
        invalid.append(duplicate)
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                render_guide(data)

    def test_accessible_search_copy_and_offline_print_support(self):
        result = render_guide(guide())
        for markup in ('for="guide_search"', 'type="search"', 'id="clear_search"',
                       'id="no_results"', 'aria-live="polite"', 'Copy example',
                       '@media print', 'article.hidden', 'textContent',
                       'aria-label="Topics by section"'):
            self.assertIn(markup, result)
        self.assertNotIn('src="http', result)
        self.assertNotIn('href="http', result)
        self.assertNotIn('innerHTML', result)


class AuthoritativeGuideTests(unittest.TestCase):
    def test_export_is_current_and_contains_all_authoritative_content(self):
        from tools.build_user_guide import ROOT
        source = json.loads((ROOT / 'docs/user-guide.json').read_text())
        expected = render_guide(source)
        self.assertEqual((ROOT / 'docs/how-to-use.html').read_text(), expected)
        for article in source['articles']:
            self.assertIn(f'<article id="{article["id"]}"', expected)
            for value in article['steps'] + article['notes']:
                self.assertIn(escape(value, quote=True), expected)

    def test_app_bundle_preserves_authoritative_guide_bytes(self):
        from tools.build_studio_app import ROOT, assemble
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            executable = directory / 'stub'
            executable.write_text('#!/bin/sh\nexit 0\n')
            executable.chmod(0o755)
            bundle = assemble(executable, ROOT, directory / 'Studio.app', sign=False)
            self.assertEqual(
                (bundle / 'Contents/Resources/user-guide.json').read_bytes(),
                (ROOT / 'docs/user-guide.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
