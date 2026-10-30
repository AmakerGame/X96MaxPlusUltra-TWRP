# TWRP for X96 Max Plus Ultra (4/64)

**Language:** English · [Українська](docs/BUILD_UK.md) · [Русский](docs/BUILD_RU.md)

An unofficial recovery port for the **X96 Max Plus Ultra 4 GB RAM / 64 GB storage**, Amlogic S905X4, board `ohm`, running Android 11. Compatibility was checked against one device with this fingerprint:

```text
Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys
```

That device reports Linux `5.4.125`, bootloader `01.01.240531.211011`, A/B slots, and a 64 MiB `boot_a`. Other memory variants, board revisions, bootloaders, and Android builds have not been verified. The recovery is based on TWRP `3.6.1_11-0` from the AM7 X4 package; this is not an official Team Win build.

## Device and image status

A combined TWRP + Magisk 31.1 boot image was built and written to this device's active `boot_a` on 2026-10-30. Local image SHA-256: `ada7a8d030ebbba97c77d60eb97b2c48754f5bcebd92d68fa9c4fce4198341a7`; the partition readback hash matched exactly. The image is Android boot header v3 and 64 MiB. Its ramdisk contains the TWRP recovery startup files, both captured IR profiles, and Magisk's `.backup/.magisk` and `overlay.d` payloads.

After `adb reboot recovery`, Wi-Fi ADB went offline and disconnected. The recovery screen, Magisk SU after Android boot, and remote behavior therefore remain unverified on-device. The last known Android fingerprint is the one above. A full 64 MiB backup of the previously installed TWRP boot is available locally as `../boot_a_twrp_before_magisk.img` (SHA-256 `e3339615a8e4665482d065e5d89e0fcfdc9c06c70d10fd63eacbb7746b1bfd3a`). The original Magisk 31.1 boot backup is `dist/boot_a_magisk_restore.img` (SHA-256 `2d520b45aacd1e7218db904ca5b47527e0d881a1f1cc2fd9acaeda39affdb733`). Keep both off-device before further changes.

D-pad keys are left as native Linux key events, and the IR cursor scancodes are disabled. The captured up/down/left/right and OK events are mapped to `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, and `KEY_ENTER`; no helper turns them into pointer motion or clicks. This TWRP GUI does not provide general focus traversal for arrow keys, so full menu navigation needs GUI/framework changes and a source build. The current package only preserves the native key events; do not assume the D-pad can operate every screen.

## Known limitations

- The supplied recovery log reports `Unable to decrypt FBE device`. `/data` decryption and Keymaster/TEE compatibility remain unresolved. **Do not format Data to test this.**
- Partition mounting, backup/restore, ZIP installation, USB boot, D-pad behavior, and clock accuracy need separate on-device checks.
- The image is Android boot header v3, 64 MiB, and preserves the stock kernel. It does not rewrite `vendor_boot`, `dtbo`, `super`, or the bootloader.
- Before any write or wipe, back up personal files and the original `boot_a`. The detailed guides explain the recovery and data-loss implications.

## Guides

- [Detailed Ukrainian guide](docs/BUILD_UK.md) · [Temporary USB test (UA)](docs/USB_TEST_UK.md)
- [Подробная инструкция на русском](docs/BUILD_RU.md) · [Временный запуск USB (RU)](docs/USB_TEST_RU.md)
- [Device compatibility notes](docs/COMPATIBILITY.md)

## Build inputs and repository contents

Firmware images, TWRP binaries, vendor executables, device logs, and generated `.img` files are not tracked. The build script reassembles the tested AM7 X4 TWRP base with this device’s captured configuration; it does not compile the TWRP framework from source. A full source build needs a matching device tree and Linux build environment (WSL is not installed here). It reads local inputs from `input/` and writes outputs to `dist/`; both directories are ignored by Git. See the guides for the exact files and build procedure.

This project contains device-specific configuration samples and source changes. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md) for licensing details.
