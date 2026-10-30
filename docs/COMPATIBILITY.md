# Device compatibility notes

## Verified target

The attached box reports `Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys`, Linux `5.4.125`, active slot `_a`, boot header v3, and 64 MiB boot / 24 MiB vendor_boot / 2 MiB dtbo partitions. The output preserves the original boot kernel and boot header, and leaves vendor_boot and dtbo untouched.

The IR node is `ir_keypad` (`0002:0002`) and advertises native relative mouse axes. The live vendor table has profiles `0xfb04` and `0xfe01`; the `fb04` profile maps OK scancode `0x5c` and the `fe01` profile maps `0x13` to Linux key code 28 (`KEY_ENTER`), which does not click the native IR mouse in TWRP. The local recovery copy maps both confirmed OK scancodes to 272 (`BTN_LEFT`) and starts both vendor profiles. USB keyboard-style remotes continue through the DPAD-to-uinput helper. The two-profile revision with the remapped codes was installed to boot_a and its full readback SHA-256 matched. The user still reports that OK does not work. Inspection found that the Android vendor-only SELinux domain was assigned to the service, while the recovery ramdisk policy has no matching domain. The rebuilt service uses the original recovery SELinux context; that image was installed and its boot_a readback SHA-256 matched. The click fix remains unconfirmed because recovery ADB went offline after reboot and the display could not be inspected through ADB.

The live Android properties report `ro.crypto.volume.filenames_mode=aes-256-cts`; the recovery fstab now specifies `aes-256-xts:aes-256-cts:v2`. The live `/metadata/vold` directory has no `metadata_encryption` key directory, so the recovery fstab does not point to that absent path. FBE decryption remains unverified; the device's Keymaster/TEE interaction may need further work. Never format `/data` to test decryption.

## Upstream references

- [AOSP vendor boot partitions](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions) describes Android 11 boot header v3 and the separate vendor_boot/DTB payload. This build preserves the box's stock boot kernel and does not rewrite vendor_boot or dtbo.
- [AOSP metadata encryption](https://source.android.com/docs/security/features/encryption/metadata) documents the `/metadata` key directory and `keydirectory` fstab option. The path is used only when present and matching the actual on-device layout.
- [LineageOS ohm device tree](https://github.com/LineageOS/android_device_amlogic_ohm/blob/lineage-24.0/BoardConfig.mk) is a useful SoC reference, but its current tree targets a 5.15 kernel and `sc2_s905x4_ah212_drm`; this Android 11 retail image runs 5.4.125, so that newer kernel/device tree is not a drop-in recovery base.
- [TeamWin X96 Max u212 tree](https://github.com/TeamWin/android_device_amlogic_u212) targets S905X2, not this S905X4 Ultra.
