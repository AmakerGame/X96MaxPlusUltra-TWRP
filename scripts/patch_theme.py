#!/usr/bin/env python3
"""Apply the X96 TV-friendly settings to an extracted TWRP theme."""

from __future__ import annotations

import re
from pathlib import Path


NAVBAR_CONDITION = '<condition var1="tw_hide_navbar" op="=" var2="0"/>'

TRANSLATIONS = {
    "en": "Hide bottom Back / Home / Console bar",
    "ru": "Скрыть нижнюю панель Back / Home / Console",
    "uk": "Приховати нижню панель Back / Home / Console",
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


def patch_language_xml(data: bytes, language: str) -> bytes:
    text = data.decode("utf-8")
    key = '<string name="x96_hide_navbar">'
    if key in text:
        return data
    value = TRANSLATIONS[language]
    closing = "</resources>"
    if closing not in text:
        raise ValueError(f"language file {language}.xml has no resources section")
    entry = f'\t\t<string name="x96_hide_navbar">{value}</string>\n'
    return text.replace(closing, entry + closing, 1).encode("utf-8")


def patch_theme_file(path: str, data: bytes) -> bytes:
    normalized = path.replace("\\", "/")
    if normalized == "twres/ui.xml":
        return patch_ui_xml(data)
    if normalized == "twres/landscape.xml":
        return patch_landscape_xml(data)
    match = re.fullmatch(r"twres/languages/(en|ru|uk)\.xml", normalized)
    if match:
        return patch_language_xml(data, match.group(1))
    return data


def patch_theme_directory(theme_dir: Path) -> None:
    for name in ("ui.xml", "landscape.xml"):
        path = theme_dir / name
        path.write_bytes(
            patch_ui_xml(path.read_bytes())
            if name == "ui.xml"
            else patch_landscape_xml(path.read_bytes())
        )
    for language in TRANSLATIONS:
        path = theme_dir / "languages" / f"{language}.xml"
        path.write_bytes(patch_language_xml(path.read_bytes(), language))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme_dir", type=Path, help="path to extracted twres directory")
    args = parser.parse_args()
    patch_theme_directory(args.theme_dir)
