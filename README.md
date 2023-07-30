# pdf2md

Convert PDF to Markdown and TXT, especially for obsidian.

- [x] Get content:
    - [x] Convert text pdf.
    - [x] Convert picture pdf by ocr.
        - [ ] Higher OCR recognition accuracy.
    - [x] Save pictures and insert to markdown by obsidian way.
- [x] Fix broken sentences. (most but not 100%)
    - [ ] Need to optimize based on more samples.
    - [ ] AI assisted recognition of sentence breaks.
- [x] Add headings:
    - [x] Convert pdf bookmarks to headings.
    - [x] Use page number as headings for picture pdf.
        - [x] Fetch first sentence for page number headings.
        - [ ] Compare the headers, catalog, and page numbers to identify the levels of headings.
- [x] Filename handling:
    - [x] Fix unsupported characters in filename.
    - [x] Replace characters conflicting with obsidian in filename.
- [x] Character encoding problem handling:
    - [x] Normalise the same character but different unicode, which can't read by TTS.
- [x] Batch convert.
- [ ] Catalog: Replace catalog to obsidian way. (little significance)
