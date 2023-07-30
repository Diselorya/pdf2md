from PIL import Image
import cv2
import numpy
import pytesseract
import chineseLanguageHelper as ch
import pathHelper as ph
import terminalHelper as th
import stringHelper as sh

def get_text_from_image_with_save(image_data: bytes, save_path_name: str):
    # 图片输出为文件
    with open(save_path_name, 'wb') as image_file:
        image_file.write(image_data)

    # 将 JPG 格式图片转换为 PIL 格式图片，Tesseract 只支持 PIL（Python Imaging Library）的Image对象 或 OpenCV
    pil_image = Image.open(save_path_name)

    # 使用OCR识别图像中的文本
    image_text = sh.string_normalise(convert_image_to_text(pil_image)) + '\n'
    pil_image.close()

    return image_text


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