import argparse
from .core import generate_cards

def main():
    parser = argparse.ArgumentParser(description='Convert article to Xiaohongshu image cards')
    parser.add_argument('input', help='Path to input text or markdown file')
    parser.add_argument('--template', help='Path to template JSON', default=None)
    parser.add_argument('--output', help='Output directory', default='cards')
    parser.add_argument('--max_chars', type=int, default=1000, help='Max chars per page')
    parser.add_argument('--marker', default='[[PAGE_BREAK]]', help='Manual page break marker')
    args = parser.parse_args()
    generate_cards(args.input, args.output, args.template, args.max_chars, args.marker)

if __name__ == '__main__':
    main()
