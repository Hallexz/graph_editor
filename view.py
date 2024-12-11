import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk, ImageOps
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class PaintView:
    def __init__(self, root, model):
        self.root = root
        self.model = model
        self.root.title("Графический Редактор")
        # Позволяем ресайз окна
        self.root.resizable(True, True)

        # Настройка темы ttkbootstrap
        self.style = tb.Style(theme='darkly')
        self.style.configure('TFrame', background="#11111A")
        self.style.configure('TButton', font=('Segoe UI', 12, 'bold'), foreground='white')
        self.style.configure('TLabel', font=('Segoe UI', 12, 'bold'), foreground='white')
        self.style.configure('TRadiobutton', font=('Segoe UI', 12, 'bold'), foreground='white')

        # Основной контейнер - PanedWindow для разделения на левую (холст) и правую (панель инструментов) части
        self.paned = ttk.Panedwindow(self.root, orient='horizontal')
        self.paned.pack(fill="both", expand=True)

        # Фрейм для холста
        self.canvas_frame = ttk.Frame(self.paned)
        self.canvas_frame.pack(fill="both", expand=True)

        # Холст
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Фрейм инструментов
        self.toolbar_frame = ttk.Frame(self.paned)
        self.toolbar_frame.pack(fill="y", expand=False, padx=5, pady=5)
        self.paned.add(self.canvas_frame, weight=3)
        self.paned.add(self.toolbar_frame, weight=1)

        # Кнопки инструментов
        self.pencil_button = ttk.Button(self.toolbar_frame, text="Карандаш")
        self.pencil_button.pack(pady=5)

        self.eraser_button = ttk.Button(self.toolbar_frame, text="Ластик")  # Новая кнопка ластика
        self.eraser_button.pack(pady=5)

        self.fill_button = ttk.Button(self.toolbar_frame, text="Заливка")
        self.fill_button.pack(pady=5)

        self.shape_button = ttk.Button(self.toolbar_frame, text="Фигура")
        self.shape_button.pack(pady=5)

        # Палитра
        self.palette_label = ttk.Label(self.toolbar_frame, text="Палитра Цветов:")
        self.palette_label.pack(pady=(20, 5))
        self.palette_canvas = tk.Canvas(self.toolbar_frame, width=200, height=200, bd=2, relief=tk.SUNKEN)
        self.palette_canvas.pack()

        # Кнопка пользовательского цвета
        self.custom_color_button = ttk.Button(self.toolbar_frame, text="Пользовательский Цвет")
        self.custom_color_button.pack(pady=(10, 15))

        # Прозрачность
        self.opacity_label = ttk.Label(self.toolbar_frame, text="Прозрачность:")
        self.opacity_label.pack(pady=(10, 5))
        self.opacity_scale = ttk.Scale(self.toolbar_frame, from_=0, to=100, orient='horizontal')
        self.opacity_scale.set(100)
        self.opacity_scale.pack(pady=5, fill="x")
        self.opacity_value_label = ttk.Label(self.toolbar_frame, text="100%")
        self.opacity_value_label.pack(pady=(0, 15))

        # Размер инструмента
        self.size_label = ttk.Label(self.toolbar_frame, text="Размер Инструмента:")
        self.size_label.pack(pady=(10, 5))
        self.size_combobox = ttk.Combobox(self.toolbar_frame, values=[1, 2, 5, 10, 15, 20, 25, 30], state='readonly')
        self.size_combobox.set(5)  # Значение по умолчанию
        self.size_combobox.pack(pady=5, fill="x")

        # Фильтры
        self.filters_label = ttk.Label(self.toolbar_frame, text="Фильтры:")
        self.filters_label.pack(pady=(10, 5))

        self.grayscale_button = ttk.Button(self.toolbar_frame, text="Градация Серого")
        self.grayscale_button.pack(pady=5)

        self.sepia_button = ttk.Button(self.toolbar_frame, text="Сепия")
        self.sepia_button.pack(pady=5)

        self.invert_button = ttk.Button(self.toolbar_frame, text="Инверсия")
        self.invert_button.pack(pady=5)

        # Сохранение/загрузка
        self.save_button = ttk.Button(self.toolbar_frame, text="Сохранить")
        self.save_button.pack(pady=15)

        self.load_button = ttk.Button(self.toolbar_frame, text="Загрузить")
        self.load_button.pack(pady=5)

        # Выбор фигуры
        self.shape_var = tk.StringVar(value="rectangle")
        self.rectangle_radio = ttk.Radiobutton(self.toolbar_frame, text="Прямоугольник", variable=self.shape_var, value="rectangle")
        self.rectangle_radio.pack(anchor=tk.W, pady=2)

        self.oval_radio = ttk.Radiobutton(self.toolbar_frame, text="Эллипс", variable=self.shape_var, value="oval")
        self.oval_radio.pack(anchor=tk.W, pady=2)

        # Создание шахматной палитры
        self.checkerboard_image = self.create_checkerboard()
        self.checkerboard_photo = ImageTk.PhotoImage(self.checkerboard_image)
        self.checkerboard_canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.checkerboard_photo)

        # Отображение основного изображения
        self.photo_image = ImageTk.PhotoImage(self.model.image)
        self.drawing_canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Сохранение ссылок на изображения, чтобы они не были удалены сборщиком мусора
        self.checkerboard_photo_ref = self.checkerboard_photo
        self.drawing_photo_ref = self.photo_image

    def create_checkerboard(self, size=10, color1=(200, 200, 200), color2=(150, 150, 150)):
        """Создаёт шахматную палитру для отображения прозрачных областей."""
        checkerboard = Image.new("RGB", (self.model.width, self.model.height), color1)
        draw = ImageDraw.Draw(checkerboard)
        for y in range(0, self.model.height, size):
            for x in range(0, self.model.width, size):
                if (x // size + y // size) % 2 == 0:
                    draw.rectangle([x, y, x+size, y+size], fill=color2)
        return checkerboard

    def update_canvas(self):
        """Обновляет изображение на холсте."""
        self.photo_image = ImageTk.PhotoImage(self.model.image)
        self.canvas.itemconfig(self.drawing_canvas_image, image=self.photo_image)
        # Обновляем ссылку, чтобы избежать удаления изображения
        self.drawing_photo_ref = self.photo_image
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def ask_color(self, initial_color):
        color = colorchooser.askcolor(color=initial_color)[1]
        return color

    def ask_save_path(self):
        return filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG files","*.png"), ("All files","*.*")])

    def ask_load_path(self):
        return filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files","*.*")])

    def show_info(self, title, message):
        messagebox.showinfo(title, message)