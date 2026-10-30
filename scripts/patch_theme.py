#!/usr/bin/env python3
"""Apply the X96 TV-friendly settings to an extracted TWRP theme."""

from __future__ import annotations

import re
from pathlib import Path


NAVBAR_CONDITION = '<condition var1="tw_hide_navbar" op="=" var2="0"/>'

TRANSLATIONS = {
    "en": "Hide bottom Back / Home / Console bar",
    "ru": "Скрыть нижнюю панель «Назад / Домой / Консоль»",
    "uk": "Приховати нижню панель «Назад / Головна / Консоль»",
}

RU_STRINGS = {
    "system": "Система", "system_image": "Образ системы",
    "vendor": "Раздел Vendor", "vendor_image": "Образ Vendor",
    "boot": "Раздел Boot", "recovery": "Режим восстановления",
    "cache": "Кэш", "data": "Данные", "android_secure": "Защищённые данные Android",
    "sdext": "Раздел SD-EXT", "adopted_data": "Данные адаптированного хранилища",
    "adopted_storage": "Адаптированное хранилище", "autostorage": "Хранилище",
    "adb_sideload_btn": "Установка через ADB", "rb_edl_btn": "Режим EDL",
    "adb_sideload_hdr": "Установка через ADB", "sideload_confirm": "Установка через ADB",
    "sideload": "ADB sideload", "ok_btn": "ОК", "fastboot_button": "Режим Fastboot",
    "tz_offset_0": "0", "tz_offset_15": "15", "tz_offset_30": "30", "tz_offset_45": "45",
    "dumlock_btn": "HTC Dumlock", "dumlock_hdr": "HTC Dumlock",
    "part_sd_m": "-", "part_sd_p": "+",
    "fm_chmod755_btn": "chmod 755", "fm_chmod755ing": "chmod 755", "fm_chmod_btn": "chmod",
    "twrp_header": "Team Win Recovery Project", "twrp_watch_header": "TWRP %tw_version%",
}

UK_STRINGS = {
    "system": "Система", "system_image": "Образ системи",
    "vendor": "Розділ Vendor", "vendor_image": "Образ Vendor",
    "boot": "Розділ Boot", "recovery": "Режим відновлення",
    "cache": "Кеш", "data": "Дані", "internal": "Внутрішнє сховище",
    "usbotg": "USB OTG", "android_secure": "Захищені дані Android",
    "dalvik": "Кеш Dalvik", "sdext": "Розділ SD-EXT",
    "adopted_data": "Дані адаптованого сховища", "adopted_storage": "Адаптоване сховище",
    "rb_edl_btn": "Режим EDL", "tz_offset_0": "0", "tz_offset_15": "15",
    "tz_offset_30": "30", "tz_offset_45": "45", "dumlock_btn": "HTC Dumlock",
    "dumlock_hdr": "HTC Dumlock", "part_sd_m": "-", "part_sd_p": "+",
    "fm_chmod755_btn": "chmod 755", "fm_chmod755ing": "chmod 755", "fm_chmod_btn": "chmod",
    "twrp_header": "Team Win Recovery Project", "twrp_watch_header": "TWRP %tw_version%",
    "auto_reflashtwrp_chk": "Автоматично повторно прошивати TWRP після встановлення ROM",
    "autostorage": "Сховище",
    "storage_hdr": "Сховище: %tw_storage_display_name% (%tw_storage_free_size% МБ)",
    "install_reboot": "Перезавантаження через %tw_sleep% с",
    "backup_storage_undecrypt_warning": "Резервна копія не міститиме деяких файлів користувача {1}, оскільки його дані не розшифровано.",
    "backup_storage_warning": "Резервні копії {1} не містять файлів у внутрішньому сховищі, зокрема фотографій і завантажень.",
    "boot_slot_a": "Слот A", "boot_slot_b": "Слот B",
    "cache_dalvik_done": "Очищення кешу Dalvik завершено!",
    "change_twrp_folder_after_process": "Папку TWRP змінено на",
    "change_twrp_folder_btn": "Змінити папку TWRP",
    "change_twrp_folder_on_process": "Зміна папки TWRP",
    "changing_boot_slot": "Зміна завантажувального слота",
    "changing_boot_slot_complete": "Завантажувальний слот змінено",
    "continue_restore_encrypted": "Продовжити відновлення?",
    "copy_logcat": "Журнал Logcat скопійовано до {1}",
    "create_ramdisk_error": "Не вдалося створити ramdisk для прошивання.",
    "current_boot_slot": "Поточний слот: %tw_active_slot%",
    "data_backup": "Дані (без внутрішнього сховища)",
    "data_media_fbe_msg": "На пристрої з FBE TWRP не створює повторно /data/media. Перезавантажте Android, щоб система створила /data/media.",
    "decrypt_data_enter_pass_fbe": "Введіть пароль користувача [%tw_crypto_user_id%]",
    "decrypt_data_enter_pattern_fbe": "Введіть графічний ключ користувача [%tw_crypto_user_id%]",
    "decrypt_data_vold_os_missing": "Відсутні файли, потрібні для розшифрування через vold: {1}",
    "decrypt_success_nodev": "Дані успішно розшифровано",
    "decrypt_user_fail_fbe": "Не вдалося розшифрувати дані користувача {1}",
    "decrypt_user_success_fbe": "Дані користувача {1} успішно розшифровано",
    "decrypt_users": "Розшифрувати дані користувачів",
    "decrypt_users_selection": "Виберіть ID користувача для розшифрування",
    "decrypting_user_fbe": "Спроба розшифрувати дані FBE користувача {1}…",
    "digest_matched": "Контрольна сума для «{1}» збігається.",
    "enable_adb": "Увімкнути ADB", "enable_fastboot": "Увімкнути Fastboot",
    "factory_reset5": "(не включаючи користувачів і екран блокування)",
    "fail_sysmap": "Не вдалося зіставити файл «{1}»",
    "fastboot_button": "Режим Fastboot", "fastboot_console_msg": "Перехід у режим Fastboot…",
    "fix_recovery_loop": "Виправити цикл перезавантаження recovery",
    "fix_recovery_loop_complete": "Цикл перезавантаження recovery виправлено",
    "fix_recovery_loop_confirm": "Виправити цикл перезавантаження recovery?",
    "fix_recovery_loop_patch_error": "Помилка виправлення ядра.",
    "fixing_recovery_loop": "Виправлення циклу перезавантаження recovery…",
    "fixing_recovery_loop_patch": "Виправлення ядра…",
    "flash_ab_both_slots": "Прошити в обидва слоти",
    "flash_ab_inactive": "Прошивання ZIP A/B у неактивний слот: {1}",
    "flash_ab_reboot": "Щоб прошити інші ZIP-файли, перезавантажте recovery для переходу на оновлений слот.",
    "fm_edit_file": "Редагувати файл", "fm_open_terminal_btn": "Відкрити термінал у цій папці",
    "include_logcat": "Додати журнал Logcat", "install_complete": "Встановлення завершено",
    "install_kernel": "Встановити ядро", "install_twrp_ramdisk": "Встановити ramdisk recovery",
    "installing": "Встановлення…", "invalid_zip_format": "Неприпустимий формат ZIP-файлу!",
    "merge_snapshots_confirm": "Об’єднати знімки?", "merges_snapshots": "Об’єднання знімків",
    "merging_snapshots": "Об’єднання знімків…", "merging_snapshots_complete": "Знімки об’єднано",
    "modified_ramdisk_error": "Файли ramdisk змінено, тому не вдалося створити образ для прошивання. Завантажте TWRP командою fastboot boot і повторіть дію або скористайтеся пунктом «Встановити ramdisk recovery».",
    "mount_vab_partitions": "Розділи в super можуть стати доступними лише після повторного запуску recovery.",
    "multiuser_warning1": "Дані не всіх користувачів розшифровано!",
    "multiuser_warning2": "Резервне копіювання та відновлення можуть завершитися помилкою!",
    "multiuser_warning_accept": "Усе одно продовжити", "multiuser_warning_hdr": "Попередження: кілька користувачів",
    "ok_btn": "ОК", "ozip_decrypt_decryption": "Розшифрування OZIP…",
    "ozip_decrypt_finish": "Розшифрування OZIP завершено!",
    "reboot_after_restore": "Після першого запуску рекомендовано один раз перезавантажити Android.",
    "reboot_install_app1": "Встановити офіційний застосунок TWRP?",
    "reboot_install_app2": "Застосунок перевіряє наявність нових версій TWRP.",
    "reboot_install_app_hdr": "Встановлення застосунку TWRP",
    "reboot_install_app_prompt_install": "Пропонувати встановлення застосунку TWRP, якщо його ще не встановлено",
    "reboot_install_app_system": "Встановити як системний застосунок",
    "reboot_installing_app": "Встановлення застосунку…",
    "reflash_twrp": "Прошити поточний TWRP", "reflash_twrp_complete": "TWRP прошито",
    "reflash_twrp_confirm": "Прошити поточний TWRP?", "reflashing_twrp": "Прошивання TWRP…",
    "remove_dynamic_groups": "Від’єднання логічних розділів Super…",
    "remove_dynamic_groups_complete": "Логічні розділи Super від’єднано",
    "remove_dynamic_groups_confirm": "Від’єднати всі логічні розділи Super?",
    "repack": "Перепакувати", "repack_backup_first": "Спершу створіть резервну копію поточного образу",
    "repack_error": "Не вдалося перепакувати образ.", "repack_image_hdr": "Вибір образу",
    "repack_kernel_confirm": "Встановити ядро?", "repack_kernel_confirm_hdr": "Встановлення ядра",
    "repack_overwrite_warning": "Якщо на пристрої був root, його буде втрачено — root потрібно буде встановити повторно.",
    "repack_ramdisk_confirm": "Встановити recovery?", "repack_ramdisk_confirm_hdr": "Встановлення recovery",
    "repacking_image": "Перепакування {1}…",
    "rescue_party0": "Спрацював механізм відновлення Android! Можливі рішення:",
    "rescue_party1": " 1. Очистити кеші та/або",
    "rescue_party2": " 2. Відформатувати розділ Data та/або",
    "rescue_party3": " 3. Встановити ROM начисто.",
    "rescue_party4": "Повідомлена проблема: ",
    "restore_pattern": "Відновити, якщо графічний ключ увімкнено?",
    "restore_pin": "Відновити, якщо PIN-код увімкнено?",
    "restore_pin_password": "Відновити, якщо PIN-код або пароль увімкнено?",
    "restore_system_context": "Не вдалося визначити контекст SELinux для {1} — Android може не завантажитися.",
    "restore_with_pattern1": "Графічний ключ увімкнено",
    "restore_with_pattern2": "Перед відновленням графічний ключ потрібно вимкнути",
    "restore_with_pin1": "PIN-код увімкнено", "restore_with_pin2": "Перед відновленням PIN-код потрібно вимкнути",
    "restore_with_pin_password1": "PIN-код або пароль увімкнено",
    "restore_with_pin_password2": "Перед відновленням PIN-код або пароль потрібно вимкнути",
    "select_user": "Вибрати користувача", "sha2_chk": "Використовувати SHA-2 для обчислення хешу",
    "skip_digest_zip_chk": "Не перевіряти контрольну суму перед встановленням ZIP",
    "swipe_to_install": "Проведіть, щоб встановити", "swipe_to_install_app": "Проведіть, щоб встановити застосунок TWRP",
    "tw_folder_exists": "Папка з такою назвою вже існує!",
    "unable_set_boot_slot": "Не вдалося змінити завантажувальний слот у завантажувачі на {1}",
    "uninstall_twrp_system_app": "Видалити системний застосунок TWRP",
    "uninstall_twrp_system_app_complete": "Системний застосунок TWRP видалено",
    "uninstall_twrp_system_app_confirm": "Видалити системний застосунок TWRP?",
    "uninstalling_twrp_system_app": "Видалення системного застосунку TWRP…",
    "unmap_super_devices": "Від’єднати логічні розділи Super",
    "unmap_super_devices_complete": "Логічні розділи Super від’єднано",
    "unmap_super_devices_confirm": "Від’єднати всі логічні розділи Super?",
    "unmapping_super_devices": "Від’єднання логічних розділів Super…",
    "unmount_sys_install": "Відмонтувати розділ System перед встановленням ZIP",
    "unmount_system": "Відмонтування розділу System…", "unmount_system_err": "Не вдалося відмонтувати розділ System",
    "unpack_error": "Не вдалося розпакувати образ.", "unpacking_image": "Розпакування {1}…",
    "vibration_disabled": "Вібрацію на цьому пристрої вимкнено",
    "wipe_dalvik_btn": "Очистити кеш Dalvik", "wipe_dalvik_complete": "Кеш Dalvik очищено",
    "wipe_dalvik_confirm": "Очистити кеш Dalvik?",
}



def patch_ui_xml(data: bytes) -> bytes:
    text = data.decode("utf-8")
    variable = '<variable name="tw_hide_navbar" value="1" persist="1"/>'
    if variable not in text:
        anchor = '<variable name="tw_samsung_navbar" value="0" persist="1"/>'
        if text.count(anchor) != 1:
            raise ValueError("could not find the expected navbar variable")
        text = text.replace(anchor, anchor + "\n\t\t" + variable, 1)

    # Increase the cursor target and pointer speed for TV viewing distances.
    text = text.replace('<placement w="15" h="15"/>', '<placement w="30" h="30"/>', 1)
    text = text.replace('<speed multiplier="2.5"/>', '<speed multiplier="3.0"/>', 1)

    start = text.find('<fill color="#000000">')
    if start < 0:
        raise ValueError("could not find the bottom navbar template")
    end = text.find("\n\t\t\t<action>", start)
    if end < 0:
        raise ValueError("could not find the end of the bottom navbar template")
    navbar = text[start:end]
    if NAVBAR_CONDITION not in navbar:
        navbar = navbar.replace(
            '<fill color="#000000">',
            '<fill color="#000000">\n\t\t\t\t' + NAVBAR_CONDITION,
            1,
        )
        navbar = re.sub(
            r"(<button>)",
            r"\1\n\t\t\t\t" + NAVBAR_CONDITION,
            navbar,
        )
    text = text[:start] + navbar + text[end:]
    return text.encode("utf-8")


def patch_landscape_xml(data: bytes) -> bytes:
    text = data.decode("utf-8")
    hide_toggle = '''\t\t\t<checkbox>
\t\t\t\t<placement x="%col1_x_right%" y="%row3a_y%"/>
\t\t\t\t<text>{@x96_hide_navbar=Hide bottom Back / Home / Console bar}</text>
\t\t\t\t<data variable="tw_hide_navbar"/>
\t\t\t</checkbox>

'''
    old_nav_checkbox = '''\t\t\t<checkbox>
\t\t\t\t<placement x="%col1_x_right%" y="%row3a_y%"/>
\t\t\t\t<text>{@rev_navbar_chk=Reversed navbar layout}</text>
\t\t\t\t<data variable="tw_samsung_navbar"/>
\t\t\t</checkbox>'''
    new_nav_checkbox = '''\t\t\t<checkbox>
\t\t\t\t<condition var1="tw_hide_navbar" op="=" var2="0"/>
\t\t\t\t<placement x="%col1_x_right%" y="%row4_y%"/>
\t\t\t\t<text>{@rev_navbar_chk=Reversed navbar layout}</text>
\t\t\t\t<data variable="tw_samsung_navbar"/>
\t\t\t</checkbox>'''
    if old_nav_checkbox in text:
        text = text.replace(old_nav_checkbox, hide_toggle + new_nav_checkbox, 1)
    elif "{@x96_hide_navbar=" not in text:
        raise ValueError("could not find the expected navbar setting")

    start = text.find('<button style="radiobutton">', text.find('<page name="settings">'))
    end = text.find('<button style="main_button_half_width">', start)
    if start < 0 or end < 0:
        raise ValueError("could not find the navbar layout controls")
    controls = text[start:end]
    if NAVBAR_CONDITION not in controls:
        controls = re.sub(
            r'(<button style="radiobutton">)',
            r"\1\n\t\t\t\t" + NAVBAR_CONDITION,
            controls,
        )
    text = text[:start] + controls + text[end:]
    return text.encode("utf-8")


def _language_strings(data: bytes) -> dict[str, str]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(data)
    resources = root.find("resources")
    if resources is None:
        raise ValueError("language XML has no resources node")
    values: dict[str, str] = {}
    for item in resources.findall("string"):
        name = item.attrib.get("name")
        if not name or name in values:
            raise ValueError(f"language XML has a missing or duplicate string name: {name}")
        values[name] = item.text or ""
    return values


def patch_language_xml(data: bytes, language: str, english_data: bytes | None = None) -> bytes:
    import html
    import xml.etree.ElementTree as ET

    if language == "en":
        return data
    translations = RU_STRINGS if language == "ru" else UK_STRINGS
    if english_data is None:
        raise ValueError(f"English source strings are required to build the {language} translation")
    english = _language_strings(english_data)
    current = _language_strings(data)
    merged = dict(current)
    for name, value in translations.items():
        if name != "x96_hide_navbar" and name not in english:
            raise ValueError(f"translation uses unknown English string: {name}")
        merged[name] = value

    missing = english.keys() - merged.keys()
    if missing:
        raise ValueError(f"{language} translation is missing {len(missing)} strings: {', '.join(sorted(missing))}")

    text = data.decode("utf-8")
    for name, value in translations.items():
        escaped_name = re.escape(name)
        pattern = re.compile(
            r'(<string\s+name="' + escaped_name + r'">)(.*?)(</string>)',
            re.DOTALL,
        )
        text, count = pattern.subn(lambda match: match.group(1) + html.escape(value, quote=False) + match.group(3), text, count=1)
        if count == 0:
            if name == "x96_hide_navbar":
                continue
            if "</resources>" not in text:
                raise ValueError(f"language file {language}.xml has no resources section")
            entry = f'\t\t<string name="{name}">{html.escape(value, quote=False)}</string>\n'
            text = text.replace("</resources>", entry + "\t</resources>", 1)

    output = text.encode("utf-8")
    values = _language_strings(output)
    if "x96_hide_navbar" not in values:
        entry = f'\t\t<string name="x96_hide_navbar">{html.escape(TRANSLATIONS[language], quote=False)}</string>\n'
        text = output.decode("utf-8").replace("</resources>", entry + "\t</resources>", 1)
        output = text.encode("utf-8")
        values = _language_strings(output)
    for name, source in english.items():
        target = values.get(name, "")
        if not target.strip():
            raise ValueError(f"{language} translation is empty for {name}")
        token_pattern = r"(?<!%)%[A-Za-z_][A-Za-z0-9_.-]*%(?!%)|\{\d+\}"
        source_tokens = re.findall(token_pattern, source)
        target_tokens = re.findall(token_pattern, target)
        if source_tokens != target_tokens:
            raise ValueError(f"placeholder mismatch in {language} translation {name}: {source_tokens} != {target_tokens}")
    return output


def patch_theme_file(path: str, data: bytes, english_data: bytes | None = None) -> bytes:
    normalized = path.replace("\\", "/")
    if normalized == "twres/ui.xml":
        return patch_ui_xml(data)
    if normalized == "twres/landscape.xml":
        return patch_landscape_xml(data)
    match = re.fullmatch(r"twres/languages/(en|ru|uk)\.xml", normalized)
    if match:
        return patch_language_xml(data, match.group(1), english_data)
    return data


def patch_theme_directory(theme_dir: Path) -> None:
    for name in ("ui.xml", "landscape.xml"):
        path = theme_dir / name
        path.write_bytes(
            patch_ui_xml(path.read_bytes())
            if name == "ui.xml"
            else patch_landscape_xml(path.read_bytes())
        )
    english_data = (theme_dir / "languages" / "en.xml").read_bytes()
    for language in ("ru", "uk"):
        path = theme_dir / "languages" / f"{language}.xml"
        path.write_bytes(patch_language_xml(path.read_bytes(), language, english_data))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme_dir", type=Path, help="path to extracted twres directory")
    args = parser.parse_args()
    patch_theme_directory(args.theme_dir)
