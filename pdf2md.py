import PyPDF2
import pytesseract
from PIL import Image
import math
import os
import re
import unicodedata
import pangu
import cv2
import numpy


sentence_end_symbols = ['。', ';' '；', '!', '！', '?', '？', ':', '：', '. ', '……']
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

# 清空终端
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


# 清空终端
def set_workdir_to_here():
    os.system('cd ' + os.path.dirname(os.path.realpath(__file__)))


def filename_char_check(filename: str, for_obsidian: bool = False, trans_map: dict = filename_trans_map) -> str:
    name = filename.translate(trans_map)
    return name if not for_obsidian else name.translate(filename_obsidian_trans_map)


def get_fixed_pdf_filename(pdf_file_name: str):
    return filename_char_check(pdf_file_name.replace('.pdf', '').replace('(Z-Library)', '').strip(), True)


def get_pdf_save_picture_path(pdf_file_name: str, page_num: int, image_count: int, picture_extname: str = 'jpg', folder_suffix: str = '.images'):
    # 图片保存在子文件夹中
    images_folder = pdf_file_name + folder_suffix
    if not os.path.isdir(images_folder):
        os.makedirs(images_folder)

    # 保存的图片名称
    image_name = f'{pdf_file_name}_{page_num}_{image_count}.{picture_extname}'
    image_path = os.path.join(images_folder, image_name)

    return image_path


def get_text_from_image_with_save(image_data: bytes, save_path_name: str):
    # 图片输出为文件
    with open(save_path_name, 'wb') as image_file:
        image_file.write(image_data)

    # 将 JPG 格式图片转换为 PIL 格式图片，Tesseract 只支持 PIL（Python Imaging Library）的Image对象 或 OpenCV
    pil_image = Image.open(save_path_name)

    # 使用OCR识别图像中的文本
    image_text = string_normalise(convert_image_to_text(pil_image)) + '\n'
    pil_image.close()

    return image_text


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


# PDF 标题比较
def recognized_as_title(text: str, bookmark_title: str, similarity: float = 1) -> bool:
    # undone: similarity 不能大于 1
    
    # 应对不完整的句子合并时的误差，截取和书签相同的长度进行比较
    text = string_deepclean(text)
    bookmark_title = string_deepclean(bookmark_title)
    if len(text) > len(bookmark_title):
        text = text[:len(bookmark_title)]

    return string_similarity(text, bookmark_title) >= similarity


def preprocess_image_for_ocr(pil_image: Image) -> Image:
    # Convert the image to grayscale if it has only one channel
    if pil_image.mode == 'L':
        pil_image = pil_image.convert('RGB')
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(numpy.array(pil_image), cv2.COLOR_RGB2GRAY)
    
    # Apply thresholding to convert the image to binary
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Convert the binary image back to PIL Image format
    preprocessed_image = Image.fromarray(binary_image)
    
    return preprocessed_image


def convert_image_to_text(pil_image: Image, language_packs: list[str] = ['chi_sim'], config: str = '--psm 6 --oem 3') -> str:
    language = '+'.join(language_packs)
    return pytesseract.image_to_string(preprocess_image_for_ocr(pil_image), lang=language, config=config)


class Bookmark:
    def __init__(self, title: str, level: int, page_number: int):
        self.title = string_normalise(title)
        self.level = level
        self.page_number = page_number
    line_number: int
    order: int


def get_bookmarks(pdf_reader, page_number):
    current_page_bookmarks = []
    for bookmark in pdf_reader.outline:
        # print(bookmark)
        if isinstance(bookmark, list):
            if pdf_reader.get_destination_page_number(bookmark[0]) == page_number:
                current_page_bookmarks.append(bookmark)
        else:
            if pdf_reader.get_destination_page_number(bookmark) == page_number:
                current_page_bookmarks.append(bookmark)
    return current_page_bookmarks


# 获取 PDF 文件中的所有标签
def get_all_bookmarks(pdf_reader: PyPDF2.PdfReader) -> list[Bookmark]:
    outlines = pdf_reader.outline
    bookmarks = []

    def process_outline(outline, level=0):
        for element in outline:
            if isinstance(element, list):
                process_outline(element, level + 1)
            else:
                title = element.title
                page_number = pdf_reader.get_destination_page_number(element)                               

                if '优胜劣汰' in title:
                    print('Here')

                # 不知道为什么，博弈论取出来的都少了 1
                bm = Bookmark(string_normalise(title), level + 1, page_number)

                # 如果标题有中文，则把英文标点替换为中文标点
                if re.match(r'[^A-Za-z0-9_]+', remove_punctuation(bm.title)) != None:
                    bm.title = pangu.spacing_text(bm.title)
                else:
                    print('')
                bm.order = len(bookmarks)
                bookmarks.append(bm)

    process_outline(outlines)
    return bookmarks


# 获取当前页可能的书签
def get_bookmark_of_this_page(bookmarks: list[Bookmark], page_number: int, tolerance_page: int = 0) -> list[Bookmark]:
    marks = []
    for bookmark in bookmarks:
        if page_number < 0 or abs(bookmark.page_number - page_number) <= tolerance_page:
            marks.append(bookmark)

    return marks 


def get_image_count(pdf_reader: PyPDF2.PdfReader) -> int:
    count = 0
    for page in pdf_reader.pages:
        count += len(page.images)
    return count


def get_char_count(pdf_reader: PyPDF2.PdfReader) -> tuple[int, list[int]]:
    count = 0
    counts = [0] * 200
    page_count = 1    
    extracted_text = ''

    for page in pdf_reader.pages:
        print(f'正在统计字符数：{page_count}/{len(pdf_reader.pages)}...{round(page_count/len(pdf_reader.pages)*100, 2)}%')
        page_count += 1
        extracted_text += page.extract_text().strip() + '\n'
        
    count = len(extracted_text.strip())

    lines = extracted_text.splitlines()
    for line in lines:
        counts[len(line)] += 1

    for i in range(len(counts)):
        if counts[-1] == 0:
            del counts[-1]
        else:
            break

    print(counts)
    return (count, counts)


def get_char_count_including_picture(pdf_reader: PyPDF2.PdfReader, including_picture: bool = False, filename_prefix: str = '') -> tuple[int, list[int], list[list[str]]]:
    count = 0
    counts = [0] * 200
    page_count = 1    
    extracted_text = ''
    if filename_prefix == '':
        filename_prefix = pdf_reader.metadata.title

    images_text_of_each_pages = []

    for page in pdf_reader.pages:
        print(f'正在统计字符数：{page_count}/{len(pdf_reader.pages)}...{round(page_count/len(pdf_reader.pages)*100, 2)}%')
        page_count += 1
        extracted_text += page.extract_text().strip() + '\n'
        images_texts = []

        if including_picture:
            image_count = 0
            for image in page.images:
                image_count += 1
                text = get_text_from_image_with_save(image.data, get_pdf_save_picture_path(get_fixed_pdf_filename(filename_prefix), page_count, image_count))
                images_texts.append(text)
                # print(f'Image-P{page_count}-{image_count}：\n{text}')
                extracted_text += text

        images_text_of_each_pages.append(images_texts)
    
    count = len(extracted_text.strip())

    lines = extracted_text.splitlines()
    for line in lines:
        counts[len(line)] += 1

    for i in range(len(counts)):
        if counts[-1] == 0:
            del counts[-1]
        else:
            break

    print(counts)
    return (count, counts, images_text_of_each_pages)


def get_char_count_of_each_line(pdf_reader: PyPDF2.PdfReader) -> list[int]:
    counts = [0] * 200
    page_count = 1    
    for page in pdf_reader.pages:
        print(f'正在统计每一行的字符数：{page_count}/{len(pdf_reader.pages)}...{round(page_count/len(pdf_reader.pages)*100, 2)}%')
        page_count += 1

        lines = page.extract_text().splitlines()
        for line in lines:
            counts[len(line)] += 1
    return counts


def get_full_line_char_count(pdf_reader: PyPDF2.PdfReader) -> int:
    counts = get_char_count_of_each_line(pdf_reader)
    max = 0
    number = 0
    for i in range(len(counts)):
        if counts[i] > max:
            max = counts[i]
            number = i
    return number


def get_max_number_index(numbers: list[int]) -> int:
    max = 0
    number = 0
    for i in range(len(numbers)):
        if numbers[i] > max and i > 5:
            max = numbers[i]
            number = i
    
    return number


def get_default_tolerance(line_max_char_count: int, tolerance_range: float = 0.2) -> int:
    return int(line_max_char_count * tolerance_range)


def get_default_tolerance(line_char_count_tolerance: int, line_max_char_count: int, tolerance_range: float = 0.2) -> int:
    return int(line_max_char_count * tolerance_range) if line_char_count_tolerance < 0 else line_char_count_tolerance


def is_broken_line(line: str, line_max_char_count: int, line_char_count_tolerance: int = -1) -> bool:
    if line.strip() == '':
        return False
    line_char_count_tolerance = get_default_tolerance(line_char_count_tolerance, line_max_char_count)
    return (len(line) >= line_max_char_count or \
        (len(line) >= line_max_char_count - line_char_count_tolerance)) and \
        not (line.strip()[-1] in sentence_end_symbols)


# 把提取出来的不完整的行拼接完整
def join_broken_line(text: str, line_max_char_count: int, line_char_count_tolerance: int = -1) -> tuple[str, bool]:
    line_char_count_tolerance = get_default_tolerance(line_char_count_tolerance, line_max_char_count)
    lines = text.splitlines()
    text_fixed = ''
    is_completed = True
    for line in lines:
        if is_broken_line(line, line_max_char_count, line_char_count_tolerance):
            text_fixed += line.rstrip()
            is_completed = False
        else:
            text_fixed += line.rstrip() + '\n'    # 换行问题不在这
            is_completed = True
    return text_fixed, is_completed


# 段落分析，加标记
def add_mark_for_each_paragraph(text: str, page_num: int, is_paragraph_completed: bool = True) -> str:
    lines = text.splitlines()
    text_new = ''
    section_count = 1
    line_count = 0
    for line in lines:
        line_count += 1
        if line.strip() == '':
            text_new += line + '\n'
            continue

        if (line_count == len(lines) and not is_paragraph_completed) or re.match(r'^#+\s+.+$', line) != None:
            if (line_count == len(lines) and not is_paragraph_completed):
                text_new += line
            else:
                text_new += line + '\n'
        else:
            text_new += f'{line} ^page-{page_num+1}-section-{section_count}' + '\n'*2   # 不能在段落开头加空格或 Tab，会导致角标无法识别等一系列 Obsidian 语法问题
            section_count += 1
    return text_new


# 识别书签，并修改为 Markdown 标题
def format_markdown_header(text: str, page_number:int, bookmarks: list[Bookmark], is_paragraph_completed: bool = True, find_bookmarks: list[bool] = None) -> str:
    if text.strip() == '':
        return text

    lines = text.strip().splitlines()
    already_find = False
    if find_bookmarks == None:
        find_bookmarks = [False] * len(bookmarks)
    new_text = ''
    line_count = 0
    for line in lines:
        line_count += 1
        if line.strip() == '':
            continue

        if '智猪博弈' in line:
            print('Here')

        page_bookmarks = get_bookmark_of_this_page(bookmarks, page_number, 1)
        if len(page_bookmarks) < 1:
            return text
            
        for bookmark in page_bookmarks:
            # 纯数字说明是用页码做标题，不查找了
            if re.match(r'^\s*[0-9]+\s*$', bookmark.title):
                continue
            if not find_bookmarks[bookmark.order] and recognized_as_title(line, bookmark.title, 0.7):
                line = '#' * bookmark.level + ' ' + bookmark.title + '\n'
                find_bookmarks[bookmark.order] = True
                already_find = True
                break

        if (line_count == len(lines) and not is_paragraph_completed):
            new_text += line
        else:            
            new_text += line + '\n'

    # # 如果实在没找到
    # if not already_find:
    #     for bm in page_bookmarks:
    #         if find_bookmarks[bm.order] == False:
    #             new_text = '\n' + '#' * bm.level + ' ' + bm.title + '\n' * 2 + new_text
    #             find_bookmarks[bm.order] = True

    if new_text.strip() == '':
        print(f'第 {page_number} 页八成有问题')

    return new_text


def pdf2md(pdf_file_path, output_path='', \
            page_as_head=False, insert_images=True, \
            force_join_broken_line=True, line_char_count_tolerance=-1, \
            show_process=True, also_txt=False):
    
    set_workdir_to_here()
    clear_terminal()

    # 打开PDF文件
    print('工作路径：' + os.getcwd())
    print('脚本路径：' + os.path.dirname(os.path.realpath(__file__)))
    pdf_reader = PyPDF2.PdfReader(open(pdf_file_path, 'rb'))

    # 提取不包含路径的文件名
    pdf_paths = os.path.split(pdf_file_path)
    pdf_file_name = pdf_paths[len(pdf_paths) - 1]

    # 纯粹的书名: 处理文件名中的特殊字符：不能作为文件名的、干扰 Obsidian 语法的
    file_name = get_fixed_pdf_filename(pdf_file_name)
    print(file_name)
    # return    
    
    pages_count = len(pdf_reader.pages)  # 获取PDF的页数
    image_count = get_image_count(pdf_reader)  # 获取PDF中的图片数量
    total_char_count, char_count_of_each_line = get_char_count(pdf_reader)  # 获取PDF中的字符数量

    is_pure_picture = False  # 初始化纯图片标志为假    
    # 判断 PDF 是否为纯图片：页数 == 图片数 and 总字数 < 页数*10
    if pages_count == image_count and total_char_count < image_count * 10:
        is_pure_picture = True
    if is_pure_picture:
        (total_char_count, char_count_of_each_line, text_each_images_pages) = \
            get_char_count_including_picture(pdf_reader, is_pure_picture, file_name)  # 获取PDF中的字符数量

    line_max_char_count = 99999
    if force_join_broken_line:
        # line_max_char_count = get_full_line_char_count(pdf_reader)  # 获取PDF中每行的最大字符数量
        line_max_char_count = get_max_number_index(char_count_of_each_line)  # 获取PDF中每行的最大字符数量

    line_char_count_tolerance = get_default_tolerance(line_char_count_tolerance, line_max_char_count)
    print(line_max_char_count, line_char_count_tolerance)

    bookmarks = get_all_bookmarks(pdf_reader)


    # 书中的所有文字保存在这个变量中
    all_text_md = ''
    all_text_txt = ''
    pages_text_pdf = []
    pages_text_txt = []


    # 记录每一页结束的时候是否是完整的段落
    is_page_last_line_completed = [False] * pages_count
           
    find_bookmarks = [False] * len(bookmarks)

    # 遍历每一页
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page_text_md = ''
        page_text_txt = ''
        head_when_picture = ''

        # 本页中的文字
        text = string_normalise(page.extract_text()) + '\n'
        page_text_md += text
        page_text_txt += text

        # 遍历本页中的每一张图片，提取出来是 JPG 格式
        image_count = 0
        for image in page.images:
            image_count += 1

            # 使用OCR识别图像中的文本
            image_path = get_pdf_save_picture_path(file_name, page_num, image_count, 'jpg')
            if is_pure_picture:
                image_text = text_each_images_pages[page_num][image_count - 1]
            else:
                image_text = get_text_from_image_with_save(image.data, image_path)
            

            page_text_md += image_text
            page_text_txt += image_text

            # 在 Markdown 中显示图片
            if insert_images:
                page_text_md += '\n' f'![[{os.path.basename(image_path)}]]' + '\n'*2

        # 合并断开的行
        if force_join_broken_line:
            page_text_md, page_completed = join_broken_line(page_text_md, line_max_char_count, line_char_count_tolerance)
            is_page_last_line_completed[page_num] = page_completed
            page_text_txt, page_completed = join_broken_line(page_text_txt, line_max_char_count, line_char_count_tolerance)
            
        # 识别书签，并修改为 Markdown 标题 
        page_text_md = format_markdown_header(page_text_md, page_num, bookmarks, page_completed, find_bookmarks)

        # 段落分析，为 Markdown 加便于引用的标记
        page_text_md = add_mark_for_each_paragraph(page_text_md, page_num, page_completed)

        # 纯图片 PDF 把图片第一行（页眉）作为标题的一部分
        if is_pure_picture:            
            # 按标点符号拆分句子
            first_sentence = re.sub(r'\^page-\d+-section-\d+', '', text_split_by_punctuation(page_text_md)[0]).strip()
            # 判断是否每页都有书签
            search = re.search(r'^(#+)\s+(.+)(\s*)$', first_sentence)
            if len(bookmarks) >= pages_count and search != None:                    
                re.sub(r'^(#+)\s+(.+)(\s*)$', r'\1 Page.' + str(page_num).rjust(4, '0') + r' \2\3', first_sentence.strip().replace('\t', ' '))
            else:
                page_text_md = '# Page.' + str(page_num).rjust(4, '0') + ' ' + first_sentence + '\n'*2 + page_text_md

        # undone: 通过页眉和目录、页码进行比对，识别各级标题

        # page_text_md = head_when_picture + '\n' + page_text_md
        print(re.sub(r'\r?\n', '※' + os.linesep, page_text_md))

        pages_text_pdf.append(page_text_md)
        pages_text_txt.append(page_text_txt)

        # 显示进度
        if show_process:
            print(f'正在打印第 {page_num + 1}/{len(pdf_reader.pages)}页...{round((page_num+1)/len(pdf_reader.pages) * 100, 2)}%')

    # 将列表拼合成文本
    all_text_md = ''.join(map(str, pages_text_pdf))
    all_text_txt = ''.join(map(str, pages_text_txt))

    # 将文本保存到 Markdown文件
    md_file = os.path.join(output_path, file_name + '.md')
    txt_file = md_file.replace('.md', '.txt', -3)
    print(md_file)
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(all_text_md.strip())

    if also_txt:
        with open(txt_file, 'w', encoding='utf-8', newline='') as txt_file:
            txt_file.write(all_text_txt.strip())


# 批量转换一个文件夹下的 PDF
def pdf2md_batch(pdf_dir_path='', output_path='', \
            page_as_head=False, insert_images=True, \
            force_join_broken_line=True, line_char_count_tolerance=-1, \
            show_process=True, also_txt=False) -> int:
    if pdf_dir_path == '':
        pdf_dir_path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(pdf_dir_path):
        print(f'路径 {pdf_dir_path} 不存在。')
        return
    if output_path == '':
        output_path = os.path.join(pdf_dir_path, 'Convert')

    success_count = 0
    for root, dirs, files in os.walk(pdf_dir_path):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                try:
                    pdf2md(file_path, output_path, page_as_head, insert_images, force_join_broken_line, line_char_count_tolerance, show_process, also_txt)
                    success_count += 1
                except Exception as e:
                    print(f"Error processing PDF file: {file_path}")
                    print(f"Error message: {str(e)}")
    return success_count
        

# 测试代码
if __name__ == '__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    # pdf_file = ''
    # pdf2md(os.path.join(script_path, pdf_file), also_txt=True)