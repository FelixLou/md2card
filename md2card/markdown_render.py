import mistune
from PIL import Image, ImageDraw, ImageFont
import pprint
import os
import re

# Basic style mapping for markdown elements
STYLE_MAP = {
    'heading': {
        1: {'font_size': 36, 'font_color': '#222222', 'bold': True},
        2: {'font_size': 32, 'font_color': '#FF6600', 'bold': True},
        3: {'font_size': 28, 'font_color': '#FF6600', 'bold': True},
        4: {'font_size': 24, 'font_color': '#333333', 'bold': True},
        5: {'font_size': 20, 'font_color': '#333333', 'bold': True},
        6: {'font_size': 18, 'font_color': '#333333', 'bold': True},
    },
    'paragraph': {'font_size': 24, 'font_color': '#333333'},
    'list': {'font_size': 24, 'font_color': '#333333'},
    'blockquote': {'font_size': 24, 'font_color': '#FF6600', 'bg_color': '#FFF3E0'},
    'strong': {'bold': True},
    'emphasis': {'italic': True},
}

# 常见系统字体路径
BOLD_FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",  # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 备选
    "/System/Library/Fonts/Microsoft/SimHei.ttf",  # Windows
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",  # Linux
]

def get_font(font_path, font_size, bold=False, italic=False):
    # 尝试加载粗体字体
    if bold:
        # 尝试常见的粗体字体文件
        for bold_path in BOLD_FONT_PATHS:
            if os.path.exists(bold_path):
                try:
                    return ImageFont.truetype(bold_path, font_size)
                except:
                    pass
                    
        # 如果无法找到粗体字体，尝试用字体索引
        try:
            return ImageFont.truetype(font_path, font_size, index=1)  # 尝试索引1作为Bold
        except:
            pass
            
        # 最后的回退：模拟粗体（通过多次绘制）
        print("使用模拟粗体")
        return ImageFont.truetype(font_path, font_size)
    else:
        return ImageFont.truetype(font_path, font_size)

def wrap_text(text, font, max_width, draw):
    # 逐字符累加，超宽就换行，适配中英文、长单词、长数字
    lines = []
    current_line = ''
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

def extract_text_from_ast(ast):
    # Recursively extract text from AST nodes, including 'raw' field
    if isinstance(ast, str):
        return ast
    if isinstance(ast, list):
        return ''.join([extract_text_from_ast(item) for item in ast])
    if isinstance(ast, dict):
        if 'raw' in ast:
            return ast['raw']
        if 'children' in ast and ast['children']:
            return extract_text_from_ast(ast['children'])
        if 'text' in ast:
            return ast['text']
        # 尝试提取所有可能的文本字段
        for field in ['content', 'value', 'literal']:
            if field in ast:
                return ast[field]
    return ''

def draw_rounded_rectangle(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)

def measure_text(text, style, font_path, max_text_width, draw, line_spacing, bg=None, pad_x=0, pad_y=0):
    font = get_font(font_path, style.get('font_size', 48))
    lines = wrap_text(text, font, max_text_width if not bg else max_text_width-2*pad_x, draw)
    total_height = 0
    for line in lines:
        bbox = font.getbbox(line)
        h = bbox[3] - bbox[1]
        total_height += h * line_spacing
    if bg:
        total_height += 2*pad_y
    return total_height

def measure_node(node, x, y, draw, template, parent_style=None):
    node_type = node.get('type')
    width, height = template.width, template.height
    line_spacing = template.line_spacing
    font_path = template.font_path
    max_text_width = width - template.margins['left'] - template.margins['right']
    if node_type == 'heading':
        level = node.get('level', 1)
        style = STYLE_MAP['heading'].get(level, STYLE_MAP['heading'][1])
        text = extract_text_from_ast(node.get('children', ''))
        h = measure_text(text, style, font_path, max_text_width, draw, line_spacing)
        return h + 18
    elif node_type == 'paragraph':
        style = STYLE_MAP['paragraph']
        text = extract_text_from_ast(node.get('children', ''))
        h = measure_text(text, style, font_path, max_text_width, draw, line_spacing)
        return h
    elif node_type == 'list':
        style = STYLE_MAP['list']
        total = 0
        for item in node.get('children', []):
            text = '• ' + extract_text_from_ast(item.get('children', ''))
            h = measure_text(text, style, font_path, max_text_width, draw, line_spacing)
            total += h
        return total
    elif node_type == 'blockquote':
        style = STYLE_MAP['blockquote']
        total_height = 0
        padding = 24
        
        for child in node.get('children', []):
            child_text = extract_text_from_ast(child.get('children', ''))
            font = get_font(font_path, style.get('font_size', template.font_size), 
                           bold=style.get('bold', False), 
                           italic=style.get('italic', False))
            lines = wrap_text(child_text, font, max_text_width - 30, draw)
            for line in lines:
                bbox = font.getbbox(line)
                h = bbox[3] - bbox[1]
                total_height += h * line_spacing
                
        return total_height + padding
    elif node_type == 'thematic_break':
        return 36
    elif node_type == 'strong' or node_type == 'emphasis':
        style = parent_style.copy() if parent_style else {}
        if node_type == 'strong':
            style['bold'] = True
        if node_type == 'emphasis':
            style['italic'] = True
        text = extract_text_from_ast(node.get('children', ''))
        h = measure_text(text, style, font_path, max_text_width, draw, line_spacing)
        return h
    elif node_type == 'text':
        style = parent_style if parent_style else STYLE_MAP['paragraph']
        h = measure_text(node.get('text', ''), style, font_path, max_text_width, draw, line_spacing)
        return h
    else:
        total = 0
        if 'children' in node:
            for child in node['children']:
                total += measure_node(child, x, y, draw, template, parent_style)
        return total

def paginate_ast_by_height(ast, template):
    width, height = template.width, template.height
    x = template.margins['left']
    y = template.margins['top']
    nav_height = 100
    y_start = nav_height + 30
    max_y = height - template.margins['bottom']
    # 用于测量的虚拟画布
    img = Image.new('RGB', (width, height), template.background_color)
    draw = ImageDraw.Draw(img)
    pages = []
    current_page = []
    current_y = y_start
    for node in ast:
        h = measure_node(node, x, current_y, draw, template)
        if current_y + h > max_y and current_page:
            pages.append(current_page)
            current_page = []
            current_y = y_start
        current_page.append(node)
        current_y += h
    if current_page:
        pages.append(current_page)
    return pages

def render_ast_page(ast_nodes, template, output_path):
    width, height = template.width, template.height
    img = Image.new('RGB', (width, height), template.background_color)
    draw = ImageDraw.Draw(img)
    x = template.margins['left']
    y = template.margins['top']
    line_spacing = template.line_spacing
    font_path = template.font_path
    max_text_width = width - template.margins['left'] - template.margins['right']
    # 顶部导航栏
    nav_height = 100
    nav_font = get_font(font_path, 38)
    # 不绘制背景色
    from PIL import Image as PILImage
    # 左侧返回icon
    try:
        icon_left = PILImage.open('assets/chevron.left@3x.png').convert('RGBA')
        icon_left = icon_left.resize((48, 48))
        img.paste(icon_left, (x, 32), icon_left)
    except Exception as e:
        pass
    # 标题
    draw.text((x+60, 32), '备忘录', font=nav_font, fill='#FFD60A')
    # 右侧上传icon
    try:
        icon_upload = PILImage.open('assets/square.and.arrow.up@3x.png').convert('RGBA')
        icon_upload = icon_upload.resize((48, 48))
        img.paste(icon_upload, (width-x-120, 32), icon_upload)
    except Exception as e:
        pass
    # 右上角更多按钮
    try:
        icon_more = PILImage.open('assets/ellipsis.circle@3x.png').convert('RGBA')
        icon_more = icon_more.resize((48, 48))
        img.paste(icon_more, (width-x-40, 32), icon_more)
    except Exception as e:
        pass
    y = nav_height + 30
    def draw_text(text, style, x, y, bg=None, radius=0, pad_x=0, pad_y=0):
        is_bold = style.get('bold', False)
        font = get_font(font_path, style.get('font_size', template.font_size), 
                       bold=is_bold, 
                       italic=style.get('italic', False))
        color = style.get('font_color', template.font_color)
        lines = wrap_text(text, font, max_text_width if not bg else max_text_width-2*pad_x, draw)
        total_height = 0
        if bg:
            h = 0
            for line in lines:
                bbox = font.getbbox(line)
                h += bbox[3] - bbox[1]
            h = h * line_spacing + 2*pad_y
            draw_rounded_rectangle(draw, [x-pad_x, y-pad_y, x+max_text_width+pad_x, y+h], radius, fill=bg)
        for line in lines:
            # 如果是粗体但没有粗体字体，通过多次绘制模拟
            draw.text((x, y), line, font=font, fill=color)
            if is_bold and font == ImageFont.truetype(font_path, style.get('font_size', template.font_size)):
                # 模拟粗体效果 - 轻微偏移多次绘制
                draw.text((x+1, y), line, font=font, fill=color)
                draw.text((x, y+1), line, font=font, fill=color)
            bbox = font.getbbox(line)
            h = bbox[3] - bbox[1]
            y += h * line_spacing
            total_height += h * line_spacing
        return total_height
    def render_node(node, x, y, parent_style=None):
        node_type = node.get('type')
        
        # 打印节点信息，便于调试
        if node_type in ['blockquote', 'block_quote']:
            print(f"发现引用节点类型: {node_type}, 内容: {extract_text_from_ast(node)}")
            node_type = 'blockquote'  # 统一为blockquote类型
        
        if node_type == 'heading':
            level = node.get('level', 1)
            style = STYLE_MAP['heading'].get(level, STYLE_MAP['heading'][1])
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            return y + h + 18
        elif node_type == 'paragraph':
            style = STYLE_MAP['paragraph']
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            return y + h
        elif node_type == 'list':
            style = STYLE_MAP['list']
            for item in node.get('children', []):
                text = '• ' + extract_text_from_ast(item.get('children', ''))
                h = draw_text(text, style, x, y)
                y += h
            return y
        elif node_type == 'blockquote':
            print("正在渲染blockquote:", node)
            style = STYLE_MAP['blockquote']
            bg_color = style.get('bg_color', '#FFF3E0')
            quote_x = x - 18
            quote_y1 = y
            
            # 先测量引用内容的总高度
            total_height = 0
            temp_y = y
            for child in node.get('children', []):
                child_text = extract_text_from_ast(child.get('children', []))
                if not child_text:
                    child_text = extract_text_from_ast(child)
                print("引用内容文本:", child_text)
                font = get_font(font_path, style.get('font_size', template.font_size), 
                               bold=style.get('bold', False), 
                               italic=style.get('italic', False))
                lines = wrap_text(child_text, font, max_text_width - 30, draw)
                for line in lines:
                    bbox = font.getbbox(line)
                    h = bbox[3] - bbox[1]
                    total_height += h * line_spacing
            
            # 如果高度太小，设置最小高度
            if total_height < 50:
                total_height = 50
            
            # 绘制背景和左侧边框
            padding = 24
            quote_bg_x1 = quote_x + 4
            quote_bg_y1 = y - padding//2
            quote_bg_x2 = x + max_text_width
            quote_bg_y2 = y + total_height + padding//2
            
            # 绘制圆角背景
            draw_rounded_rectangle(draw, [quote_bg_x1, quote_bg_y1, quote_bg_x2, quote_bg_y2], 
                                 radius=16, fill=bg_color)
            
            # 绘制左侧橙色边框
            quote_y2 = y + total_height + padding//2
            draw.line([quote_x, quote_y1, quote_x, quote_y2], fill='#FFB300', width=8)
            
            # 渲染引用内容文本
            original_y = y
            for child in node.get('children', []):
                child_text = extract_text_from_ast(child.get('children', []))
                if not child_text:
                    child_text = extract_text_from_ast(child)
                if child_text:
                    h = draw_text(child_text, style, x + 16, y)
                    y += h
            
            # 确保即使无文本也返回合适高度
            if y == original_y:
                return original_y + total_height + padding
            
            return y + padding//2
        elif node_type == 'thematic_break':
            line_y = y + 18
            draw.line([x, line_y, width-template.margins['right'], line_y], fill='#E5E5E5', width=6)
            return line_y + 18
        elif node_type == 'strong':
            style = parent_style.copy() if parent_style else STYLE_MAP['paragraph'].copy()
            style['bold'] = True
            style['font_color'] = '#000000'  # 确保加粗文本颜色足够深
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            return y + h
        elif node_type == 'emphasis':
            style = parent_style.copy() if parent_style else {}
            style['italic'] = True
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            return y + h
        elif node_type == 'delete':
            style = parent_style.copy() if parent_style else STYLE_MAP['paragraph'].copy()
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            # 画删除线
            font = get_font(font_path, style.get('font_size', template.font_size))
            bbox = font.getbbox(text)
            mid_y = y + (bbox[3] - bbox[1]) // 2
            draw.line([x, mid_y, x + bbox[2] - bbox[0], mid_y], fill='#888888', width=3)
            return y + h
        elif node_type == 'code':
            # 代码块
            code_text = node.get('raw', '')
            code_font = get_font(font_path, 28)
            code_bg = '#F5F5F5'
            pad = 16
            lines = code_text.split('\n')
            h = 0
            for line in lines:
                bbox = code_font.getbbox(line)
                h += bbox[3] - bbox[1] + 8
            draw_rounded_rectangle(draw, [x-pad, y-pad, x+max_text_width+pad, y+h+pad], radius=12, fill=code_bg)
            yy = y
            for line in lines:
                draw.text((x, yy), line, font=code_font, fill='#333333')
                bbox = code_font.getbbox(line)
                yy += bbox[3] - bbox[1] + 8
            return y + h + 2*pad
        elif node_type == 'inline_code':
            # 行内代码
            code_text = node.get('raw', '')
            code_font = get_font(font_path, 28)
            code_bg = '#F5F5F5'
            pad = 6
            bbox = code_font.getbbox(code_text)
            h = bbox[3] - bbox[1]
            w = bbox[2] - bbox[0]
            draw_rounded_rectangle(draw, [x, y, x+w+2*pad, y+h+2*pad], radius=6, fill=code_bg)
            draw.text((x+pad, y+pad), code_text, font=code_font, fill='#333333')
            return y + h + 2*pad
        elif node_type == 'link':
            # 链接文本蓝色下划线
            style = parent_style.copy() if parent_style else STYLE_MAP['paragraph'].copy()
            style['font_color'] = '#1976D2'
            text = extract_text_from_ast(node.get('children', ''))
            h = draw_text(text, style, x, y)
            font = get_font(font_path, style.get('font_size', template.font_size))
            bbox = font.getbbox(text)
            underline_y = y + bbox[3] - bbox[1]
            draw.line([x, underline_y, x + bbox[2] - bbox[0], underline_y], fill='#1976D2', width=2)
            return y + h
        elif node_type == 'image':
            # 简单插入图片（缩放到最大宽度）
            from PIL import Image as PILImage
            img_path = node.get('src') or node.get('url')
            try:
                pil_img = PILImage.open(img_path)
                ratio = min(max_text_width / pil_img.width, 1.0)
                new_w = int(pil_img.width * ratio)
                new_h = int(pil_img.height * ratio)
                pil_img = pil_img.resize((new_w, new_h))
                img.paste(pil_img, (x, y))
                return y + new_h + 10
            except Exception as e:
                h = draw_text('[图片加载失败]', STYLE_MAP['paragraph'], x, y)
                return y + h
        elif node_type == 'break':
            return y + 12
        elif node_type == 'table':
            # 简单表格渲染
            cell_pad = 12
            row_h = 0
            col_w = []
            # 先计算最大列宽
            for row in node.get('children', []):
                for i, cell in enumerate(row.get('children', [])):
                    text = extract_text_from_ast(cell.get('children', ''))
                    font = get_font(font_path, 32)
                    bbox = font.getbbox(text)
                    w = bbox[2] - bbox[0]
                    if len(col_w) <= i:
                        col_w.append(w)
                    else:
                        col_w[i] = max(col_w[i], w)
            # 渲染表格
            yy = y
            for row in node.get('children', []):
                xx = x
                row_h = 0
                for i, cell in enumerate(row.get('children', [])):
                    text = extract_text_from_ast(cell.get('children', ''))
                    font = get_font(font_path, 32)
                    bbox = font.getbbox(text)
                    w = col_w[i] + 2*cell_pad
                    h = bbox[3] - bbox[1] + 2*cell_pad
                    draw.rectangle([xx, yy, xx+w, yy+h], outline='#CCCCCC', width=2, fill='#FAFAFA')
                    draw.text((xx+cell_pad, yy+cell_pad), text, font=font, fill='#333333')
                    xx += w
                    row_h = max(row_h, h)
                yy += row_h
            return y + (yy - y)
        else:
            if 'children' in node:
                for child in node['children']:
                    y = render_node(child, x, y, parent_style)
            return y
    for node in ast_nodes:
        y = render_node(node, x, y)
    img.save(output_path)

def render_markdown_to_image(md_text, template, output_path):
    # 兼容旧接口，直接渲染为单页图片（不分页）
    md = mistune.create_markdown(renderer='ast')
    ast = md(md_text)
    render_ast_page(ast, template, output_path)

def render_markdown_to_images(md_text, template, output_dir):
    import os
    
    # 预处理Markdown文本，标准化blockquote格式
    lines = md_text.split("\n")
    processed_lines = []
    
    for line in lines:
        if line.strip().startswith(">"):
            # 确保标准blockquote格式
            content = line.strip()[1:].strip()
            processed_lines.append(f"> {content}")
        else:
            processed_lines.append(line)
    
    processed_md = "\n".join(processed_lines)
    
    md = mistune.create_markdown(renderer='ast')
    ast = md(processed_md)
    
    # 手动检测并转换blockquote节点
    def convert_blockquotes(nodes):
        for i, node in enumerate(nodes):
            if isinstance(node, dict):
                if node.get('type') == 'paragraph':
                    # 检查段落内容是否为blockquote
                    text = extract_text_from_ast(node)
                    if text.startswith(">"):
                        # 创建新的blockquote节点
                        content = text[1:].strip()
                        nodes[i] = {
                            'type': 'blockquote',
                            'children': [{
                                'type': 'paragraph',
                                'children': [{
                                    'type': 'text',
                                    'raw': content
                                }]
                            }]
                        }
                        print(f"转换为blockquote: {content}")
                # 递归处理子节点
                if 'children' in node and isinstance(node['children'], list):
                    convert_blockquotes(node['children'])
    
    # 应用转换
    convert_blockquotes(ast)
    
    pages = paginate_ast_by_height(ast, template)
    for i, page_nodes in enumerate(pages, 1):
        out_path = os.path.join(output_dir, f'page_{i:02d}.png')
        render_ast_page(page_nodes, template, out_path) 