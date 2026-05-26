import sys
from pathlib import Path
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Tuple

from PIL import ImageGrab

from .bezier import calculate_bezier_curve, get_bezier_point_at_t


Point = Tuple[float, float]


class BezierLabApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BézierLab")
        self.set_window_icon()
        self.root.geometry("1100x750")

        self.x_min = 0
        self.x_max = 7
        self.y_min = 0
        self.y_max = 7
        self.padding = 80

        self.default_control_points: List[Point] = [
            (1, 1),
            (1, 2.333),
            (4.667, 5),
            (6, 5),
        ]
        self.control_points: List[Point] = list(self.default_control_points)

        self.default_u_values: List[float] = [0.0, 0.3, 0.5, 0.7, 1.0]
        self.u_values: List[float] = list(self.default_u_values)

        self.selected_point_index: Optional[int] = None
        self.drag_radius = 12
        self.updating_points_table = False

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.toolbar = tk.Frame(self.main_frame, bg="#f4f4f4", padx=10, pady=8)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.toolbar, text="Reset Points", command=self.reset_points, width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Remove Last Point", command=self.remove_last_point, width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Clear All Points", command=self.clear_all_points, width=16).pack(side=tk.LEFT, padx=5)

        self.status_text = tk.StringVar(value="Points: 0")

        self.status_label = tk.Label(
            self.toolbar,
            textvariable=self.status_text,
            bg="#f4f4f4",
            font=("Arial", 10, "bold"),
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.content_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.side_panel = tk.Frame(
            self.content_frame,
            width=320,
            bg="#f4f4f4",
            padx=10,
            pady=10,
        )
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.build_side_panel()
        self.bind_events()
        
    def set_window_icon(self) -> None:
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parents[2]

        icon_path = base_path / "assets" / "img" / "logo.ico"

        if icon_path.exists():
            self.root.iconbitmap(icon_path)

    def build_side_panel(self) -> None:
        tk.Label(
            self.side_panel,
            text="Control Points",
            bg="#f4f4f4",
            font=("Arial", 12, "bold"),
        ).pack(pady=(0, 8))

        columns = ("point", "x", "y")

        self.points_table = ttk.Treeview(
            self.side_panel,
            columns=columns,
            show="headings",
            height=8,
        )

        self.points_table.heading("point", text="Point")
        self.points_table.heading("x", text="X")
        self.points_table.heading("y", text="Y")

        self.points_table.column("point", width=60, anchor="center")
        self.points_table.column("x", width=80, anchor="center")
        self.points_table.column("y", width=80, anchor="center")

        self.points_table.pack(fill=tk.X)
        self.points_table.bind("<<TreeviewSelect>>", self.on_table_select)

        tk.Label(
            self.side_panel,
            text="Edit Selected Point",
            bg="#f4f4f4",
            font=("Arial", 12, "bold"),
        ).pack(pady=(18, 8))

        edit_frame = tk.Frame(self.side_panel, bg="#f4f4f4")
        edit_frame.pack(fill=tk.X)

        tk.Label(edit_frame, text="X:", bg="#f4f4f4").grid(row=0, column=0, padx=4, pady=4)
        self.x_entry = tk.Entry(edit_frame, width=10)
        self.x_entry.grid(row=0, column=1, padx=4, pady=4)

        tk.Label(edit_frame, text="Y:", bg="#f4f4f4").grid(row=1, column=0, padx=4, pady=4)
        self.y_entry = tk.Entry(edit_frame, width=10)
        self.y_entry.grid(row=1, column=1, padx=4, pady=4)

        tk.Button(
            self.side_panel,
            text="Apply X/Y",
            command=self.apply_selected_point_edit,
            width=18,
        ).pack(pady=8)

        tk.Label(
            self.side_panel,
            text="Computed Bézier Points",
            bg="#f4f4f4",
            font=("Arial", 12, "bold"),
        ).pack(pady=(18, 8))

        u_frame = tk.Frame(self.side_panel, bg="#f4f4f4")
        u_frame.pack(fill=tk.X)

        tk.Label(u_frame, text="u:", bg="#f4f4f4").pack(side=tk.LEFT, padx=4)

        self.u_entry = tk.Entry(u_frame, width=10)
        self.u_entry.pack(side=tk.LEFT, padx=4)
        self.u_entry.insert(0, "0.5")

        tk.Button(
            u_frame,
            text="Add",
            command=self.add_u_value,
            width=8,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            self.toolbar,
            text="Export PNG",
            command=self.export_canvas_as_png,
            width=16,
            bg="#2E86C1",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            self.side_panel,
            text="Reset u values",
            command=self.reset_u_values,
            width=18,
        ).pack(pady=6)

        computed_columns = ("u", "x", "y")

        self.computed_table = ttk.Treeview(
            self.side_panel,
            columns=computed_columns,
            show="headings",
            height=7,
        )

        self.computed_table.heading("u", text="u")
        self.computed_table.heading("x", text="x")
        self.computed_table.heading("y", text="y")

        self.computed_table.column("u", width=60, anchor="center")
        self.computed_table.column("x", width=80, anchor="center")
        self.computed_table.column("y", width=80, anchor="center")

        self.computed_table.pack(fill=tk.X, pady=(4, 10))

    def bind_events(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Configure>", self.render)

    def to_screen(self, math_x: float, math_y: float) -> Point:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        usable_w = canvas_w - 2 * self.padding
        usable_h = canvas_h - 2 * self.padding

        if usable_w <= 0 or usable_h <= 0:
            return 0, 0

        screen_x = self.padding + (
            (math_x - self.x_min)
            / (self.x_max - self.x_min)
            * usable_w
        )

        screen_y = canvas_h - self.padding - (
            (math_y - self.y_min)
            / (self.y_max - self.y_min)
            * usable_h
        )

        return screen_x, screen_y

    def to_math(self, screen_x: float, screen_y: float) -> Point:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        usable_w = canvas_w - 2 * self.padding
        usable_h = canvas_h - 2 * self.padding

        if usable_w <= 0 or usable_h <= 0:
            return self.x_min, self.y_min

        math_x = self.x_min + (
            (screen_x - self.padding)
            * (self.x_max - self.x_min)
            / usable_w
        )

        math_y = self.y_min + (
            (canvas_h - self.padding - screen_y)
            * (self.y_max - self.y_min)
            / usable_h
        )

        return math_x, math_y

    def on_press(self, event) -> None:
        self.selected_point_index = None

        for index, (x, y) in enumerate(self.control_points):
            sx, sy = self.to_screen(x, y)
            distance = math.hypot(event.x - sx, event.y - sy)

            if distance <= self.drag_radius:
                self.selected_point_index = index
                break

        self.render()

    def on_drag(self, event) -> None:
        if self.selected_point_index is None:
            return

        math_x, math_y = self.to_math(event.x, event.y)

        math_x = max(self.x_min, min(self.x_max, math_x))
        math_y = max(self.y_min, min(self.y_max, math_y))

        self.control_points[self.selected_point_index] = (math_x, math_y)
        self.render()

    def on_release(self, event) -> None:
        self.selected_point_index = None
        self.render()

    def on_double_click(self, event) -> None:
        math_x, math_y = self.to_math(event.x, event.y)

        math_x = max(self.x_min, min(self.x_max, math_x))
        math_y = max(self.y_min, min(self.y_max, math_y))

        self.control_points.append((math_x, math_y))
        self.selected_point_index = len(self.control_points) - 1

        self.render()

    def on_right_click(self, event) -> None:
        for index, (x, y) in enumerate(self.control_points):
            sx, sy = self.to_screen(x, y)
            distance = math.hypot(event.x - sx, event.y - sy)

            if distance <= self.drag_radius:
                self.control_points.pop(index)
                self.selected_point_index = None
                self.render()
                break

    def on_table_select(self, event) -> None:
        if self.updating_points_table:
            return

        selected_items = self.points_table.selection()

        if not selected_items:
            return

        selected_id = selected_items[0]

        if not selected_id.startswith("point_"):
            return

        index = int(selected_id.replace("point_", ""))

        if index >= len(self.control_points):
            return

        if index == self.selected_point_index:
            return

        self.selected_point_index = index
        self.render(update_table=False)

    def reset_points(self) -> None:
        self.control_points = list(self.default_control_points)
        self.selected_point_index = None
        self.render()

    def remove_last_point(self) -> None:
        if not self.control_points:
            return

        self.control_points.pop()

        if (
            self.selected_point_index is not None
            and self.selected_point_index >= len(self.control_points)
        ):
            self.selected_point_index = None

        self.render()

    def clear_all_points(self) -> None:
        self.control_points.clear()
        self.selected_point_index = None
        self.render()

    def update_status_text(self) -> None:
        if self.selected_point_index is None:
            self.status_text.set(f"Points: {len(self.control_points)}")
            return

        if self.selected_point_index >= len(self.control_points):
            self.status_text.set(f"Points: {len(self.control_points)}")
            return

        x, y = self.control_points[self.selected_point_index]

        self.status_text.set(
            f"Selected B{self.selected_point_index}: x={x:.3f}, y={y:.3f}"
        )

    def update_points_table(self) -> None:
        self.updating_points_table = True

        for item in self.points_table.get_children():
            self.points_table.delete(item)

        for index, (x, y) in enumerate(self.control_points):
            item_id = f"point_{index}"

            self.points_table.insert(
                "",
                tk.END,
                iid=item_id,
                values=(f"B{index}", f"{x:.3f}", f"{y:.3f}"),
            )

        if (
            self.selected_point_index is not None
            and self.selected_point_index < len(self.control_points)
        ):
            selected_id = f"point_{self.selected_point_index}"

            if self.points_table.exists(selected_id):
                self.points_table.selection_set(selected_id)
                self.points_table.focus(selected_id)

        self.root.after_idle(self.finish_table_update)

    def finish_table_update(self) -> None:
        self.updating_points_table = False

    def update_edit_boxes(self) -> None:
        self.x_entry.delete(0, tk.END)
        self.y_entry.delete(0, tk.END)

        if self.selected_point_index is None:
            return

        if self.selected_point_index >= len(self.control_points):
            return

        x, y = self.control_points[self.selected_point_index]

        self.x_entry.insert(0, f"{x:.3f}")
        self.y_entry.insert(0, f"{y:.3f}")

    def apply_selected_point_edit(self) -> None:
        if self.selected_point_index is None:
            messagebox.showwarning("No point selected", "Select a control point first.")
            return

        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", "X and Y must be valid numbers.")
            return

        x = max(self.x_min, min(self.x_max, x))
        y = max(self.y_min, min(self.y_max, y))

        self.control_points[self.selected_point_index] = (x, y)
        self.render()

    def add_u_value(self) -> None:
        try:
            value = float(self.u_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid input",
                "u must be a number between 0.0 and 1.0.",
            )
            return

        if not 0.0 <= value <= 1.0:
            messagebox.showerror(
                "Invalid u value",
                "u must be between 0.0 and 1.0.",
            )
            return

        if any(abs(value - existing) < 1e-9 for existing in self.u_values):
            messagebox.showwarning(
                "Duplicate u value",
                "This u value already exists.",
            )
            return

        self.u_values.append(value)
        self.u_values.sort()
        self.render()

    def reset_u_values(self) -> None:
        self.u_values = list(self.default_u_values)
        self.render()

    def update_computed_points_table(self) -> None:
        for item in self.computed_table.get_children():
            self.computed_table.delete(item)

        if len(self.control_points) < 2:
            return

        for u in self.u_values:
            x, y = get_bezier_point_at_t(self.control_points, u)

            self.computed_table.insert(
                "",
                tk.END,
                values=(f"{u:.3f}", f"{x:.3f}", f"{y:.3f}"),
            )

    def export_canvas_as_png(self) -> None:
        self.root.update()

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Save canvas as PNG",
        )

        if not filepath:
            return

        try:
            x0 = self.canvas.winfo_rootx()
            y0 = self.canvas.winfo_rooty()
            x1 = x0 + self.canvas.winfo_width()
            y1 = y0 + self.canvas.winfo_height()

            image = ImageGrab.grab(bbox=(x0, y0, x1, y1))
            image.save(filepath)

            messagebox.showinfo(
                "Export successful",
                f"Canvas exported to:\n{filepath}",
            )

        except Exception as error:
            messagebox.showerror("Export failed", str(error))

    def render(self, event=None, update_table=True) -> None:
        self.canvas.delete("all")

        self.draw_grid()
        self.draw_control_polygon()
        self.draw_curve()
        self.draw_computed_points()
        self.draw_control_points()

        self.update_status_text()
        self.update_edit_boxes()

        if update_table:
            self.update_points_table()
            self.update_computed_points_table()

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

        self.canvas.create_line(
            flat_points,
            fill="#aaaaaa",
            dash=(5, 5),
            width=1.5,
        )

    def draw_curve(self) -> None:
        if len(self.control_points) < 2:
            return

        curve_points = calculate_bezier_curve(self.control_points, resolution=100)
        screen_points = [self.to_screen(x, y) for x, y in curve_points]
        flat_points = [value for point in screen_points for value in point]

        self.canvas.create_line(flat_points, fill="blue", width=3)

    def draw_computed_points(self) -> None:
        if len(self.control_points) < 2:
            return

        radius = 5

        for u in self.u_values:
            x, y = get_bezier_point_at_t(self.control_points, u)
            sx, sy = self.to_screen(x, y)

            self.canvas.create_oval(
                sx - radius,
                sy - radius,
                sx + radius,
                sy + radius,
                fill="red",
                outline="red",
            )

            if u not in (0.0, 1.0):
                self.canvas.create_text(
                    sx + 38,
                    sy + 22,
                    text=f"u={u:.2f}\n({x:.2f}, {y:.2f})",
                    fill="red",
                    font=("Arial", 9),
                )

    def draw_control_points(self) -> None:
        radius = 6

        for index, (x, y) in enumerate(self.control_points):
            sx, sy = self.to_screen(x, y)

            color = "green" if index == self.selected_point_index else "black"

            self.canvas.create_oval(
                sx - radius,
                sy - radius,
                sx + radius,
                sy + radius,
                fill=color,
            )

            self.canvas.create_text(
                sx + 18,
                sy - 18,
                text=f"B{index}",
                fill="blue",
                font=("Arial", 10, "bold"),
            )


def run_app() -> None:
    root = tk.Tk()
    BezierLabApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()