import json
from PIL import Image, ImageDraw, ImageFont

class Template:
    def __init__(self, config):
        self.width = config.get('width', 1080)
        self.height = config.get('height', 1920)
        self.background_color = config.get('background_color', '#FFFFFF')
        self.background_image = config.get('background_image')
        self.font_path = config.get('font_path', 'arial.ttf')
        self.font_size = config.get('font_size', 48)
        self.font_color = config.get('font_color', '#000000')
        self.line_spacing = config.get('line_spacing', 1.5)
        self.margins = config.get('margins', {'top':100,'bottom':100,'left':100,'right':100})
        self.font = ImageFont.truetype(self.font_path, self.font_size)

    @classmethod
    def from_json(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return cls(config)
