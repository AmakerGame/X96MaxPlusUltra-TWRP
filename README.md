# TWRP for X96 Max Plus Ultra (4/64)

**Language:** English · [Українська](docs/BUILD_UK.md) · [Русский](docs/BUILD_RU.md)

An unofficial recovery port for the **X96 Max Plus Ultra 4 GB RAM / 64 GB storage**, Amlogic S905X4, board `ohm`, running Android 11. Compatibility was checked against one device with this fingerprint:

```text
Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys
```

That device reports Linux `5.4.125`, bootloader `01.01.240531.211011`, A/B slots, and a 64 MiB `boot_a`. Other memory variants, board revisions, bootloaders, and Android builds have not been verified. The recovery is based on TWRP `3.6.1_11-0` from the AM7 X4 package; this is not an official Team Win build.

## Device and image status

The image `boot_a_twrp_patched.img` with SHA-256 `e3339615a8e4665482d065e5d89e0fcfdc9c06c70d10fd63eacbb7746b1bfd3a` was written to the device's active `boot_a`. A full readback SHA-256 matched. `adb reboot recovery` was issued, but ADB became `offline` in recovery, so the latest screen and input behavior could not be independently verified.

The user reports that the remote's **OK button still does not work**. The image includes both captured IR profiles (`fb04` and `fe01`) with OK mapped to a mouse click, and starts `remotecfg` in the recovery SELinux context. This is a targeted fix, not a confirmed result. A gyroscope mouse remains the fallback. RTC clock synchronization is included but also needs on-screen confirmation.

## Known limitations

- The supplied recovery log reports `Unable to decrypt FBE device`. `/data` decryption and Keymaster/TEE compatibility remain unresolved. **Do not format Data to test this.**
- Partition mounting, backup/restore, ZIP installation, USB boot, remote clicks, and clock accuracy need separate on-device checks.
- The image is Android boot header v3, 64 MiB, and preserves the stock kernel. It does not rewrite `vendor_boot`, `dtbo`, `super`, or the bootloader.
- Before any write or wipe, back up personal files and the original `boot_a`. The detailed guides explain the recovery and data-loss implications.

## Guides

- [Detailed Ukrainian guide](docs/BUILD_UK.md) · [Temporary USB test (UA)](docs/USB_TEST_UK.md)
- [Подробная инструкция на русском](docs/BUILD_RU.md) · [Временный запуск USB (RU)](docs/USB_TEST_RU.md)
- [Device compatibility notes](docs/COMPATIBILITY.md)

## Build inputs and repository contents

Firmware images, TWRP binaries, vendor executables, device logs, and generated `.img` files are not tracked. The build script reads local inputs from `input/` and writes outputs to `dist/`; both directories are ignored by Git. See the guides for the exact files and build procedure.

This project contains device-specific configuration samples and source changes. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md) for licensing details.
