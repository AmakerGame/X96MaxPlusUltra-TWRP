# Roadmap

## Implemented in the current local/device image

- TV-oriented landscape theme and larger pointer
- Persistent Settings checkbox to hide/show Back, Home, and Console bar; hidden by default
- English, Ukrainian, and Russian labels
- Both captured IR profiles included with native D-pad and Enter key mapping; cursor mode disabled
- RTC/timezone startup configuration; no D-pad-to-pointer translation
- Combined TWRP + Magisk 31.1 boot_a v3 image rebuilt, installed, ramdisk inspected, and full partition readback SHA-256 matched
- Detailed Ukrainian/Russian installation, backup, USB test, and FBE risk documentation

## Still needs on-device verification/fixes

- Recovery ADB went offline after reboot, so confirm TWRP screen, D-pad/OK key behavior, and Magisk SU after Android boot.
- Full D-pad focus traversal needs TWRP GUI/framework support and a matching source build; current TWRP GUI does not provide generic arrow-key focus navigation.
- Verify clock, display, partition mounts, backup/restore, and USB temporary boot.
- Investigate Android 11 FBE decryption with device Keymaster/TEE. Do not format Data to test.
- Retest TV layout at 1920x1080 and common overscan settings.
