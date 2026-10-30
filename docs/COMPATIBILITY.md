# Device compatibility notes

## Verified target

The attached box reports `Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys`, Linux `5.4.125`, active slot `_a`, boot header v3, and 64 MiB boot / 24 MiB vendor_boot / 2 MiB dtbo partitions. The output preserves the original boot kernel and boot header, and leaves vendor_boot and dtbo untouched.

The IR node is `ir_keypad` (`0002:0002`). The captured profiles are `0xfb04` (OK scancode `0x5c`) and `0xfe01` (OK scancode `0x13`). The latest build disables the `fe01` cursor-mode scancodes and leaves the D-pad/OK mappings as Linux keys (`KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, `KEY_ENTER`). No helper translates these into pointer motion or clicks. The device's recovery log/photo shows Linux key events arriving, but the TWRP GUI does not implement general arrow-key focus traversal; full D-pad operation needs GUI/framework changes and a source build.

On 2026-10-30 the combined TWRP + Magisk 31.1 boot image was written to `boot_a`. File and partition readback SHA-256 matched: `ada7a8d030ebbba97c77d60eb97b2c48754f5bcebd92d68fa9c4fce4198341a7`. The 64 MiB v3 ramdisk was inspected and contains TWRP recovery init files, both IR profiles, and Magisk `.backup/.magisk` payload. Wi-Fi ADB disconnected after `adb reboot recovery`, so the recovery UI and subsequent Android Magisk SU have not been confirmed on-screen. The previous installed TWRP image backup is local as `../boot_a_twrp_before_magisk.img` (`e3339615a8e4665482d065e5d89e0fcfdc9c06c70d10fd63eacbb7746b1bfd3a`); original Magisk boot backup is `dist/boot_a_magisk_restore.img` (`2d520b45aacd1e7218db904ca5b47527e0d881a1f1cc2fd9acaeda39affdb733`).

The live Android properties report `ro.crypto.volume.filenames_mode=aes-256-cts`; the recovery fstab now specifies `aes-256-xts:aes-256-cts:v2`. The live `/metadata/vold` directory has no `metadata_encryption` key directory, so the recovery fstab does not point to that absent path. FBE decryption remains unverified; the device's Keymaster/TEE interaction may need further work. Never format `/data` to test decryption.

## Upstream references

- [AOSP vendor boot partitions](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions) describes Android 11 boot header v3 and the separate vendor_boot/DTB payload. This build preserves the box's stock boot kernel and does not rewrite vendor_boot or dtbo.
- [AOSP metadata encryption](https://source.android.com/docs/security/features/encryption/metadata) documents the `/metadata` key directory and `keydirectory` fstab option. The path is used only when present and matching the actual on-device layout.
- [LineageOS ohm device tree](https://github.com/LineageOS/android_device_amlogic_ohm/blob/lineage-24.0/BoardConfig.mk) is a useful SoC reference, but its current tree targets a 5.15 kernel and `sc2_s905x4_ah212_drm`; this Android 11 retail image runs 5.4.125, so that newer kernel/device tree is not a drop-in recovery base.
- [TeamWin X96 Max u212 tree](https://github.com/TeamWin/android_device_amlogic_u212) targets S905X2, not this S905X4 Ultra.
