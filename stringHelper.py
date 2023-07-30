import unicodedata
import re

# 字符串标准化
def string_normalise(text: str, strip: bool = True, one_blank: bool = True, one_newline: bool = True, remove_unprint: bool = True) -> str:    
    # 统一中文字符 Unicode 编码  
    # '前⾔' 和 '前言' 在视觉上可能看起来相似，但它们实际上是由不同的字符组成的。
    # '前⾔' 中的第二个字符是一个特殊字符，它是 Unicode 字符集中的一个字符，表示为 U+2F54。
    # '前言' 中的第二个字符是一个普通的汉字字符，它是 Unicode 字符集中的一个字符，表示为 U+524D。
    # 可使用 unicodedata.normalize('NFKC', text) 方法标准化，但不能 100% 标准化，仍有漏网之鱼
    text = unicodedata.normalize('NFKC', text)

    # 去掉前后空白字符
    if strip:
        text = text.strip()

    # 多个空格替换为 1 个空格
    if one_blank:
        text = re.sub(r' +', ' ', text)

    if one_newline:
        text = text.replace(r'(\r?\n){2,}', '\n')
        
    # 使用正则表达式替换非打印字符为空字符串
    if remove_unprint:
        text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text)

    return text


# 去掉标点符号
def remove_punctuation(text: str) -> str:
    # Use regular expression to remove all punctuation marks
    text_without_punctuation = re.sub(r'[^\w\s]', '', text)
    return text_without_punctuation


def string_deepclean(text: str, ignore_case: bool = True, normalise: bool = True, \
                      ignore_space: bool = True, ignore_punctuation: bool = True) -> str:
    if ignore_case:
        text = text.lower()

    if normalise:
        text = string_normalise(text)

    if ignore_space:
        text = re.sub(r'\s+', '', text)

    if ignore_punctuation:
        text = remove_punctuation(text)

    return text


# 判断字符串相似度
def string_similarity(text1: str, text2: str, ignore_case: bool = True, normalise: bool = True, \
                      ignore_space: bool = True, ignore_punctuation: bool = True) -> float:  
    if '到底谁为⻥肉' in text2:
        print('Here')

    text1 = string_deepclean(text1, ignore_case, normalise, ignore_space, ignore_punctuation)
    text2 = string_deepclean(text2, ignore_case, normalise, ignore_space, ignore_punctuation)

    # max_length = max(len(text1), len(text2))
    # min_length = min(len(text1), len(text2))
    # len_diff = max_length - min_length
    # offset = 0
    # diff_count = len_diff
    # 这种比较法一旦有错位就不行了，后面的全部会判定为不一样
    # for i in range(min_length):
    #     if text1[i] == text2[i]:
    #         diff_count += 1

    similarity = chars_similarity(text1, text2, False)

    return similarity


# 判断字符相似度
def chars_similarity(text1: str, text2: str, clean: bool = False) -> float:
    if clean:
        text1 = string_normalise(text1)
        text2 = string_normalise(text2)

    set1 = set(text1)
    set2 = set(text2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    similarity = intersection / union
    return similarity