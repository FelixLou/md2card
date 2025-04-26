def extract_all_text(node):
    if isinstance(node, dict):
        if 'raw' in node:
            return node['raw']
        elif 'children' in node:
            return ''.join(extract_all_text(child) for child in node['children'])
        else:
            return ''
    elif isinstance(node, list):
        return ''.join(extract_all_text(child) for child in node)
    else:
        return str(node)

import mistune
from PIL import Image, ImageDraw
from .templates import Template
from .utils import load_text
from .markdown_render import render_markdown_to_image, render_markdown_to_images

def paginate_markdown_blocks(md_text, max_chars, marker='[[PAGE_BREAK]]'):
    # 先按 marker 分段
    segments = md_text.split(marker)
    pages = []
    for seg in segments:
        md = mistune.create_markdown(renderer='ast')
        ast = md(seg)
        current_blocks = []
        current_len = 0
        for block in ast:
            block_text = ''
            if block['type'] == 'blank_line':
                block_text = '\n'
            elif block['type'] == 'thematic_break':
                block_text = '---\n'
            elif block['type'] == 'heading':
                level = block.get('attrs', {}).get('level', 1)
                text = extract_all_text(block['children']) if block.get('children') else ''
                block_text = f"{'#'*level} {text}\n"
            elif block['type'] == 'paragraph':
                block_text = extract_all_text(block['children']) + '\n'
            elif block['type'] == 'block_quote':
                for child in block['children']:
                    block_text += '> ' + extract_all_text(child['children']) + '\n'
            elif block['type'] == 'list':
                for item in block['children']:
                    for li in item['children']:
                        block_text += '- ' + extract_all_text(li['children']) + '\n'
            else:
                continue
            if current_len + len(block_text) > max_chars and current_blocks:
                pages.append(''.join(current_blocks))
                current_blocks = []
                current_len = 0
            current_blocks.append(block_text)
            current_len += len(block_text)
        if current_blocks:
            pages.append(''.join(current_blocks))
    return pages

def render_page(text, template, output_path):
    render_markdown_to_image(text, template, output_path)

def generate_cards(input_path, output_dir, template_path=None, max_chars=1000, marker='[[PAGE_BREAK]]'):
    import os
    os.makedirs(output_dir, exist_ok=True)
    text = load_text(input_path)
    print('DEBUG: Text after load_text, before any processing:')
    print(repr(text[:500]))
    tpl = Template.from_json(template_path) if template_path else Template.from_json('default_template.json')
    
    # 先按 marker 分段
    segments = text.split(marker)
    
    # 如果只有一页，按高度自动分页
    if len(segments) == 1:
        render_markdown_to_images(text, tpl, output_dir)
    else:
        # 有手动分页标记，按标记分页处理
        print(f"检测到手动分页标记，分为 {len(segments)} 个区域")
        page_counter = 1  # 页面计数器
        
        for i, segment in enumerate(segments, 1):
            if segment.strip():  # 忽略空段落
                # 对每个区域进行高度测量和自动分页
                md = mistune.create_markdown(renderer='ast')
                ast = md(segment)
                
                # 测量AST树高度，分页
                width, height = tpl.width, tpl.height
                x = tpl.margins['left']
                y = tpl.margins['top']
                nav_height = 100
                y_start = nav_height + 30
                max_y = height - tpl.margins['bottom']
                
                # 临时画布用于测量
                from PIL import Image, ImageDraw
                temp_img = Image.new('RGB', (width, height), tpl.background_color)
                temp_draw = ImageDraw.Draw(temp_img)
                
                # 导入测量函数
                from .markdown_render import measure_node
                
                # 分页
                sub_pages = []
                current_page = []
                current_y = y_start
                
                for node in ast:
                    node_height = measure_node(node, x, current_y, temp_draw, tpl)
                    if current_y + node_height > max_y and current_page:
                        sub_pages.append(current_page)
                        current_page = []
                        current_y = y_start
                    current_page.append(node)
                    current_y += node_height
                
                if current_page:
                    sub_pages.append(current_page)
                
                # 渲染子页面
                for sub_page in sub_pages:
                    out_path = os.path.join(output_dir, f'page_{page_counter:02d}.png')
                    from .markdown_render import render_ast_page
                    render_ast_page(sub_page, tpl, out_path)
                    page_counter += 1
                
                print(f"区域 {i} 分为 {len(sub_pages)} 页")
