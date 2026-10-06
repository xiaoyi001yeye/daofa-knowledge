"""Prepare local textbook pages and record explicit visual review."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def renderer_path(override=None):
    candidates = [override, shutil.which('pdftoppm'),
                  str(Path(sys.executable).parent.parent / 'native/poppler/Library/bin/pdftoppm.exe')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and Path(candidate).stat().st_size > 256:
            return str(candidate)
    raise ValueError('缺少 Poppler pdftoppm；请通过 --renderer 指定可用的程序。')


def page_numbers(value, count):
    numbers = set()
    for part in value.split(','):
        limits = part.split('-')
        if len(limits) > 2:
            raise ValueError('页序格式应为 17-23 或 17,18。')
        first, last = int(limits[0]), int(limits[-1])
        if first < 1 or last < first or last > count:
            raise ValueError(f'PDF 页序必须在 1–{count} 范围内。')
        numbers.update(range(first, last + 1))
    return sorted(numbers)


def local_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('页面记录引用了工作目录之外的文件。')
    return path


def check_source(manifest):
    source = Path(manifest['source_file'])
    if not source.is_file():
        raise ValueError('缺少本地教材 PDF，无法继续提取或核对。')
    if digest(source) != manifest['sha256']:
        raise ValueError('教材内容已变化；请为新来源使用独立工作目录，不沿用旧核对结果。')


@contextmanager
def workspace_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    path = root / '.pipeline.lock'
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError('该工作目录正在提取或核对，请等待完成后重试；异常退出后确认没有运行进程，再移除 .pipeline.lock。')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as lock:
            lock.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def prepare(args):
    from pypdf import PdfReader
    source = args.pdf.resolve()
    if not source.is_file():
        raise ValueError(f'找不到教材 PDF：{source}')
    source_hash = digest(source)
    out = args.out.resolve()
    manifest_path = out / 'manifest.json'
    reader = PdfReader(str(source))
    selected = page_numbers(args.pages, len(reader.pages))
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest['sha256'] != source_hash:
            raise ValueError('教材内容已变化；请为新来源使用独立工作目录，不沿用旧核对结果。')
        manifest['source_file'] = str(source)
    else:
        manifest = {'schema_version': 1, 'source_id': 'sha256-' + source_hash[:16],
                    'source_file': str(source), 'sha256': source_hash,
                    'title': args.title or source.stem, 'edition': None,
                    'page_count': len(reader.pages), 'pages': {}}
    renderer = renderer_path(args.renderer)
    out.mkdir(parents=True, exist_ok=True)
    for number in selected:
        key = str(number)
        existing = manifest['pages'].get(key)
        if existing and (existing['review_status'] in ('reviewed', 'extracted') or existing.get('reviewed_text_file')):
            required = ['image_file', 'raw_text_file']
            if existing.get('reviewed_text_file'):
                required.append('reviewed_text_file')
            if all(local_file(out, existing[field]).is_file() for field in required):
                if digest(local_file(out, existing['image_file'])) != existing['image_sha256']:
                    raise ValueError(f'PDF 第 {number} 页图像已变化；请重新检查工作资料。')
                if existing.get('reviewed_text_file') and digest(local_file(out, existing['reviewed_text_file'])) != existing['reviewed_text_sha256']:
                    raise ValueError(f'PDF 第 {number} 页核对文本已变化；请重新执行 review 记录修订。')
                print(f'保留 PDF 第 {number} 页：{existing["review_status"]}')
                continue
            if existing.get('reviewed_text_file'):
                raise ValueError(f'PDF 第 {number} 页核对资料缺失；保留原记录，请恢复资料。')
        prefix = out / f'page-{number:03d}'
        result = subprocess.run([renderer, '-f', key, '-l', key, '-r', str(args.dpi),
                                 '-singlefile', '-png', str(source), str(prefix)],
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError(f'页面渲染失败：{result.stderr.strip()}')
        image = prefix.with_suffix('.png')
        raw = prefix.with_suffix('.raw.txt')
        layout = prefix.with_suffix('.ocr.json')
        text = reader.pages[number - 1].extract_text() or ''
        method, status, notes = 'text', 'extracted', ''
        if not text.strip():
            if args.skip_ocr:
                method, status, notes = 'pending_ocr', 'needs_review', '扫描页尚未进行 OCR。'
            else:
                shell = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
                if not shell.is_file():
                    raise ValueError('当前扫描页需要 OCR；第一版需 Windows PowerShell 5.1，或用 --skip-ocr 保留页面供人工处理。')
                result = subprocess.run([str(shell), '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                         '-File', str(Path(__file__).with_name('windows_ocr.ps1')),
                                         '-ImagePath', str(image), '-OutputPath', str(layout)],
                                        capture_output=True)
                if result.returncode:
                    raise ValueError('Windows OCR 失败：' + result.stderr.decode('utf-8', errors='replace'))
                text = read_json(layout)['text']
                method = 'windows_ocr'
                if not text.strip():
                    status, notes = 'needs_review', 'OCR 未识别到文字，请对照页面处理。'
        raw.write_text(text, encoding='utf-8')
        manifest['pages'][key] = {'pdf_page': number, 'textbook_page': None,
                                 'image_file': image.name, 'image_sha256': digest(image),
                                 'raw_text_file': raw.name, 'layout_file': layout.name if layout.exists() else None,
                                 'method': method, 'review_status': status, 'reviewed_text_file': None,
                                 'reviewed_by': None, 'review_notes': notes, 'history': []}
        write_json(manifest_path, manifest)
        print(f'提取 PDF 第 {number} 页：{method}，{status}')


def review(args):
    path = args.manifest.resolve()
    manifest = read_json(path)
    check_source(manifest)
    root = path.parent
    page = manifest['pages'].get(str(args.page))
    if not page:
        raise ValueError('该 PDF 页面尚未提取。')
    if digest(local_file(root, page['image_file'])) != page['image_sha256']:
        raise ValueError('页面图像已变化，请重新核对来源。')
    text = args.text.read_text(encoding='utf-8-sig')
    if not text.strip() or not args.reviewer.strip() or not args.notes.strip():
        raise ValueError('核对文字、核对者和核对说明必须非空。')
    reviewed = root / f'page-{args.page:03d}.reviewed.txt'
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    # Keep immutable revisions as well as the current reviewed text.
    revision = root / 'revisions' / f'page-{args.page:03d}-{text_hash[:16]}.txt'
    revision.parent.mkdir(exist_ok=True)
    revision.write_text(text, encoding='utf-8', newline='\n')
    reviewed.write_text(text, encoding='utf-8', newline='\n')
    page.update({'textbook_page': args.textbook_page, 'reviewed_text_file': reviewed.name,
                 'reviewed_text_sha256': text_hash, 'reviewed_image_sha256': page['image_sha256'],
                 'review_status': 'needs_review' if args.needs_review else 'reviewed',
                 'reviewed_by': args.reviewer, 'review_notes': args.notes})
    page['history'].append({'at': datetime.now(timezone.utc).isoformat(), 'by': args.reviewer,
                            'status': page['review_status'], 'notes': args.notes,
                            'text_sha256': text_hash, 'revision_file': revision.relative_to(root).as_posix()})
    write_json(path, manifest)
    print(f'记录 PDF 第 {args.page} 页：{page["review_status"]}，教材页码 {args.textbook_page}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--pdf', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    prep.add_argument('--pages', required=True)
    prep.add_argument('--title')
    prep.add_argument('--dpi', type=int, default=180)
    prep.add_argument('--renderer')
    prep.add_argument('--skip-ocr', action='store_true')
    checked = commands.add_parser('review')
    checked.add_argument('--manifest', type=Path, required=True)
    checked.add_argument('--page', type=int, required=True)
    checked.add_argument('--text', type=Path, required=True)
    checked.add_argument('--textbook-page', default=None)
    checked.add_argument('--reviewer', required=True)
    checked.add_argument('--notes', required=True)
    checked.add_argument('--needs-review', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            if not 70 <= args.dpi <= 400:
                raise ValueError('dpi 必须在 70–400 范围内。')
            with workspace_lock(args.out.resolve()):
                prepare(args)
        else:
            with workspace_lock(args.manifest.resolve().parent):
                review(args)
    except (OSError, ValueError, KeyError, ImportError) as error:
        print(f'错误：{error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
