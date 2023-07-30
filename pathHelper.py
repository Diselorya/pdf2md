import os
import pathlib

filename_trans_map = str.maketrans({
    '<': '《',
    '>': '》',
    ':': '：',
    '"': '“',
    '/': '┘',
    '\\': '└',
    '(': '（',
    ')': '）',
    '|': '┇',
    '?': '？',
    '*': '※',
})

filename_obsidian_trans_map = str.maketrans({
    '[': '【',
    ']': '】',
})


def filename_char_check(filename: str, for_obsidian: bool = False, trans_map: dict = filename_trans_map) -> str:
    name = filename.translate(trans_map)
    return name if not for_obsidian else name.translate(filename_obsidian_trans_map)