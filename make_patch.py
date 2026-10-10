#!/usr/bin/env python3
"""Build the replay-options fix and a local xdelta patch from an owned EXE."""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess

ORIGINAL_SHA256 = 'ecac1ea40bff26d529ec5852dbfdbe14a44ba0a4767985886a89bda09eb58a54'
FIXED_SHA256 = '26c0a2ff801c53f3932be69343c649a80f92fe9082cfe28479d8f7b46eb881a7'
HOOK, CAVE, ORIGINAL_CALLEE = 0x32B5D, 0x63510, 0x4CD02


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(original):
    if digest(original) != ORIGINAL_SHA256:
        raise ValueError('Unsupported WRMS.EXE: original SHA-256 does not match.')
    header = struct.unpack_from('<I', original, 0x3C)[0]
    u32 = lambda offset: struct.unpack_from('<I', original, header + offset)[0]
    pages, page_size, data_start = u32(0x14), u32(0x28), u32(0x80)
    fixup_offsets = header + u32(0x68)
    fixup_records = header + u32(0x6C)
    page_offsets = list(struct.unpack_from(f'<{pages + 1}I', original, fixup_offsets))
    old_end = fixup_records + page_offsets[-1]
    object_table = header + u32(0x40)
    code_size = struct.unpack_from('<I', original, object_table)[0]
    if original[HOOK:HOOK + 5] != bytes.fromhex('e8 a0 a1 01 00'):
        raise ValueError('Unexpected post-load instruction.')
    if code_size != 0x43907 or data_start != 0x1FC00:
        raise ValueError('Unexpected LE executable layout.')
    if set(original[data_start + code_size:CAVE + 32]) != {0}:
        raise ValueError('Expected code cave is not empty.')

    # Save EFLAGS/EAX, copy the loaded CFG option into runtime state, restore
    # both, then tail-call the original audio synchronizer.
    stub = bytearray(bytes.fromhex('9c 50 a1 ac 19 01 00 a3 c7 dc 00 00 58 9d e9'))
    stub += struct.pack('<i', ORIGINAL_CALLEE - (CAVE + len(stub) + 4))
    page = (CAVE - data_start) // page_size
    source = (CAVE - data_start) % page_size
    # Internal LE offset32 fixups: source operand offset, target object 2,
    # then target offset (32-bit for CFG option; 16-bit for runtime flag).
    added_fixups = (struct.pack('<BBhBI', 7, 0x10, source + 3, 2, 0x119AC)
                    + struct.pack('<BBhBH', 7, 0, source + 8, 2, 0xDCC7))
    insert_at = fixup_records + page_offsets[page + 1]
    growth = len(added_fixups)
    if set(original[old_end:data_start]) != {0} or data_start - old_end <= growth:
        raise ValueError('Insufficient zero padding for LE relocation records.')

    patched = bytearray(original)
    patched[insert_at:data_start] = added_fixups + original[insert_at:data_start - growth]
    for index in range(page + 1, len(page_offsets)):
        page_offsets[index] += growth
    struct.pack_into(f'<{pages + 1}I', patched, fixup_offsets, *page_offsets)
    for field in (0x30, 0x38):
        struct.pack_into('<I', patched, header + field, u32(field) + growth)
    for field in (0x70, 0x78):
        if header + u32(field) < insert_at:
            raise ValueError('Unexpected LE import-table location.')
        struct.pack_into('<I', patched, header + field, u32(field) + growth)
    struct.pack_into('<I', patched, object_table, CAVE - data_start + len(stub))
    patched[CAVE:CAVE + len(stub)] = stub
    patched[HOOK:HOOK + 5] = b'\xE8' + struct.pack('<i', CAVE - HOOK - 5)
    result = bytes(patched)
    if digest(result) != FIXED_SHA256:
        raise ValueError('Generated output hash differs from the verified build.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True,
                        help='Path to your own, unmodified BIN/WRMS.EXE')
    parser.add_argument('--out-dir', type=Path, default=Path('local-patch'),
                        help='Local output directory (never commit generated files)')
    parser.add_argument('--xdelta', type=Path, default=Path('xdelta3'),
                        help='Path to xdelta3 executable')
    args = parser.parse_args()
    original = args.exe.read_bytes()
    patched = build(original)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    fixed_exe = args.out_dir / 'WRMS.fixed.EXE'
    delta = args.out_dir / 'automatic-action-replay.xdelta'
    if fixed_exe.exists() or delta.exists():
        parser.error('Output already exists; choose an empty output directory.')
    fixed_exe.write_bytes(patched)
    try:
        subprocess.run([str(args.xdelta.resolve()), '-e', '-s', str(args.exe.resolve()),
                        str(fixed_exe.resolve()), str(delta.resolve())], check=True)
    except (OSError, subprocess.CalledProcessError):
        fixed_exe.unlink(missing_ok=True)
        raise
    print('Original SHA-256:', digest(original))
    print('Fixed EXE SHA-256:', digest(patched))
    print('Created local-only files:', fixed_exe, delta)
    print('Do not publish the executable or delta without confirming distribution rights.')


if __name__ == '__main__':
    main()