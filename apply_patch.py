#!/usr/bin/env python3
"""Apply a locally generated replay xdelta patch with hash checks and backup."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ORIGINAL = 'ecac1ea40bff26d529ec5852dbfdbe14a44ba0a4767985886a89bda09eb58a54'
FIXED = '26c0a2ff801c53f3932be69343c649a80f92fe9082cfe28479d8f7b46eb881a7'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True, help='Target WRMS.EXE')
    parser.add_argument('--delta', type=Path, required=True, help='Locally generated xdelta file')
    parser.add_argument('--xdelta', type=Path, default=Path('xdelta3'))
    args = parser.parse_args()
    target = args.exe.resolve()
    if sha256(target) != ORIGINAL:
        parser.error('Unsupported EXE version or already patched; target was not changed.')
    backup = target.with_name(target.name + '.replay-original.bak')
    if backup.exists():
        if sha256(backup) != ORIGINAL:
            parser.error('Existing backup does not match original; target was not changed.')
    else:
        with backup.open('xb') as stream:
            stream.write(target.read_bytes())
    handle, temporary_name = tempfile.mkstemp(prefix='worms-replay-', suffix='.exe',
                                               dir=target.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        subprocess.run([str(args.xdelta.resolve()), '-d', '-s', str(target),
                        str(args.delta.resolve()), str(temporary)], check=True)
        if sha256(temporary) != FIXED:
            parser.error('Delta output hash mismatch; target was not changed.')
        shutil.copymode(target, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print('Patched:', target)
    print('Original backup:', backup)
    print('Fixed SHA-256:', sha256(target))


if __name__ == '__main__':
    main()