import re

def load_text(path):
    print(f"DEBUG: Reading file: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text.replace('\r\n', '\n').replace('\r', '\n')

def split_by_marker(text, marker):
    return text.split(marker)

def split_text(text, max_chars):
    pages = []
    for i in range(0, len(text), max_chars):
        pages.append(text[i:i+max_chars])
    return pages
