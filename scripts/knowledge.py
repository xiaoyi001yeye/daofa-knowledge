"""Compile reviewed knowledge cards, validate provenance, and search Markdown."""
import argparse
import json
import re
import sys
from pathlib import Path

from pdf_pages import check_source, digest, local_file, read_json, write_json


MARKER = re.compile(r'<a id="([A-Za-z0-9-]+)"></a>\s*## ([^\n]+)\n\s*<!-- daofa: (.*?) -->\n', re.S)


def parse_markdown(text, relative):
    markers = list(MARKER.finditer(text))
    if text.count('<!-- daofa:') != len(markers):
        raise ValueError(f'{relative} 的知识点锚点、标题或元数据格式已损坏。')
    entries = []
    for i, marker in enumerate(markers):
        data = json.loads(marker.group(3))
        if data.get('id') != marker.group(1):
            raise ValueError(f'{relative} 的知识点编号与锚点不一致。')
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        entries.append({**data, 'title': marker.group(2).strip(), 'path': relative,
                        'anchor': marker.group(1), 'content': text[marker.end():end].strip()})
    return entries


def read_entries(root, excluding=None):
    entries = []
    for path in sorted(root.glob('*/*.md')):
        if excluding and path.resolve() == excluding.resolve():
            continue
        entries.extend(parse_markdown(path.read_text(encoding='utf-8-sig'), path.relative_to(root).as_posix()))
    return entries


def source_certificate(manifest):
    pages = {}
    for number, page in manifest['pages'].items():
        pages[number] = {key: page.get(key) for key in (
            'pdf_page', 'textbook_page', 'review_status', 'reviewed_by',
            'reviewed_text_sha256', 'reviewed_image_sha256')}
    return {key: manifest.get(key) for key in ('source_id', 'sha256', 'title', 'edition', 'page_count')} | {'pages': pages}


def source_registry(root, manifest=None):
    path = root / 'sources.json'
    data = read_json(path) if path.exists() else {'schema_version': 1, 'sources': {}}
    if manifest:
        incoming = source_certificate(manifest)
        existing = data['sources'].get(manifest['source_id'])
        if existing:
            if existing['sha256'] != incoming['sha256']:
                raise ValueError('来源编号对应的教材指纹不一致。')
            incoming['pages'] = {**existing['pages'], **incoming['pages']}
        data['sources'][manifest['source_id']] = incoming
    return data


def validate(entries, registry, private=None, private_root=None):
    ids, verified = set(), []
    for entry in entries:
        identity = entry.get('id', '')
        if not re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+', identity):
            raise ValueError('知识点需要稳定的字母、数字、连字符编号。')
        if identity in ids:
            raise ValueError(f'重复知识点编号：{identity}')
        ids.add(identity)
        if entry.get('status') != 'verified':
            continue
        if not entry.get('content', '').strip() or not entry.get('source_refs'):
            raise ValueError(f'{identity} 缺少知识正文或教材来源。')
        for ref in entry['source_refs']:
            source = registry['sources'].get(ref.get('source_id'))
            if not source or ref.get('sha256') != source.get('sha256'):
                raise ValueError(f'{identity} 的教材来源身份或指纹不匹配。')
            page = source['pages'].get(str(ref.get('pdf_page')))
            if not page or page.get('review_status') != 'reviewed':
                raise ValueError(f'{identity} 引用未核对的教材页面。')
            if not page.get('reviewed_by') or not page.get('reviewed_text_sha256'):
                raise ValueError(f'{identity} 缺少核对记录。')
            if ref.get('textbook_page') != page.get('textbook_page'):
                raise ValueError(f'{identity} 的教材页码与核对记录不一致。')
            if not ref.get('locator', '').strip():
                raise ValueError(f'{identity} 缺少核对文字定位提示。')
            if private and private['source_id'] == ref['source_id'] and str(ref['pdf_page']) in private['pages']:
                original = private['pages'][str(ref['pdf_page'])]
                checked = local_file(private_root, original['reviewed_text_file'])
                image = local_file(private_root, original['image_file'])
                if digest(checked) != original['reviewed_text_sha256'] or digest(image) != original['reviewed_image_sha256']:
                    raise ValueError(f'{identity} 的核对资料已变化，请重新核对。')
                if ref['locator'] not in checked.read_text(encoding='utf-8-sig'):
                    raise ValueError(f'{identity} 的定位文字不在核对文本中。')
        verified.append(entry)
    return verified


def write_indexes(root, entries, registry):
    root.mkdir(parents=True, exist_ok=True)
    write_json(root / 'sources.json', registry)
    write_json(root / '题眼索引.json', {'schema_version': 1, 'points': entries})
    lines = ['# 题眼索引', '', '> 由知识点生成；题眼用于找到候选，作答前阅读知识正文。', '',
             '| 题眼 | 问法 | 知识点 | 教材页码 |', '| --- | --- | --- | --- |']
    for entry in entries:
        clues = '、'.join(entry.get('clues', [])) or entry['title']
        questions = '、'.join(entry.get('question_patterns', []))
        pages = '、'.join(dict.fromkeys(str(r['textbook_page']) for r in entry['source_refs']))
        link = entry['path'].replace(' ', '%20') + '#' + entry['anchor']
        cells = [clues, questions, f'[{entry["title"]}]({link})', pages]
        lines.append('| ' + ' | '.join(str(c).replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
    (root / '题眼索引.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def compile_cards(args):
    cards = read_json(args.cards)
    manifest = read_json(args.manifest)
    check_source(manifest)
    root, private_root = args.knowledge.resolve(), args.manifest.resolve().parent
    book, filename = cards['book'], cards['filename']
    for part in (book, filename):
        if not part or part in ('.', '..') or any(c in part for c in '/\\\n\r'):
            raise ValueError('册次与课文件名只能是单个目录名/文件名。')
    if not filename.endswith('.md') or not cards.get('points'):
        raise ValueError('课文件必须是 Markdown，并包含知识点。')
    destination = root / book / filename
    lines = ['---', f'title: {cards["title"]}', f'unit: {cards["unit"]}', 'status: verified', '---', '',
             '# ' + cards['title'], '', '> 本课知识已逐页对照教材核对；表达为结构化整理。', '',
             '## 本课主旨', '', cards.get('summary', ''), '']
    for card in cards['points']:
        refs = []
        for requested in card['sources']:
            page = manifest['pages'].get(str(requested['pdf_page']))
            if not page or page['review_status'] != 'reviewed':
                raise ValueError(f'{card["id"]} 引用未核对的教材页面。')
            refs.append({'source_id': manifest['source_id'], 'sha256': manifest['sha256'],
                         'pdf_page': page['pdf_page'], 'textbook_page': page['textbook_page'],
                         'locator': requested['locator']})
        meta = {key: card[key] for key in ('id', 'section', 'kind', 'clues', 'question_patterns')}
        meta.update({'status': 'verified', 'lesson': cards['title'], 'unit': cards['unit'],
                     'book': book, 'grade': book[:-2], 'volume': book[-2:], 'source_refs': refs})
        lines.extend([f'<a id="{card["id"]}"></a>', '## ' + card['title'],
                      '<!-- daofa: ' + json.dumps(meta, ensure_ascii=False) + ' -->', '', card['content'], '',
                      '来源：' + '；'.join(f'教材第 {r["textbook_page"]} 页（PDF 第 {r["pdf_page"]} 页）' for r in refs) + '。', ''])
    rendered = '\n'.join(lines)
    new_entries = parse_markdown(rendered, destination.relative_to(root).as_posix())
    all_entries = read_entries(root, excluding=destination) + new_entries
    registry = source_registry(root, manifest)
    valid = validate(all_entries, registry, manifest, private_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding='utf-8')
    write_indexes(root, valid, registry)
    print(f'已生成 {cards["title"]}：{len(new_entries)} 个核对知识点；全库 {len(valid)} 个。')


def build(args):
    root = args.knowledge.resolve()
    if not root.is_dir():
        raise ValueError('找不到知识库目录。')
    manifest = read_json(args.manifest) if args.manifest else None
    if manifest:
        check_source(manifest)
    registry = source_registry(root, manifest)
    entries = validate(read_entries(root), registry, manifest, args.manifest.resolve().parent if manifest else None)
    write_indexes(root, entries, registry)
    print(f'校验通过：{len(entries)} 个核对知识点。')


def bigrams(text):
    compact = ''.join(re.findall(r'[\w]', text.lower()))
    return {compact[i:i+2] for i in range(len(compact) - 1)}


def search(args):
    root = args.knowledge.resolve()
    if not root.is_dir():
        raise ValueError('找不到知识库目录。')
    entries = validate(read_entries(root), source_registry(root))
    query = args.query.strip()
    if not query:
        raise ValueError('检索题目不能为空。')
    query_pairs, candidates = bigrams(query), []
    for entry in entries:
        phrases = entry.get('clues', []) + [entry['title']]
        exact = sum(8 for p in phrases if len(p) >= 2 and p in query)
        shared = len(query_pairs & bigrams(' '.join(phrases + [entry['content']])))
        score = exact + shared
        if score:
            candidates.append({**entry, 'score': score})
    candidates.sort(key=lambda item: (-item['score'], item['id']))
    print(json.dumps({'status': 'candidates' if candidates else 'insufficient_evidence',
                      'note': '候选匹配需结合设问核对适用性。' if candidates else '当前知识库依据不足。',
                      'candidates': candidates[:args.limit]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('compile', 'build', 'search'):
        sub = commands.add_parser(name)
        sub.add_argument('--knowledge', type=Path, default=Path('knowledge'))
        if name in ('compile', 'build'):
            sub.add_argument('--manifest', type=Path, required=name == 'compile')
        if name == 'compile':
            sub.add_argument('--cards', type=Path, required=True)
        if name == 'search':
            sub.add_argument('--query', required=True)
            sub.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    try:
        if args.command == 'compile':
            compile_cards(args)
        elif args.command == 'build':
            build(args)
        else:
            if not 1 <= args.limit <= 30:
                raise ValueError('候选数量必须在 1–30 范围内。')
            search(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'错误：{error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
