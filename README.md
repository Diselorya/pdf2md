# pdf2md

Convert PDF to Markdown and TXT, especially for obsidian.

Due to the use of the pytesseract library, it is necessary to manually install the Tesseract-OCR software and add system variables. For detailed methods, please refer to: [基于pytesseract进行图片文字识别 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/561216149)


- [X] Get content:
  - [X] Convert text pdf.
  - [X] Convert picture pdf by ocr.
    - [ ] Higher OCR recognition accuracy.
  - [X] Save pictures and insert to markdown by obsidian way.
- [X] Fix broken sentences. (most but not 100%)
  - [ ] Need to optimize based on more samples.
  - [ ] AI assisted recognition of sentence breaks.
- [X] Add headings:
  - [X] Convert pdf bookmarks to headings.
  - [X] Use page number as headings for picture pdf.
    - [X] Fetch first sentence for page number headings.
    - [ ] Compare the headers, catalog, and page numbers to identify the levels of headings.
- [X] Filename handling:
  - [X] Fix unsupported characters in filename.
  - [X] Replace characters conflicting with obsidian in filename.
- [X] Character encoding problem handling:
  - [X] Normalise the same character but different unicode, which can't read by TTS.
- [X] Batch convert.
- [ ] Catalog: Replace catalog to obsidian way. (little significance)
