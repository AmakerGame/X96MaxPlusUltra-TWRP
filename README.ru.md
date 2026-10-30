# TWRP для X96 Max Plus Ultra (4/64)

Неофициальный порт для **X96 Max Plus Ultra 4 ГБ RAM / 64 ГБ**, плата `ohm`, Amlogic S905X4, Android 11. Совместимость сверялась на одном экземпляре с fingerprint `Droidlogic/ohm/ohm:11/RD2A.211001.002/eng.ubuntu.20240531.201028:userdebug/test-keys`, ядром 5.4.125 и загрузчиком `01.01.240531.211011`. Другие варианты памяти/платы/прошивки не подтверждены.

Это не официальная сборка Team Win. TWRP основан на пакете AM7 X4 3.6.1_11-0, который загружался на этой приставке.

**Язык:** [English](README.md) · [українською](docs/BUILD_UK.md) · [на русском](docs/BUILD_RU.md).

Руководства: [временный запуск USB (UA)](docs/USB_TEST_UK.md) · [USB на русском](docs/USB_TEST_RU.md) · [совместимость](docs/COMPATIBILITY.md).

## Текущее состояние

30.10.2026 собран и записан в активный `boot_a` этой приставки совместный образ TWRP + Magisk 31.1. SHA-256 файла и контрольного чтения раздела совпадает: `ada7a8d030ebbba97c77d60eb97b2c48754f5bcebd92d68fa9c4fce4198341a7`. Образ — Android boot header v3, 64 MiB. В ramdisk сохранены init-файлы TWRP, оба считанных ИК-профиля и полезная нагрузка Magisk.

После прошивки образ успешно загрузился обратно в Android. `magisk -v` показал Magisk 31.1, а `su -c id` вернул UID 0 с SELinux-контекстом Magisk. После `adb reboot recovery` Wi-Fi ADB и ping стали недоступны, поэтому экран recovery и работу D-pad в графическом меню TWRP визуально проверить не удалось. Резервная копия предыдущего TWRP boot: `../boot_a_twrp_before_magisk.img`, SHA-256 `e3339615a8e4665482d065e5d89e0fcfdc9c06c70d10fd63eacbb7746b1bfd3a`. Исходный Magisk boot: `dist/boot_a_magisk_restore.img`, SHA-256 `2d520b45aacd1e7218db904ca5b47527e0d881a1f1cc2fd9acaeda39affdb733`.

Keylayout приставки преобразует коды 28/103/108/105/106 в DPAD_CENTER/UP/DOWN/LEFT/RIGHT. Сборщик теперь проверяет эти коды в обоих ИК-профилях и keylayout. Стрелки и OK передаются как клавиши, без эмуляции мыши. Но GUI TWRP не имеет универсального перемещения фокуса стрелками; для полноценного D-pad нужно менять и собирать GUI/framework под совместимое device tree.

## Известные ограничения

- Android 11 использует FBE. В переданном recovery-логе есть `Unable to decrypt FBE device`. Расшифровка `/data` и совместимость Keymaster/TEE не исправлены; **не форматируйте Data для проверки**.
- Создание/восстановление резервных копий всех разделов и установка ZIP не подтверждены.
- Образ имеет Android boot header v3 и размер 64 MiB, сохраняет штатное ядро. Он не изменяет `vendor_boot`, `dtbo`, `super` или загрузчик.
- Перед прошивкой сохраните личные данные и штатный `boot_a`. См. инструкции по резервному копированию и восстановлению.

## Сборка

Исходные образы firmware/TWRP, `remotecfg`, снятые логи и готовые `.img` не хранятся в этом репозитории. Build script использует локальные файлы в `input/` и создаёт результат в `dist/`; эти папки исключены из Git. Подробные требования — [BUILD_UK](docs/BUILD_UK.md) и [BUILD_RU](docs/BUILD_RU.md).

Лицензии: [NOTICE.md](NOTICE.md), [LICENSE](LICENSE).
