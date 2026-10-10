#!/usr/bin/env bash
set -euo pipefail

# Run from the folder containing WRMS.EXE, automatic-action-replay.xdelta,
# and preferably xdelta3 (or xdelta3.exe).
EXE="${EXE:-WRMS.EXE}"
DELTA="${DELTA:-automatic-action-replay.xdelta}"
BACKUP="${EXE}.orig"
TEMP="${EXE}.patching.$$"
ORIGINAL_SHA256="ecac1ea40bff26d529ec5852dbfdbe14a44ba0a4767985886a89bda09eb58a54"
FIXED_SHA256="26c0a2ff801c53f3932be69343c649a80f92fe9082cfe28479d8f7b46eb881a7"

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    fail 'Need sha256sum or shasum to verify the executable safely.'
  fi
}

if [[ ! -f "$EXE" ]]; then
  fail "Cannot find $EXE in the current directory."
fi
if [[ ! -f "$DELTA" ]]; then
  fail "Cannot find $DELTA in the current directory."
fi
if [[ -e "$TEMP" ]]; then
  fail "Temporary output already exists: $TEMP"
fi

if [[ -f ./xdelta3 ]]; then
  XDELTA=./xdelta3
elif [[ -f ./xdelta3.exe ]]; then
  XDELTA=./xdelta3.exe
elif command -v xdelta3 >/dev/null 2>&1; then
  XDELTA=xdelta3
elif command -v xdelta3.exe >/dev/null 2>&1; then
  XDELTA=xdelta3.exe
else
  fail 'Place xdelta3 or xdelta3.exe in this folder, or add it to PATH.'
fi

actual="$(sha256 "$EXE")"
[[ "$actual" == "$ORIGINAL_SHA256" ]] || fail \
  "WRMS.EXE is not the supported original (SHA-256: $actual). Restore your original EXE first."

if [[ -e "$BACKUP" ]]; then
  backup_hash="$(sha256 "$BACKUP")"
  [[ "$backup_hash" == "$ORIGINAL_SHA256" ]] || fail \
    "$BACKUP exists but is not the expected original; refusing to overwrite it."
fi

cleanup() {
  rm -f -- "$TEMP"
}
trap cleanup EXIT

printf 'Applying %s with %s...\n' "$DELTA" "$XDELTA"
"$XDELTA" -d -s "$EXE" "$DELTA" "$TEMP" || fail 'xdelta3 failed; WRMS.EXE was not changed.'

patched_hash="$(sha256 "$TEMP")"
[[ "$patched_hash" == "$FIXED_SHA256" ]] || fail \
  "Patched output SHA-256 did not match the verified result ($patched_hash). WRMS.EXE was not changed."

if [[ ! -e "$BACKUP" ]]; then
  cp -p -- "$EXE" "$BACKUP"
fi
mv -f -- "$TEMP" "$EXE"
trap - EXIT

printf 'Patch applied successfully.\n'
printf 'Original backup: %s\n' "$BACKUP"
printf 'Fixed SHA-256: %s\n' "$patched_hash"
