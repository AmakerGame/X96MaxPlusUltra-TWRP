from __future__ import annotations

import gzip
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TWRP = ROOT / "input" / "twrp" / "twrp.img"
SOURCE_BOOT = ROOT / "input" / "stock" / "boot_a.img"
SOURCE_AUTOSCRIPT = ROOT / "input" / "twrp" / "aml_autoscript"
REMOTE_CAPTURE = ROOT / "input" / "vendor"
TEST_DIR = ROOT / "dist" / "usb-test"
sys.path.insert(0, str(ROOT / "scripts"))
from patch_theme import patch_theme_file


def align(value: int, page: int) -> int:
    return (value + page - 1) // page * page


def parse_newc(blob: bytes) -> list[tuple[bytes, bytes, bytes]]:
    records: list[tuple[bytes, bytes, bytes]] = []
    pos = 0
    while blob[pos : pos + 6] == b"070701":
        header = blob[pos : pos + 110]
        size = int(header[54:62], 16)
        name_size = int(header[94:102], 16)
        name_start = pos + 110
        name_end = name_start + name_size
        data_start = align(name_end, 4)
        data_end = data_start + size
        name_record = blob[name_start:name_end]
        data = blob[data_start:data_end]
        records.append((header, name_record, data))
        pos = align(data_end, 4)
        if name_record == b"TRAILER!!!\0":
            break
    if not records or records[-1][1] != b"TRAILER!!!\0":
        raise ValueError("newc archive has no trailer")
    return records


def pack_newc(records: list[tuple[bytes, bytes, bytes]]) -> bytes:
    out = bytearray()
    for old_header, name, data in records:
        header = bytearray(old_header)
        header[54:62] = f"{len(data):08x}".encode("ascii")
        header[94:102] = f"{len(name):08x}".encode("ascii")
        out.extend(header)
        out.extend(name)
        out.extend(b"\0" * ((-len(out)) % 4))
        out.extend(data)
        out.extend(b"\0" * ((-len(out)) % 4))
    return bytes(out)


def make_newc(name: str, data: bytes, mode: int, inode: int) -> tuple[bytes, bytes, bytes]:
    name_bytes = name.encode("utf-8") + b"\0"
    is_dir = mode & 0o170000 == 0o040000
    values = [inode, mode, 0, 0, 2 if is_dir else 1, 0, len(data), 0, 0, 0, 0, len(name_bytes), 0]
    header = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in values)
    return header, name_bytes, data


def patch_init(data: bytes) -> bytes:
    text = data.decode("utf-8").replace("\r\n", "\n")
    old_chmod = (
        "on init\n"
        "    chmod 0777 /bin/systemcontrol_static\n"
        "    chmod 0777 /sbin/remotecfg\n"
    )
    if old_chmod not in text:
        raise ValueError("expected AM7 X4 init chmod block was not found")
    text = text.replace(old_chmod, "", 1)
    # The archive does not contain this module. The target Android kernel also
    # exposes dwc_otg/xhci rather than a dwc3.ko module, so do not try to insmod
    # a nonexistent file from /boot during recovery startup.
    if "    insmod /boot/dwc3.ko\n" not in text:
        raise ValueError("expected stale dwc3 module command was not found")
    text = text.replace("    insmod /boot/dwc3.ko\n", "", 1)

    old_services = (
        "service remotecfg3 /sbin/remotecfg -c /sbin/remote.cfg -t /sbin/remote.tab3 -d\n"
        "    oneshot\n"
        "    seclabel u:r:recovery:s0\n\n"
        "service remotecfg1 /sbin/remotecfg -c /sbin/remote.cfg -t /sbin/remote.tab1 -d\n"
        "    oneshot\n"
        "    seclabel u:r:recovery:s0\n\n"
        "service remotecfg2 /sbin/remotecfg -c /sbin/remote.cfg -t /sbin/remote.tab2 -d\n"
        "    oneshot\n"
        "    seclabel u:r:recovery:s0\n\n"
        "service systemcontrol /vendor/bin/systemcontrol_static /vendor/etc/mesondisplay.cfg\n"
        "    oneshot\n"
        "    seclabel u:r:recovery:s0"
    )
    new_services = (
        "service remotecfg_fb04 /sbin/remotecfg -c /sbin/remote.cfg -t /sbin/remote.tab1\n"
        "    user root\n"
        "    group root\n"
        "    class main\n"
        "    oneshot\n"
        "    disabled\n"
        # Recovery's own SELinux policy contains the known-good recovery
        # domain; the Android vendor-only remotecfg domain is not in this
        # recovery policy and can prevent init from launching the service.
        "    seclabel u:r:recovery:s0\n\n"
        "service remotecfg_fe01 /sbin/remotecfg -c /sbin/remote.cfg -t /sbin/remote-tab2.tab\n"
        "    user root\n"
        "    group root\n"
        "    class main\n"
        "    oneshot\n"
        "    disabled\n"
        "    seclabel u:r:recovery:s0\n\n"
        "service system_control /vendor/bin/systemcontrol\n"
        "    user root\n"
        "    group system root media audio\n"
        "    interface vendor.amlogic.hardware.systemcontrol@1.0::ISystemControl default\n"
        "    interface vendor.amlogic.hardware.systemcontrol@1.1::ISystemControl default\n"
        "    class main\n"
        "    disabled\n"
        "    seclabel u:r:recovery:s0"
    )
    new_services += (
        "\n\nservice tvremote /sbin/tvremote\n"
        "    user root\n"
        "    group root input\n"
        "    class main\n"
        "    disabled\n"
        "    seclabel u:r:recovery:s0"
    )
    if old_services not in text:
        raise ValueError("expected AM7 X4 service block was not found")
    text = text.replace(old_services, new_services, 1)

    # Start the display HAL at the vendor's early-boot phase and use its
    # exact IR table after the recovery input devices have appeared.
    text = text.replace(
        "on boot\n    start vendor.keymaster-4-1\n",
        "on early-boot\n    start system_control\n\n"
        "on boot\n    start vendor.keymaster-4-1\n    start remotecfg_fb04\n"
        "    start remotecfg_fe01\n"
        "    start tvremote\n",
        1,
    )
    return text.encode("utf-8")


def patch_recovery_service(data: bytes) -> bytes:
    text = data.decode("utf-8").replace("\r\n", "\n")
    old_action = "on boot\n\n# For starting recovery on 5.0 and newer\n"
    new_action = (
        "on boot\n"
        "    setprop persist.sys.timezone Europe/Kiev\n"
        "    exec u:r:recovery:s0 root root -- /sbin/tvremote --set-time\n\n"
        "    start recovery\n\n"
        "# For starting recovery on 5.0 and newer\n"
    )
    if old_action not in text:
        raise ValueError("expected recovery service boot action was not found")
    text = text.replace(old_action, new_action, 1)
    old_service = (
        "service recovery /system/bin/recovery\n"
        "    socket recovery stream 422 system system\n"
        "    seclabel u:r:recovery:s0"
    )
    new_service = (
        "service recovery /system/bin/recovery\n"
        "    socket recovery stream 422 system system\n"
        "    setenv TZ Europe/Kiev\n"
        "    seclabel u:r:recovery:s0\n"
        "    disabled"
    )
    if old_service not in text:
        raise ValueError("expected recovery service definition was not found")
    return text.replace(old_service, new_service, 1).encode("utf-8")


def build_tvremote() -> Path:
    source = ROOT / "device" / "x96max_plus_ultra" / "src" / "tvremote.c"
    ndk_home = os.environ.get("ANDROID_NDK_HOME") or os.environ.get("ANDROID_NDK_ROOT")
    if ndk_home:
        ndk_dirs = [Path(ndk_home)]
    else:
        sdk_roots = [
            os.environ.get("ANDROID_SDK_ROOT"),
            os.environ.get("ANDROID_HOME"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Android", "Sdk"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
        ]
        ndk_dirs = sorted(
            ndk
            for sdk in sdk_roots
            if sdk
            for ndk in (Path(sdk) / "ndk").glob("*")
        )
    clangs = [
        d / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "clang.exe"
        for d in ndk_dirs
    ]
    clang = next((p for p in reversed(clangs) if p.is_file()), None)
    if clang is None:
        raise RuntimeError("Android NDK clang.exe not found; install NDK or set ANDROID_NDK_HOME")
    output = ROOT / "dist" / "tvremote"
    output.parent.mkdir(parents=True, exist_ok=True)
    compile_env = os.environ.copy()
    compile_env["TMP"] = str(output.parent)
    compile_env["TEMP"] = str(output.parent)
    subprocess.run(
        [str(clang), "--target=armv7a-linux-androideabi21", "-O2", "-Wall", "-Wextra",
         "-fPIE", "-pie", str(source), "-o", str(output)],
        check=True,
        env=compile_env,
    )
    return output


def patch_ramdisk(compressed: bytes, tvremote: Path) -> bytes:
    raw = gzip.decompress(compressed)
    records = parse_newc(raw)
    found: set[str] = set()
    patched: list[tuple[bytes, bytes, bytes]] = []
    for header, name, data in records:
        path = name[:-1].decode("utf-8", "replace")
        if path in {"ramdisk-files.txt", "ramdisk-files.sha256sum"}:
            # These are extraction-time inventories and become stale when the
            # ramdisk is tailored. They are not used at runtime.
            continue
        if path == "init.recovery.amlogic.rc":
            data = patch_init(data)
            found.add("init")
        elif path == "init.recovery.service.rc":
            data = patch_recovery_service(data)
            found.add("recovery_service")
        elif path == "system/etc/recovery.fstab":
            # The live device confirms all these by-name aliases and dynamic
            # logical partitions. Normalize misc to the alias verified on-device.
            old = b"/dev/block/platform/soc/fe08c000.mmc/by-name/misc"
            if old not in data:
                raise ValueError("expected misc fstab path was not found")
            data = data.replace(old, b"/dev/block/by-name/misc", 1)
            old_crypto = b"fileencryption=aes-256-xts,keydirectory=/metadata/vold/metadata_encryption"
            if old_crypto not in data:
                raise ValueError("expected generic /data encryption flags were not found")
            # Android reports aes-256-cts filenames, and the live metadata
            # partition has no vold/metadata_encryption key directory.
            data = data.replace(
                old_crypto,
                b"fileencryption=aes-256-xts:aes-256-cts:v2",
                1,
            )
            found.add("fstab")
        elif path == "twres/ui.xml" or path == "twres/landscape.xml" or path in {
            "twres/languages/en.xml",
            "twres/languages/ru.xml",
            "twres/languages/uk.xml",
        }:
            data = patch_theme_file(path, data)
        patched.append((header, name, data))
    if found != {"init", "recovery_service", "fstab"}:
        raise ValueError(f"did not find expected ramdisk files: {found}")

    # Embed the exact IR config, executable and Android key layouts read from
    # this box. This keeps the recovery independent of whether /vendor mounted.
    remote_files = {
        "sbin/tvremote": (tvremote, 0o100755),
        "sbin/remotecfg": (REMOTE_CAPTURE / "remotecfg", 0o100755),
        "sbin/remote.cfg": (REMOTE_CAPTURE / "remote.cfg", 0o100644),
        "sbin/remote.tab1": (REMOTE_CAPTURE / "remote.tab1", 0o100644),
        "sbin/remote-tab2.tab": (REMOTE_CAPTURE / "remote-tab2.tab", 0o100644),
        "system/usr/keylayout/Vendor_0002_Product_0002.kl": (
            REMOTE_CAPTURE / "Vendor_0002_Product_0002.kl", 0o100644
        ),
        "system/usr/keylayout/Vendor_4842_Product_0001.kl": (
            REMOTE_CAPTURE / "Vendor_4842_Product_0001.kl", 0o100644
        ),
        "vendor/usr/keylayout/Vendor_0002_Product_0002.kl": (
            REMOTE_CAPTURE / "Vendor_0002_Product_0002.kl", 0o100644
        ),
        "vendor/usr/keylayout/Vendor_4842_Product_0001.kl": (
            REMOTE_CAPTURE / "Vendor_4842_Product_0001.kl", 0o100644
        ),
    }
    existing = {name[:-1].decode("utf-8", "replace") for _, name, _ in patched}
    next_inode = max(int(header[6:14], 16) for header, _, _ in patched) + 1
    additions: list[tuple[bytes, bytes, bytes]] = []
    for dirname in ("system/usr", "system/usr/keylayout", "vendor/usr", "vendor/usr/keylayout"):
        if dirname not in existing:
            additions.append(make_newc(dirname, b"", 0o040755, next_inode))
            next_inode += 1
            existing.add(dirname)
    for name, (source, mode) in remote_files.items():
        if name in existing:
            raise ValueError(f"target ramdisk unexpectedly already contains {name}")
        if not source.is_file():
            raise FileNotFoundError(source)
        content = source.read_bytes()
        if name == "sbin/remote.cfg":
            if b"repeat_enable = 0" in content:
                content = content.replace(b"repeat_enable = 0", b"repeat_enable = 1", 1)
            elif b"repeat_enable = 1" not in content:
                raise ValueError("expected repeat_enable setting was not found in remote.cfg")
        elif name in {"sbin/remote.tab1", "sbin/remote-tab2.tab"}:
            # Preserve both live profiles read from this box. Their OK keys
            # arrive as KEY_ENTER, while the IR node is a native mouse; map
            # each profile's confirmed OK scancode to BTN_LEFT for TWRP.
            expected = {
                "sbin/remote.tab1": (b"custom_code = 0xfb04", b"0x5[cC]", "fb04/0x5c"),
                "sbin/remote-tab2.tab": (b"custom_code = 0xfe01", b"0x13", "fe01/0x13"),
            }
            marker, scan_re, label = expected[name]
            start = content.find(marker)
            if start < 0:
                raise ValueError(f"{name} does not contain the live {label.split('/')[0]} profile")
            end = content.find(b"key_end", start)
            if end < 0:
                raise ValueError(f"{name} profile has no key_end")
            section = content[start:end]
            pattern = rb"(?m)^([ \t]*" + scan_re + rb"[ \t]+)28([ \t]*(?:#.*)?\r?)$"
            section, count = re.subn(pattern, rb"\g<1>272\2", section)
            if count != 1:
                raise ValueError(f"could not remap {label} OK key to BTN_LEFT")
            content = content[:start] + section + content[end:]
        additions.append(make_newc(name, content, mode, next_inode))
        next_inode += 1
    patched[-1:-1] = additions
    return gzip.compress(pack_newc(patched), compresslevel=9, mtime=0)


def unpack_v0(image: bytes) -> tuple[bytearray, bytes, bytes, int]:
    if image[:8] != b"ANDROID!":
        raise ValueError("input is not an Android boot image")
    page = struct.unpack_from("<I", image, 36)[0]
    kernel_size = struct.unpack_from("<I", image, 8)[0]
    ramdisk_size = struct.unpack_from("<I", image, 16)[0]
    header_version = struct.unpack_from("<I", image, 40)[0]
    if header_version != 0:
        raise ValueError(f"expected legacy v0 temporary image, found v{header_version}")
    kernel_start = page
    ramdisk_start = page + align(kernel_size, page)
    header = bytearray(image[:page])
    kernel = image[kernel_start : kernel_start + kernel_size]
    ramdisk = image[ramdisk_start : ramdisk_start + ramdisk_size]
    return header, kernel, ramdisk, page


def pack_v0(header: bytearray, kernel: bytes, ramdisk: bytes, page: int) -> bytes:
    struct.pack_into("<I", header, 16, len(ramdisk))
    out = bytearray(header)
    out.extend(kernel)
    out.extend(b"\0" * (align(len(out), page) - len(out)))
    out.extend(ramdisk)
    out.extend(b"\0" * (align(len(out), page) - len(out)))
    return bytes(out)


def pack_v3(stock: bytes, ramdisk: bytes) -> bytes:
    if stock[:8] != b"ANDROID!" or struct.unpack_from("<I", stock, 40)[0] != 3:
        raise ValueError("boot_a.img is not Android boot v3")
    page = 4096
    kernel_size = struct.unpack_from("<I", stock, 8)[0]
    kernel_start = page
    kernel = stock[kernel_start : kernel_start + kernel_size]
    if len(kernel) != kernel_size:
        raise ValueError("truncated stock kernel")
    header = bytearray(stock[:page])
    struct.pack_into("<I", header, 12, len(ramdisk))
    out = bytearray(header)
    out.extend(kernel)
    out.extend(b"\0" * (align(len(out), page) - len(out)))
    out.extend(ramdisk)
    out.extend(b"\0" * (align(len(out), page) - len(out)))
    partition_size = len(stock)
    if len(out) > partition_size:
        raise ValueError("custom v3 boot image exceeds boot_a partition")
    out.extend(b"\0" * (partition_size - len(out)))
    return bytes(out)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    tvremote = build_tvremote()
    original_twrp = SOURCE_TWRP.read_bytes()
    old_header, old_kernel, old_ramdisk, page = unpack_v0(original_twrp)
    custom_ramdisk = patch_ramdisk(old_ramdisk, tvremote)
    temp_image = pack_v0(old_header, old_kernel, custom_ramdisk, page)

    TEST_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_DIR / "twrp.img").write_bytes(temp_image)
    shutil.copy2(SOURCE_AUTOSCRIPT, TEST_DIR / "aml_autoscript")
    (TEST_DIR / "README_UA.txt").write_text(
        "Тимчасовий тест TWRP для X96 Max Plus Ultra (Android 11 / S905X4)\n"
        "\n"
        "1. Відформатуй USB-флешку у FAT32.\n"
        "2. Скопіюй aml_autoscript і twrp.img з цієї папки в корінь флешки.\n"
        "3. Вимкни приставку, встав флешку та подай живлення.\n"
        "4. Одразу натисни RESET і утримуй приблизно 5–7 секунд.\n"
        "\n"
        "Точна ціль: X96 Max Plus Ultra 4/64, плата ohm, Android 11.\n"
        "Це тимчасовий USB-запуск; див. docs/USB_TEST_UK.md та docs/BUILD_UK.md.\n"
        "Не натискай Install, Wipe, Format Data або Restore під час першої перевірки.\n"
        "OK ІЧ-пульта переналаштовано для профілів fb04 і fe01, але роботу ще треба перевірити.\n"
        "Гіроскопічна/USB-миша є резервом; перевір час, розділи й керування.\n"
        "TWRP не підтверджено розшифровує FBE /data. Не форматуйте Data як тест.\n"
        "Цей комплект не записує boot_a автоматично.\n",
        encoding="utf-8",
    )

    stock_boot = SOURCE_BOOT.read_bytes()
    patched_boot = pack_v3(stock_boot, custom_ramdisk)
    (ROOT / "dist" / "boot_a_twrp_patched.img").write_bytes(patched_boot)

    print("temporary image:", len(temp_image), "bytes", sha(temp_image))
    print("patched boot_a:", len(patched_boot), "bytes", sha(patched_boot))
    print("stock boot kernel sha256:", sha(stock_boot[4096 : 4096 + struct.unpack_from('<I', stock_boot, 8)[0]]))
    print("temporary TWRP kernel sha256:", sha(old_kernel))


if __name__ == "__main__":
    main()
