from PIL import Image, ImageDraw, ImageOps
import colorsys
from PIL import Image, ImageDraw, ImageTk, ImageOps
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class PaintModel:
    def __init__(self, width=1000, height=700):
        self.width = width
        self.height = height
        self.brush_size = 5
        self.eraser_size = 10  # Размер ластика по умолчанию
        self.brush_color = "#7C7DC9"  
        self.brush_opacity = 255
        self.current_tool = "pencil"  
        self.shape_type = "rectangle"
        self.image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))  # Прозрачный фон
        self.draw = ImageDraw.Draw(self.image, 'RGBA')

    def set_brush_color(self, color):
        self.brush_color = color

    def set_brush_opacity(self, percent):
        self.brush_opacity = int((percent / 100) * 255)

    def set_tool(self, tool):
        self.current_tool = tool

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type

    def set_brush_size(self, size):
        self.brush_size = size

    def set_eraser_size(self, size):
        self.eraser_size = size

    def hex_to_rgba(self, hex_color, opacity):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (r, g, b, opacity)
        elif len(hex_color) == 3:
            r, g, b = tuple(int(hex_color[i]*2, 16) for i in (0, 1, 2))
            return (r, g, b, opacity)
        else:
            return (255, 255, 255, opacity)  # fallback

    def draw_pencil_line(self, x0, y0, x1, y1):
        rgba_color = self.hex_to_rgba(self.brush_color, self.brush_opacity)
        self.draw.line([x0, y0, x1, y1], fill=rgba_color, width=self.brush_size)

    def draw_eraser_line(self, x0, y0, x1, y1):
        # Ластик устанавливает прозрачность пикселей
        rgba_color = (0, 0, 0, 0)  # Полностью прозрачный
        self.draw.line([x0, y0, x1, y1], fill=rgba_color, width=self.eraser_size)

    def draw_shape(self, x0, y0, x1, y1):
        rgba_color = self.hex_to_rgba(self.brush_color, self.brush_opacity)
        if self.shape_type == "rectangle":
            self.draw.rectangle([x0, y0, x1, y1], outline=rgba_color, width=2)
        elif self.shape_type == "oval":
            self.draw.ellipse([x0, y0, x1, y1], outline=rgba_color, width=2)

    def flood_fill(self, x, y):
        # Заливка
        pixels = self.image.load()
        width, height = self.image.size
        try:
            target_color = pixels[x, y]
        except IndexError:
            return

        fill_color_rgba = self.hex_to_rgba(self.brush_color, self.brush_opacity)
        if target_color == fill_color_rgba:
            return

        stack = [(x, y)]
        while stack:
            nx, ny = stack.pop()
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if pixels[nx, ny] != target_color:
                continue
            pixels[nx, ny] = fill_color_rgba
            stack.extend([(nx+1, ny), (nx-1, ny), (nx, ny+1), (nx, ny-1)])

    def apply_grayscale(self):
        self.image = ImageOps.grayscale(self.image).convert("RGBA")
        self.draw = ImageDraw.Draw(self.image, 'RGBA')

    def apply_sepia(self):
        sepia_image = ImageOps.grayscale(self.image).convert("RGBA")
        width, height = sepia_image.size
        pixels = sepia_image.load()
        for py in range(height):
            for px in range(width):
                gray = pixels[px, py][0]
                r = min(int(gray * 1.3), 255)
                g = min(int(gray * 1.1), 255)
                b = min(int(gray * 0.9), 255)
                pixels[px, py] = (r, g, b, 255)
        self.image = sepia_image
        self.draw = ImageDraw.Draw(self.image, 'RGBA')

    def apply_invert(self):
        alpha = self.image.split()[-1]
        rgb_image = self.image.convert("RGB")
        inverted_image = ImageOps.invert(rgb_image).convert("RGBA")
        inverted_image.putalpha(alpha)
        self.image = inverted_image
        self.draw = ImageDraw.Draw(self.image, 'RGBA')

    def hsv_to_rgb(self, h, s, v):
        return colorsys.hsv_to_rgb(h, s, v)

    def create_palette_image(self, resolution=300):
        """Создаёт палитру цветов для выбора."""
        palette_image = Image.new("RGB", (resolution, resolution))
        for x in range(resolution):
            for y in range(resolution):
                hue = x / resolution
                saturation = 1 - y / resolution
                r, g, b = self.hsv_to_rgb(hue, saturation, 1)
                palette_image.putpixel((x, y), (int(r*255), int(g*255), int(b*255)))
        return palette_image