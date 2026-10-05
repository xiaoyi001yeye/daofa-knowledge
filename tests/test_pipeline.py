import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.pdf = self.work / 'book.pdf'
        document = canvas.Canvas(str(self.pdf))
        document.drawString(50, 700, 'Evidence: consider other people objectively.')
        document.showPage()
        document.drawString(50, 700, 'More evidence: learning helps us grow.')
        document.save()
        self.output = self.work / 'pages'

    def command(self, script, *arguments, success=True):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / script), *map(str, arguments)],
            capture_output=True, text=True, encoding='utf-8',
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def prepare(self):
        return self.command('pdf_pages.py', 'prepare', '--pdf', self.pdf,
                            '--out', self.output, '--pages', '1')

    def test_review_preserves_correction_and_both_page_numbers_on_resume(self):
        self.prepare()
        manifest_file = self.output / 'manifest.json'
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        self.assertEqual(manifest['pages']['1']['review_status'], 'extracted')
        self.assertIsNone(manifest['pages']['1']['textbook_page'])
        correction = self.work / 'corrected.txt'
        correction.write_text('Evidence corrected after visual inspection.\nSecond checked line.\n', encoding='utf-8')
        self.command('pdf_pages.py', 'review', '--manifest', manifest_file,
                     '--page', '1', '--text', correction, '--textbook-page', '10',
                     '--reviewer', 'test reviewer', '--notes', 'Page image inspected.')
        self.prepare()
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        page = manifest['pages']['1']
        self.assertEqual(page['review_status'], 'reviewed')
        self.assertEqual(page['pdf_page'], 1)
        self.assertEqual(page['textbook_page'], '10')
        self.assertEqual((self.output / page['reviewed_text_file']).read_text(encoding='utf-8'),
                         'Evidence corrected after visual inspection.\nSecond checked line.\n')
        self.assertTrue((self.output / page['image_file']).is_file())

    def test_resume_does_not_erase_an_unresolved_visual_review(self):
        self.prepare()
        text = self.work / 'uncertain.txt'
        text.write_text('Uncertain character: [needs review].', encoding='utf-8')
        manifest = self.output / 'manifest.json'
        self.command('pdf_pages.py', 'review', '--manifest', manifest, '--page', '1',
                     '--text', text, '--reviewer', 'test reviewer', '--notes', 'Unclear character.',
                     '--needs-review')
        self.prepare()
        page = json.loads(manifest.read_text(encoding='utf-8'))['pages']['1']
        self.assertEqual(page['review_status'], 'needs_review')
        self.assertIn('Uncertain character', (self.output / page['reviewed_text_file']).read_text(encoding='utf-8'))

    def test_only_reviewed_evidence_can_be_published_and_searched_in_a_new_copy(self):
        self.prepare()
        manifest = self.output / 'manifest.json'
        cards = self.work / 'cards.json'
        cards.write_text(json.dumps({
            'book': '七年级上册', 'title': '第二课 正确认识自我',
            'unit': '第一单元 少年有梦', 'filename': '02_第二课_正确认识自我.md',
            'summary': 'Synthetic evidence fixture, not textbook content.',
            'points': [{'id': '7A-L02-K01', 'title': '对待他人评价', 'section': '认识自己',
                        'kind': '做法', 'content': '客观冷静地对待他人评价。',
                        'clues': ['他人评价', '不同评价'], 'question_patterns': ['怎么做'],
                        'sources': [{'pdf_page': 1, 'locator': 'Evidence:'}]}],
        }, ensure_ascii=False), encoding='utf-8')
        knowledge = self.work / 'knowledge'
        rejected = self.command('knowledge.py', 'compile', '--cards', cards,
                                '--manifest', manifest, '--knowledge', knowledge, success=False)
        self.assertIn('核对', rejected.stderr)
        reviewed = self.work / 'reviewed.txt'
        reviewed.write_text('Evidence: consider other people objectively.', encoding='utf-8')
        self.command('pdf_pages.py', 'review', '--manifest', manifest, '--page', '1',
                     '--text', reviewed, '--textbook-page', '10', '--reviewer', 'test reviewer',
                     '--notes', 'Fixture inspected.')
        self.command('knowledge.py', 'compile', '--cards', cards, '--manifest', manifest,
                     '--knowledge', knowledge)
        new_copy = self.work / 'new-copy' / 'knowledge'
        shutil.copytree(knowledge, new_copy)
        result = self.command('knowledge.py', 'search', '--knowledge', new_copy, '--query', '他人评价')
        hits = json.loads(result.stdout)
        self.assertEqual(hits['candidates'][0]['id'], '7A-L02-K01')
        self.assertEqual(hits['candidates'][0]['source_refs'][0]['textbook_page'], '10')
        absent = self.command('knowledge.py', 'search', '--knowledge', new_copy, '--query', '宪法监督机关')
        self.assertEqual(json.loads(absent.stdout)['status'], 'insufficient_evidence')
        published = next(new_copy.glob('*/*.md'))
        published.write_text(published.read_text(encoding='utf-8').replace(
            '<a id="7A-L02-K01"></a>', '<a id="broken_anchor"></a>'), encoding='utf-8')
        corrupted = self.command('knowledge.py', 'search', '--knowledge', new_copy,
                                 '--query', '他人评价', success=False)
        self.assertIn('格式已损坏', corrupted.stderr)

    def test_same_filename_with_changed_source_does_not_reuse_old_review(self):
        self.prepare()
        manifest_file = self.output / 'manifest.json'
        previous = manifest_file.read_bytes()
        changed = canvas.Canvas(str(self.pdf))
        changed.drawString(50, 700, 'Different edition, same file name.')
        changed.save()
        result = self.command('pdf_pages.py', 'prepare', '--pdf', self.pdf,
                              '--out', self.output, '--pages', '1', success=False)
        self.assertIn('教材内容已变化', result.stderr)
        self.assertEqual(manifest_file.read_bytes(), previous)

    def test_busy_workspace_refuses_parallel_writes_without_changing_manifest(self):
        self.prepare()
        manifest = self.output / 'manifest.json'
        previous = manifest.read_bytes()
        lock = self.output / '.pipeline.lock'
        lock.write_text('other process', encoding='utf-8')
        result = self.command('pdf_pages.py', 'prepare', '--pdf', self.pdf,
                              '--out', self.output, '--pages', '1', success=False)
        self.assertIn('正在提取或核对', result.stderr)
        self.assertEqual(manifest.read_bytes(), previous)
        self.assertTrue(lock.exists())

    def test_separate_page_batches_retain_previously_published_sources(self):
        knowledge = self.work / 'knowledge'
        for number in (1, 2):
            pages = self.work / f'batch-{number}'
            self.command('pdf_pages.py', 'prepare', '--pdf', self.pdf,
                         '--out', pages, '--pages', number)
            text = self.work / f'checked-{number}.txt'
            text.write_text('Verified evidence for this page.', encoding='utf-8')
            self.command('pdf_pages.py', 'review', '--manifest', pages / 'manifest.json',
                         '--page', number, '--text', text, '--textbook-page', number,
                         '--reviewer', 'test reviewer', '--notes', 'Fixture visually inspected.')
            card = self.work / f'cards-{number}.json'
            card.write_text(json.dumps({
                'book': '七年级上册', 'title': f'Lesson {number}', 'unit': 'Fixture',
                'filename': f'{number:02d}.md', 'points': [{
                    'id': f'7A-L{number:02d}-K01', 'title': f'Point {number}',
                    'section': 'Fixture', 'kind': '认识', 'content': '测试依据。',
                    'clues': ['测试依据'], 'question_patterns': ['是什么'],
                    'sources': [{'pdf_page': number, 'locator': 'Verified evidence'}],
                }],
            }, ensure_ascii=False), encoding='utf-8')
            self.command('knowledge.py', 'compile', '--cards', card,
                         '--manifest', pages / 'manifest.json', '--knowledge', knowledge)
        self.command('knowledge.py', 'build', '--knowledge', knowledge)
        result = self.command('knowledge.py', 'search', '--knowledge', knowledge, '--query', '测试依据')
        self.assertEqual({p['id'] for p in json.loads(result.stdout)['candidates']},
                         {'7A-L01-K01', '7A-L02-K01'})


if __name__ == '__main__':
    unittest.main()
