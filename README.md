pth-file-investigation
======================

Investigation into [bpo-33944](https://bugs.python.org/issue33944).

An attempt to collect information on all pypi packages that contain or write
`.pth` files as part of installation.

### `collect.py`

A script which scrapes pypi to collect information on packages.  Since I
didn't bother with proper retry logic or exception handling (in all cases)
there's a restart mechanism `--continue-from ...`.  The script produces
progress output on stderr and pypi paths on stdout.

Sample usage:

```bash
python3 collect.py | tee log
```

Or

```bash
python3 collect.py --continue-after /simple/foo | tee -a log
```

### what `collect.py` finds

`.pth` files here are defined as files ending in `.pth` but not `-nspkg.pth`.
`-nspkg.pth` files are for setuptools namespace packages and aren't
particularly interesting to this data collection.

- For each package listed on `pypi.org/simple` (probably don't load in a browser
or you'll be v sad).
    - find the latest `.whl`
        - search the list of files for a `.pth` file
    - find the latest `.tar.gz` / `.tgz`
        - search the list of files for a `.pth` file
        - search the bytes of `setup.py` for `b'.pth'`

### [`log`](./log)

A list of outputs I generated from the `170178` packages when I scraped on
2019-03-01
