import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk, ImageOps
import ttkbootstrap as tb
from ttkbootstrap.constants import *


class PaintController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.last_x = None
        self.last_y = None
        self.shape_start_x = None
        self.shape_start_y = None
        self.current_shape_id = None

        # Привязываем события
        self.view.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.view.canvas.bind("<B1-Motion>", self.on_move_press)
        self.view.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.view.palette_canvas.bind("<Button-1>", self.pick_color)
        self.view.pencil_button.config(command=self.use_pencil)
        self.view.eraser_button.config(command=self.use_eraser)  # Привязка кнопки ластика
        self.view.fill_button.config(command=self.use_fill)
        self.view.shape_button.config(command=self.use_shape)
        self.view.custom_color_button.config(command=self.choose_color)

        self.view.opacity_scale.config(command=self.change_opacity)
        self.view.size_combobox.bind("<<ComboboxSelected>>", self.change_size)  # Привязка изменения размера

        self.view.grayscale_button.config(command=self.apply_grayscale)
        self.view.sepia_button.config(command=self.apply_sepia)
        self.view.invert_button.config(command=self.apply_invert)

        self.view.save_button.config(command=self.save_image)
        self.view.load_button.config(command=self.load_image)

        self.view.rectangle_radio.config(command=self.update_shape_type)
        self.view.oval_radio.config(command=self.update_shape_type)

        # Создаём палитру
        palette_image = self.model.create_palette_image(300)
        self.palette_photo = ImageTk.PhotoImage(palette_image.resize((200, 200)))
        self.view.palette_canvas.create_image(0, 0, anchor='nw', image=self.palette_photo)
        # Сохраняем ссылку
        self.view.palette_photo_ref = self.palette_photo

        self.view.update_canvas()

    def use_pencil(self):
        self.model.set_tool("pencil")
        # Устанавливаем размер кисти из комбобокса
        size = self.get_current_size()
        self.model.set_brush_size(size)

    def use_eraser(self):
        self.model.set_tool("eraser")
        # Устанавливаем размер ластика из комбобокса
        size = self.get_current_size()
        self.model.set_eraser_size(size)

    def use_fill(self):
        self.model.set_tool("fill")

    def use_shape(self):
        self.model.set_tool("shape")
        self.model.set_shape_type(self.view.shape_var.get())

    def update_shape_type(self):
        self.model.set_shape_type(self.view.shape_var.get())

    def choose_color(self):
        color = self.view.ask_color(self.model.brush_color)
        if color:
            self.model.set_brush_color(color)

    def change_opacity(self, value):
        opacity_percent = float(value)
        self.model.set_brush_opacity(opacity_percent)
        self.view.opacity_value_label.config(text=f"{int(opacity_percent)}%")

    def change_size(self, event):
        size = self.get_current_size()
        tool = self.model.current_tool
        if tool == "pencil":
            self.model.set_brush_size(size)
        elif tool == "eraser":
            self.model.set_eraser_size(size)

    def get_current_size(self):
        try:
            size = int(self.view.size_combobox.get())
            return size
        except ValueError:
            return 5  # Значение по умолчанию

    def pick_color(self, event):
        # Определяем цвет из палитры
        x_ratio = event.x / 200
        y_ratio = event.y / 200
        hue = x_ratio
        saturation = 1 - y_ratio
        r, g, b = self.model.hsv_to_rgb(hue, saturation, 1)
        hex_color = '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
        self.model.set_brush_color(hex_color)

    def on_button_press(self, event):
        tool = self.model.current_tool
        if tool in ["pencil", "eraser"]:
            self.last_x, self.last_y = event.x, event.y
        elif tool == "fill":
            self.model.flood_fill(event.x, event.y)
            self.view.update_canvas()
        elif tool == "shape":
            self.shape_start_x, self.shape_start_y = event.x, event.y
            # Прорисовка временной фигуры на Canvas
            if self.model.shape_type == "rectangle":
                self.current_shape_id = self.view.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                                          outline=self.model.brush_color, width=2)
            elif self.model.shape_type == "oval":
                self.current_shape_id = self.view.canvas.create_oval(event.x, event.y, event.x, event.y,
                                                                     outline=self.model.brush_color, width=2)

    def on_move_press(self, event):
        tool = self.model.current_tool
        if tool == "pencil":
            x, y = event.x, event.y
            # Рисуем только в PIL изображении
            if self.last_x is not None and self.last_y is not None:
                self.model.draw_pencil_line(self.last_x, self.last_y, x, y)
                self.last_x, self.last_y = x, y
                self.view.update_canvas()
        elif tool == "eraser":
            x, y = event.x, event.y
            if self.last_x is not None and self.last_y is not None:
                self.model.draw_eraser_line(self.last_x, self.last_y, x, y)
                self.last_x, self.last_y = x, y
                self.view.update_canvas()
        elif tool == "shape" and self.current_shape_id is not None:
            # Двигаем временную фигуру
            self.view.canvas.coords(self.current_shape_id, self.shape_start_x, self.shape_start_y, event.x, event.y)

    def on_button_release(self, event):
        tool = self.model.current_tool
        if tool == "shape" and self.current_shape_id is not None:
            x0, y0 = self.shape_start_x, self.shape_start_y
            x1, y1 = event.x, event.y
            self.model.draw_shape(x0, y0, x1, y1)
            self.view.update_canvas()
            self.view.canvas.delete(self.current_shape_id)
            self.current_shape_id = None

    def save_image(self):
        file_path = self.view.ask_save_path()
        if file_path:
            self.model.image.save(file_path)
            self.view.show_info("Сохранение", f"Изображение сохранено как {file_path}")

    def load_image(self):
        file_path = self.view.ask_load_path()
        if file_path and os.path.exists(file_path):
            loaded_image = Image.open(file_path).convert("RGBA").resize((self.model.width, self.model.height))
            self.model.image = loaded_image
            self.model.draw = ImageDraw.Draw(self.model.image, 'RGBA')
            self.view.update_canvas()
            self.view.show_info("Загрузка", f"Изображение загружено из {file_path}")

    def apply_grayscale(self):
        self.model.apply_grayscale()
        self.view.update_canvas()

    def apply_sepia(self):
        self.model.apply_sepia()
        self.view.update_canvas()

    def apply_invert(self):
        self.model.apply_invert()
        self.view.update_canvas()