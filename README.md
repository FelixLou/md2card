# md2card

一个将Markdown文件转换为小红书风格图片卡片的工具。

## 功能特点

- 支持常见的Markdown语法（标题、粗体、引用块、列表等）
- 自动根据内容高度进行分页
- 支持手动分页标记 (`[[PAGE_BREAK]]`)
- 自定义模板和样式
- 小红书风格美化（导航栏、引用框等）
- 混合分页策略：手动分页+自动分页

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/md2card.git
cd md2card

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发模式
pip install -e .
```

## 使用方法

```bash
# 基本用法
md2card your_markdown_file.md --output output_directory

# 使用自定义模板
md2card your_markdown_file.md --template custom_template.json --output output_directory

# 指定最大字符数和分页标记
md2card your_markdown_file.md --output output_directory --max_chars 500 --marker "[[PAGE_BREAK]]"
```

## 分页说明

md2card支持两种分页方式：

1. **自动分页**：根据内容高度自动计算分页位置
2. **手动分页**：使用`[[PAGE_BREAK]]`标记指定分页位置
3. **混合分页**：手动分页区域内如果内容过长，会自动再次分页

## 自定义模板

可以通过JSON文件自定义卡片样式：

```json
{
  "width": 900,
  "height": 1200,
  "background_color": "#FFFFFF",
  "font_path": "/System/Library/Fonts/PingFang.ttc",
  "font_size": 24,
  "font_color": "#333333",
  "line_spacing": 1.5,
  "margins": {
    "left": 80,
    "right": 80,
    "top": 80,
    "bottom": 80
  }
}
```

## 支持的Markdown语法

- 标题 (h1-h6)
- 粗体和斜体
- 引用块
- 有序和无序列表
- 代码块和行内代码
- 链接
- 图片
- 表格
- 水平分割线

## 许可证

MIT
