# Device notes

- Marketing name: X96 Max Plus Ultra
- Android product / board: `ohm`
- SoC family: Amlogic S905X4
- Tested Android generation: Android 11
- Live Android fingerprint: `Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys`
- Kernel: Linux `5.4.125`, arm64 kernel with 32-bit Android userspace (`armeabi-v7a`)
- Bootloader: `01.01.240531.211011`
- Boot layout: Android boot header v3, A/B; active slot `_a`; `boot_a` 64 MiB, `vendor_boot_a` 24 MiB, `dtbo_a` 2 MiB; no standalone `recovery` partition
- Dynamic storage: `super` 2.5 GB, `userdata` about 55.2 GiB; logical system/vendor/product/odm partitions
- Recovery entry: `adb reboot recovery`; normal `adb reboot` enters Android
- Tested base recovery: TWRP 3.6.1_11-0 from AM7 X4 package
- Android reports FBE filenames `aes-256-cts`; recovery log reports contents `aes-256-xts`. `/metadata/vold/metadata_encryption` is absent on the running system. TWRP's FBE decrypt still needs on-device verification.
- IR input is `ir_keypad` (vendor/product `0002:0002`) with native `REL_X/REL_Y`; USB receiver is XING WEI `4842:0001`.

Reference remote tables and key layouts are under `config/`. Vendor binaries and firmware images are not tracked.
