import os
import PyPDF2
import re
import pangu
import stringHelper as sh
import pdfHelper as ph
import chineseLanguageHelper as ch


def get_pdf_save_picture_path(pdf_file_name: str, page_num: int, image_count: int, output_path: str = '', picture_extname: str = 'jpg', folder_suffix: str = '.images'):
    # 图片保存在子文件夹中
    images_folder = os.path.join(output_path, pdf_file_name + folder_suffix)
    if not os.path.isdir(images_folder):
        os.makedirs(images_folder)

    # 保存的图片名称
    image_name = f'{pdf_file_name}_{page_num}_{image_count}.{picture_extname}'
    image_path = os.path.join(images_folder, image_name)

    return image_path



# PDF 标题比较
def recognized_as_title(text: str, bookmark_title: str, similarity: float = 1) -> bool:
    # undone: similarity 不能大于 1
    
    # 应对不完整的句子合并时的误差，截取和书签相同的长度进行比较
    text = sh.string_deepclean(text)
    bookmark_title = sh.string_deepclean(bookmark_title)
    if len(text) > len(bookmark_title):
        text = text[:len(bookmark_title)]

    return sh.string_similarity(text, bookmark_title) >= similarity


class Bookmark:
    def __init__(self, title: str, level: int, page_number: int):
        self.title = sh.string_normalise(title)
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
                bm = Bookmark(sh.string_normalise(title), level + 1, page_number)

                # 如果标题有中文，则把英文标点替换为中文标点
                if re.match(r'[^A-Za-z0-9_]+', sh.remove_punctuation(bm.title)) != None:
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


def get_char_count_including_picture(pdf_reader: PyPDF2.PdfReader, output_path: str = '', including_picture: bool = False, filename_prefix: str = '') -> tuple[int, list[int], list[list[str]]]:
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
                text = ph.get_text_from_image_with_save(image.data, get_pdf_save_picture_path(filename_prefix, page_count, image_count, output_path))
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
        not (line.strip()[-1] in ch.sentence_end_symbols)


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
    

def is_pure_picture(pages_count: int, image_count: int, total_char_count: int) -> bool:
    # 判断 PDF 是否为纯图片：页数 == 图片数 and 总字数 < 页数*10
    if pages_count == image_count and total_char_count < image_count * 10:
        return True
    else:
        return False

def get_max_line_char_count(occurrence_of_line_char_count: list[int]) -> int:   
    return get_max_number_index(occurrence_of_line_char_count)


class PdfInfo:
    def __init__(self, reader: PyPDF2.PdfFileReader):
        self.reader = reader

        self.title = reader.metadata.title
        self.author = reader.metadata.author
        self.subject = reader.metadata.subject
        self.creator = reader.metadata.creator
        self.producer = reader.metadata.producer
        self.creation_date = reader.metadata.creation_date
        self.modification_date = reader.metadata.modification_date
        
        self.page_count = len(reader.pages)  # 获取PDF的页数
        self.image_count = get_image_count(reader)  # 获取PDF中的图片数量
        self.total_char_count, self.occurrence_of_line_char_count = get_char_count(reader)  # 获取PDF中的字符数量
        self.max_char_count_of_line = get_max_line_char_count(self.occurrence_of_line_char_count)  # 获取PDF中的最大行字符数
        
        self.is_pure_picture = is_pure_picture(self.page_count, self.image_count, self.total_char_count)


    def update_char_counts_including_images(self, output_path: str = '.outputs', image_file_name_prefix: str = '') -> 'PdfInfo':
        if image_file_name_prefix == '':
            image_file_name_prefix = self.title
        
        (self.total_char_count, self.occurrence_of_line_char_count, self.text_each_images_pages) = \
            get_char_count_including_picture(self.reader, output_path, self.is_pure_picture, image_file_name_prefix)
        
        self.max_char_count_of_line = get_max_line_char_count(self.occurrence_of_line_char_count)  # 获取PDF中的最大行字符数
        
        return self
