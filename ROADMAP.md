# Roadmap

## Implemented in the current local/device image

- TV-oriented landscape theme and larger pointer
- Persistent Settings checkbox to hide/show Back, Home, and Console bar; hidden by default
- English, Ukrainian, and Russian labels
- Both captured IR profiles included; OK scancodes mapped to BTN_LEFT
- USB DPAD-to-pointer helper and RTC/timezone startup configuration
- boot_a v3 image rebuilt, installed, and full partition readback SHA-256 matched
- Detailed Ukrainian/Russian installation, backup, USB test, and FBE risk documentation

## Still needs on-device verification/fixes

- User reports IR OK still does not click; recovery ADB became unavailable after reboot, so collect fresh recovery.log/getevent output and verify which profile/service is active.
- Verify USB remote arrows/OK/Back, clock, display, partition mounts, backup/restore, and USB temporary boot.
- Investigate Android 11 FBE decryption with device Keymaster/TEE. Do not format Data to test.
- Retest TV layout at 1920x1080 and common overscan settings.
