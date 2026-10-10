# Worms: Automatic Action Replay Fix

## Quick start — Git Bash, no Python

1. Copy your **original, unpatched** `WRMS.EXE` into this folder.
2. Download xdelta3 from the [official project](https://github.com/jmacd/xdelta)
   and put `xdelta3.exe` in this folder.
3. Make sure `automatic-action-replay.xdelta` is in this folder too.
4. Open Git Bash here and run:

   ```sh
   bash ./apply_patch.sh
   ```

The script checks the EXE version, applies the xdelta patch, saves the original
as `WRMS.EXE.orig`, then replaces `WRMS.EXE`. If validation fails, it leaves
the EXE unchanged. To undo, restore `WRMS.EXE.orig`. **Python is not needed to
apply the patch.**

## What this fixes

The game's **Automatic Action Replay** setting could be saved as OFF but was
turned ON again at startup by a separate runtime flag. This is not the distinct
**Action Tracking** option.

Only the exact original build is supported: SHA-256
`ecac1ea40bff26d529ec5852dbfdbe14a44ba0a4767985886a89bda09eb58a54`.
The fixed EXE hash is
`26c0a2ff801c53f3932be69343c649a80f92fe9082cfe28479d8f7b46eb881a7`.

## Patch file and rights

The patch file is not included in this source repository; obtain it separately
and place it beside the script. A delta may contain data derived from the game
executable. Confirm you have the right to obtain and use the delta under local
law and applicable licence terms. The game and its files remain the property
of their respective rights holders. This project is unofficial and provides
no legal advice. The included MIT license covers only this repository's
original source and documentation.

## Why disabling Automatic Action Replay at all?

The action replay feature is not a true replay of the previous game state, but rather a
replay of the input commands. The game does not restore the exact state of all objects, which can lead to inconsistencies. For example, worms that were alive before the replay may be dead afterward, or vice versa. This can be frustrating for players who expect the replay to accurately reflect the original game state. Disabling Automatic Action Replay helps to avoid these inconsistencies and ensures a more reliable gaming experience.