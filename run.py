import ttkbootstrap as tb
from model import PaintModel
from view import PaintView
from controller import PaintController

if __name__ == "__main__":
    root = tb.Window()
    model = PaintModel()
    view = PaintView(root, model)
    controller = PaintController(model, view)
    root.mainloop()