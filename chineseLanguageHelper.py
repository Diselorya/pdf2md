

sentence_end_symbols = ['。', ';' '；', '!', '！', '?', '？', ':', '：', '. ', '……']


# 英文标点改中文标点
def convert_punctuation_to_chinese(text: str) -> str:
    punctuation_mapping = {
        '.': '。',
        ',': '，',
        '?': '？',
        '!': '！',
        ':': '：',
        ';': '；',
        '(': '（',
        ')': '）',
        '[': '【',
        ']': '】',
        '{': '{',
        '}': '}',
        '<': '《',
        '>': '》',
        '"': '“',
        "'": '‘',
        '_': '——',
        '^': '……',
    }
    for char in punctuation_mapping:
        text = text.replace(char, punctuation_mapping[char])
    return text


# 按标点符号拆分句子
def text_split_by_punctuation(text: str) -> list[str]:
    start = 0
    splitted = []
    for pos in range(len(text)):
        if text[pos] in sentence_end_symbols or text[pos] == '\n':
            splitted.append(text[start:pos+1].strip())
            start = pos + 1

    if start < pos:
        splitted.append(text[start:])

    return splitted