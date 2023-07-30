import PyPDF2
import os
import re
import chineseLanguageHelper as clh
import pathHelper
import terminalHelper as th
import pdfHelper
import stringHelper as sh


def get_fixed_pdf_filename(pdf_file_name: str):
    return pathHelper.filename_char_check(pdf_file_name.replace('.pdf', '').replace('(Z-Library)', '').strip(), True)


# 段落分析，加 Obsidian 引用标记
def add_mark_for_each_paragraph(text: str, page_num: int, is_paragraph_completed: bool = True) -> str:
    lines = text.splitlines()
    text_new = ''
    section_count = 1
    for line_num, line in enumerate(lines):
        if line.strip() == '':
            text_new += line + '\n'
            continue

        # 如果是最后一行且段落未完成，或者是标题行，则不加引用标记
        if (line_num + 1 == len(lines) and not is_paragraph_completed) or re.match(r'^#+\s+.+$', line) != None:
            if (line_num + 1 == len(lines) and not is_paragraph_completed):
                text_new += line
            else:
                text_new += line + '\n'
        else:
            # 在每个段落的非空行后加入引用标记
            # 不能在段落开头加空格或 Tab，会导致角标无法识别等一系列 Obsidian 语法问题
            text_new += f'{line} ^page-{page_num+1}-section-{section_count}' + '\n'*2
            section_count += 1
    return text_new


# 识别书签，并修改为 Markdown 标题
def format_markdown_header(text: str, page_number:int, bookmarks: list[pdfHelper.Bookmark], is_paragraph_completed: bool = True, find_bookmarks: list[bool] = None) -> str:
    if text.strip() == '':
        return text

    lines = text.strip().splitlines()
    already_find = False
    if find_bookmarks is None:
        find_bookmarks = [False] * len(bookmarks)
    new_text = ''
    line_count = 0
    for line in lines:
        line_count += 1
        if line.strip() == '':
            continue

        page_bookmarks = pdfHelper.get_bookmark_of_this_page(bookmarks, page_number, 1)
        if len(page_bookmarks) < 1:
            return text
            
        for bookmark in page_bookmarks:
            # 纯数字说明是用页码做标题，不查找了
            if re.match(r'^\s*[0-9]+\s*$', bookmark.title):
                continue
            if not find_bookmarks[bookmark.order] and pdfHelper.recognized_as_title(line, bookmark.title, 0.7):
                line = '#' * bookmark.level + ' ' + bookmark.title + '\n'
                find_bookmarks[bookmark.order] = True
                already_find = True
                break

        if (line_count == len(lines) and not is_paragraph_completed):
            new_text += line
        else:            
            new_text += line + '\n'

    # # 如果实在没找到，就在段落开头加入
    # if not already_find:
    #     for bm in page_bookmarks:
    #         if find_bookmarks[bm.order] == False:
    #             new_text = '\n' + '#' * bm.level + ' ' + bm.title + '\n' * 2 + new_text
    #             find_bookmarks[bm.order] = True

    return new_text


def pdf2md(pdf_file_path, output_path='', \
            page_as_head=False, insert_images=True, \
            force_join_broken_line=True, line_char_count_tolerance=-1, \
            show_process=True, also_txt=False):
    
    th.set_workdir_to_here()
    th.clear_terminal()

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

    # undone: 这些变量可以用一个类存储，放在 pdfHelper 里
    pdf_info = pdfHelper.PdfInfo(pdf_reader)  # 获取PDF的基本信息

    # 更新 PDF 中的字符数量，连图片中的字符也算
    if pdf_info.is_pure_picture:
            pdf_info.update_char_counts_including_images(output_path, file_name)

    line_max_char_count = 99999
    if force_join_broken_line:
        line_max_char_count = pdfHelper.get_max_line_char_count(pdf_info.occurrence_of_line_char_count)  # 获取PDF中每行的最大字符数量

    line_char_count_tolerance = pdfHelper.get_default_tolerance(line_char_count_tolerance, line_max_char_count)
    print(line_max_char_count, line_char_count_tolerance)

    bookmarks = pdfHelper.get_all_bookmarks(pdf_reader)


    # 书中的所有文字保存在这个变量中
    all_text_md = ''
    all_text_txt = ''
    pages_text_pdf = []
    pages_text_txt = []
    

    # 记录每一页结束的时候是否是完整的段落
    is_page_last_line_completed = [False] * pdf_info.page_count
           
    find_bookmarks = [False] * len(bookmarks)

    # 遍历每一页
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page_text_md = ''
        page_text_txt = ''

        # 本页中的文字
        text = sh.string_normalise(page.extract_text()) + '\n'
        page_text_md += text
        page_text_txt += text

        # 遍历本页中的每一张图片，提取出来是 JPG 格式
        pdf_info.image_count = 0
        for image in page.images:
            pdf_info.image_count += 1

            # 使用OCR识别图像中的文本
            image_path = pdfHelper.get_pdf_save_picture_path(file_name, page_num, pdf_info.image_count, 'jpg')
            if pdf_info.is_pure_picture:
                image_text = pdf_info.text_each_images_pages[page_num][pdf_info.image_count - 1]
            else:
                image_text = pdfHelper.get_text_from_image_with_save(image.data, image_path)
            

            page_text_md += image_text
            page_text_txt += image_text

            # 在 Markdown 中显示图片
            if insert_images:
                page_text_md += '\n' f'![[{os.path.basename(image_path)}]]' + '\n'*2

        # 合并断开的行
        if force_join_broken_line:
            page_text_md, page_completed = pdfHelper.join_broken_line(page_text_md, line_max_char_count, line_char_count_tolerance)
            is_page_last_line_completed[page_num] = page_completed
            page_text_txt, page_completed = pdfHelper.join_broken_line(page_text_txt, line_max_char_count, line_char_count_tolerance)
            
        # 识别书签，并修改为 Markdown 标题 
        page_text_md = format_markdown_header(page_text_md, page_num, bookmarks, page_completed, find_bookmarks)

        # 段落分析，为 Markdown 加便于引用的标记
        page_text_md = add_mark_for_each_paragraph(page_text_md, page_num, page_completed)

        # 纯图片 PDF 把图片第一行（页眉）作为标题的一部分
        if pdf_info.is_pure_picture:            
            # 按标点符号拆分句子
            first_sentence = re.sub(r'\^page-\d+-section-\d+', '', clh.text_split_by_punctuation(page_text_md)[0]).strip()
            # 判断是否每页都有书签
            search = re.search(r'^(#+)\s+(.+)(\s*)$', first_sentence)
            if len(bookmarks) >= pdf_info.page_count and search != None:                    
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
    """
    批量转换一个文件夹下的 PDF
    :param pdf_dir_path: PDF 文件夹路径
    :param output_path: 输出路径
    :param page_as_head: 是否将每页的标题作为 Markdown 的标题
    :param insert_images: 是否将图片插入到 Markdown 中
    :param force_join_broken_line: 是否强制连接断行
    :param line_char_count_tolerance: 超过这个值的断行会被强制连接
    :param show_process: 是否显示处理进度
    :param also_txt: 是否同时输出 txt 文件
    :return: 成功处理的文件数量
    """
    
    # 如果没有指定 PDF 目录，则将 PDF 目录设置为当前脚本所在的目录
    if pdf_dir_path == '':
        pdf_dir_path = os.path.dirname(os.path.realpath(__file__))
    # 如果 PDF 目录不存在，则打印一个错误信息并退出
    if not os.path.exists(pdf_dir_path):
        print(f'路径 {pdf_dir_path} 不存在。')
        return
    # 如果没有指定输出路径，则将输出路径设置为 PDF 目录下的 Convert 文件夹
    if output_path == '':
        output_path = os.path.join(pdf_dir_path, 'Convert')
    # 如果输出路径不存在，则创建输出路径
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # 如果输出路径不存在，则打印一个错误信息并退出
    if not os.path.exists(output_path):
        print(f'输出路径 {output_path} 无法建立。')
        return

    success_count = 0
    for root, dirs, files in os.walk(pdf_dir_path):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                try:
                    # convert PDF to Markdown file
                    pdf2md(file_path, output_path, page_as_head, insert_images, force_join_broken_line, line_char_count_tolerance, show_process, also_txt)
                    success_count += 1
                except Exception as e:
                    print(f"Error processing PDF file: {file_path}")
                    print(f"Error message: {str(e)}")
    return success_count
        

# 测试代码
if __name__ == '__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    pdf_file = 'C:\\Users\\listo\\Desktop\\我的云\\Workspace\\Exercise\\PythonPractise\\PDF 转 MD\\博弈论 ((美) 约翰·冯·诺依曼 著 刘霞 译) (Z-Library).pdf'
    pdf2md(os.path.join(script_path, pdf_file), also_txt=True)

    # dir = ''
    # pdf2md_batch(dir, also_txt=True)

    print(clh.sentence_end_symbols)