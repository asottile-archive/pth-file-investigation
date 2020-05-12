import argparse
import contextlib
import html.parser
import io
import multiprocessing.pool
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from typing import List
from typing import Optional
from typing import Tuple


class GetsLinks(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(
            self,
            tag: str,
            attrs: List[Tuple[str, Optional[str]]],
    ) -> None:
        href = next((v for k, v in attrs if k == 'href'), None)
        if tag == 'a' and href is not None:
            self.links.append(href)

    @classmethod
    def get_links(cls, contents: bytes) -> List[str]:
        inst = cls()
        inst.feed(contents.decode())
        return inst.links


def is_pth_filename(filename: str) -> bool:
    return filename.endswith('.pth') and not filename.endswith('nspkg.pth')


def process_link(s: str) -> Tuple[bool, str]:
    try:
        resp = urllib.request.urlopen(f'https://pypi.org{s}')
    except urllib.error.URLError:
        return False, s

    links = GetsLinks.get_links(resp.read())
    last_tgz: Optional[str] = None
    last_whl: Optional[str] = None
    for link in links:
        link, _, _ = link.partition('#')
        if link.endswith(('.tar.gz', '.tgz')):
            last_tgz = link
        elif link.endswith('.whl'):
            last_whl = link

    with contextlib.suppress(RuntimeError):  # what errors???
        if last_whl is not None:
            resp = urllib.request.urlopen(last_whl)
            bio = io.BytesIO(resp.read())
            with zipfile.ZipFile(bio) as zipf:
                for filename in zipf.namelist():
                    if is_pth_filename(filename):
                        return True, s

    with contextlib.suppress(tarfile.TarError):
        if last_tgz is not None:
            resp = urllib.request.urlopen(last_tgz)
            bio = io.BytesIO(resp.read())
            with tarfile.open(fileobj=bio) as tgz:
                setup_py_member = None
                for member in tgz.getmembers():
                    if is_pth_filename(member.name):
                        return True, s
                    elif member.name.endswith('/setup.py'):
                        setup_py_member = member
                if setup_py_member is not None:
                    setup_py_f = tgz.extractfile(setup_py_member)
                    assert setup_py_f
                    contents = setup_py_f.read()
                    if b'.pth' in contents:
                        return True, s

    return False, s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--continue-from')
    args = parser.parse_args()

    resp = urllib.request.urlopen('https://pypi.org/simple')
    links = GetsLinks.get_links(resp.read())
    if args.continue_from:
        links = links[links.index(args.continue_from) + 1:]
    with multiprocessing.Pool(8) as pool:
        i = 0
        for has_pth, link in pool.imap_unordered(
                process_link, links, chunksize=10,
        ):
            i += 1
            if has_pth:
                print(link)
            if i % 100 == 0:
                print(f'{i} / {len(links)}', file=sys.stderr)


if __name__ == '__main__':
    exit(main())
