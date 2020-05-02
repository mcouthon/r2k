"""Adapted from SO: https://stackoverflow.com/a/48946422/978089"""
import re
import unicodedata
from typing import Dict, List, Tuple, Union

_common_char_maps: Dict[str, str] = {}


def _unicode_character_name(char: str) -> Union[str, None]:
    """Get the full unicode char name"""
    try:
        return unicodedata.name(char)
    except ValueError:
        return None


def _get_all_unicode_characters() -> List[Tuple[str, str]]:
    """Generate all Unicode characters with their names"""
    all_unicode_characters = []
    for n in range(0, 0x10FFFF):  # Unicode planes 0-16
        char = chr(n)  # Python 3
        name = _unicode_character_name(char)
        if name:
            all_unicode_characters.append((char, name))
    return all_unicode_characters


def _get_common_char_map() -> Dict[str, str]:
    """Create a mapping from common unicode characters to their ASCII counterparts"""
    global _common_char_maps
    if not _common_char_maps:
        all_unicode_characters = _get_all_unicode_characters()
        for char, name in all_unicode_characters:
            if "DOUBLE QUOTATION MARK" in name:
                _common_char_maps[char] = '"'
            elif "SINGLE QUOTATION MARK" in name:
                _common_char_maps[char] = "'"
            elif "DASH" in name and "DASHED" not in name:
                _common_char_maps[char] = "-"
    return _common_char_maps


def strip_common_unicode_chars(string: str) -> str:
    """Replace common unicode characters with comparable ASCII values"""
    char_map = _get_common_char_map()
    for char, replacement in char_map.items():
        if char in string:
            string = string.replace(char, replacement)
    return string


def normalize_str(string: str) -> str:
    """
    Strip any non alpha-numeric characters from a string and replace them with underscores
    """
    return re.sub(r"\W+", "_", string)
