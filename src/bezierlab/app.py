import tkinter as tk
from typing import Tuple

from src.bezierlab.bezier import calculate_bezier_curve, get_bezier_poit_at_t
import math

Point = Tuple[float, float]

class BezierLabApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BézierLab")
        self.root.geometry("1000x700")

        self.x_min = 0
        self.x_max = 7
        self.y_min = 0
        self.y_max = 7
        self.padding = 80  # leaves 80px empty around the canvas.

        self.control_points: list[Point] = [
            (1, 1),
            (1, 2.333),
            (4.667, 5),
            (6, 5),
        ]
        self.selected_point_index = None
        self.drag_radius = 12

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Configure>", self.render)

    def to_screen(self, math_x: float, math_y: float) -> Point:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w <= 1 or canvas_h <= 1:
            return 0, 0

        screen_x = self.padding + (
            (math_x - self.x_min)
            / (self.x_max - self.x_min)
            * (canvas_w - 2 * self.padding)
        )
        screen_y = canvas_h - self.padding - (
            (math_y - self.y_min)
            / (self.y_max - self.y_min)
            * (canvas_h - 2 * self.padding)
        )

        return screen_x, screen_y

    def to_math(self, screen_x: float, screen_y: float) -> Point:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        # FIX 1: Corrected denominator math formula error
        math_x = self.x_min + (
            (screen_x - self.padding)
            * (self.x_max - self.x_min)
            / (canvas_w - 2 * self.padding)
        )

        math_y = self.y_min + (
            (canvas_h - self.padding - screen_y)
            * (self.y_max - self.y_min)
            / (canvas_h - 2 * self.padding)
        )

        return math_x, math_y
    
    def on_press(self, event):
        self.selected_point_index = None
        for index, (x, y) in enumerate(self.control_points):
            sx, sy = self.to_screen(x, y)

            distance = math.hypot(event.x - sx, event.y - sy)

            if distance <= self.drag_radius:
                self.selected_point_index = index
                self.render()
                break

    def on_drag(self, event):
        if self.selected_point_index is None:
            return
        
        math_x, math_y = self.to_math(event.x, event.y)

        math_x = max(self.x_min, min(self.x_max, math_x))
        math_y = max(self.y_min, min(self.y_max, math_y))

        self.control_points[self.selected_point_index] = (math_x, math_y)

        self.render()

    def on_release(self, event):
        self.selected_point_index = None
        self.render()

    def render(self, event=None) -> None:
        self.canvas.delete("all")

        self.draw_grid()
        self.draw_control_polygon()
        self.draw_curve()
        self.draw_control_points()

        canvas_w = self.canvas.winfo_width()
        self.canvas.create_text(
            canvas_w / 2,
            30,
            text="Bézier Curve Simulation",
            font=("Arial", 20, "bold"),
        )
    
    def draw_grid(self) -> None:
        for x in range(int(self.x_min), int(self.x_max) + 1):
            sx, sy1 = self.to_screen(x, self.y_min)
            _, sy2 = self.to_screen(x, self.y_max)

            self.canvas.create_line(sx, sy1, sx, sy2, fill="#dddddd", dash=(4, 4))
            self.canvas.create_text(sx, sy1 + 18, text=str(x), font=("Arial", 10))
            
        for y in range(int(self.y_min), int(self.y_max) + 1):
            sx1, sy = self.to_screen(self.x_min, y)
            sx2, _ = self.to_screen(self.x_max, y)
            self.canvas.create_line(sx1, sy, sx2, sy, fill="#dddddd", dash=(4, 4))
            self.canvas.create_text(sx1 - 18, sy, text=str(y), font=("Arial", 10))

    def draw_control_polygon(self) -> None:
        if len(self.control_points) < 2:
            return
        
        screen_points = [self.to_screen(x, y) for x, y in self.control_points]
        flat_points = [value for point in screen_points for value in point]

        self.canvas.create_line(flat_points, fill="#aaaaaa", dash=(5, 5), width=1.5)

    def draw_curve(self) -> None:
        if len(self.control_points) < 2:
            return
        
        curve_points = calculate_bezier_curve(self.control_points, resolution=100)

        screen_points = [self.to_screen(x, y) for x, y in curve_points]
        flat_points = [value for point in screen_points for value in point]

        self.canvas.create_line(flat_points, fill="blue", width=3)

    def draw_control_points(self) -> None:
        radius = 6

        for index, (x, y) in enumerate(self.control_points):
            sx, sy = self.to_screen(x, y)

            color = "green" if index == self.selected_point_index else "black"
            self.canvas.create_oval(
                sx - radius, sy - radius, sx + radius, sy + radius, fill=color
            )

            self.canvas.create_text(
                sx + 18, sy - 18, text=f"B{index}", fill="blue", font=("Arial", 10, "bold")
            )

def run_app():
    root = tk.Tk()
    BezierLabApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()