from src.bezierlab.bezier import calculate_bezier_curve, get_bezier_poit_at_t
from PIL import ImageGrab

import tkinter as tk

class BezierLabApp:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.title("BézierLab")
        
