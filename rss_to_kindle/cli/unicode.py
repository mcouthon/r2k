"""Adapted from SO: https://stackoverflow.com/a/48946422/978089"""
import unicodedata
from typing import Union


def unicode_character_name(char: str) -> Union[str, None]:
    """Get the full unicode char name"""
    try:
        return unicodedata.name(char)
    except ValueError:
        return None


def get_all_unicode_characters() -> list:
    """Generate all Unicode characters with their names"""
    all_unicode_characters = []
    for n in range(0, 0x10FFFF):  # Unicode planes 0-16
        char = chr(n)  # Python 3
        name = unicode_character_name(char)
        if name:
            all_unicode_characters.append((char, name))
    return all_unicode_characters


def get_common_char_mapping() -> dict:
    """Create a mapping from common unicode characters to their ASCII counterparts"""
    all_unicode_characters = get_all_unicode_characters()
    common_char_maps = {}
    for char, name in all_unicode_characters:
        if "DOUBLE QUOTATION MARK" in name:
            common_char_maps[char] = '"'
        elif "SINGLE QUOTATION MARK" in name:
            common_char_maps[char] = "'"
        elif "DASH" in name and "DASHED" not in name:
            common_char_maps[char] = "-"
    return common_char_maps
