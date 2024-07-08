import tkinter as tk
from tkinter import simpledialog
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from PIL import Image, ImageDraw, ImageTk
import random
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')

def create_radial_gradient(size, color1, color2):
    img = Image.new('RGB', size, color1)
    draw = ImageDraw.Draw(img)
    for i in range(size[0]):
        for j in range(size[1]):
            dist = ((i - size[0]/2)**2 + (j - size[1]/2)**2)**0.5
            ratio = min(1.0, dist / (size[0]/2))
            color = tuple([int(c1*(1-ratio) + c2*ratio) for c1,c2 in zip(color1, color2)])
            draw.point([i,j], fill=color)
    return img

class StartScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Particle Simulation")

        # Load the background image for the start screen
        image_path = r'C:\Users\dell\Desktop\background.jpg'
        self.bg_image = Image.open(image_path)
        self.bg_image = ImageTk.PhotoImage(self.bg_image)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        self.auto_button = tk.Button(root, text="Auto Mode", command=self.start_auto_mode, width=20, height=2)
        self.auto_button.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        self.manual_button = tk.Button(root, text="Manual Mode", command=self.start_manual_mode, width=20, height=2)
        self.manual_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

    def start_auto_mode(self):
        self.auto_button.destroy()
        self.manual_button.destroy()
        self.canvas.destroy()
        auto_mode_app = AutoMode(self.root)  # 这里启动自动模式

    def start_manual_mode(self):
        self.auto_button.destroy()
        self.manual_button.destroy()
        self.canvas.destroy()
        manual_mode_app = ManualMode(self.root)  # 这里启动手动模式

class AutoMode:
    def __init__(self, root):
        self.root = root
        self.root.title("Particle Simulation (Auto Mode)")

        image_path = r'C:\Users\dell\Desktop\background.jpg'
        self.bg_image = Image.open(image_path)
        self.bg_image = ImageTk.PhotoImage(self.bg_image)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        self.fixed_circle_radius = 100
        self.fixed_circle_x = 400
        self.fixed_circle_y = 300

        self.scale_factor = 100 / 15

        self.start_button = tk.Button(root, text="Start", command=self.start, width=10, height=2)
        self.start_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.upper_line = None
        self.lower_line = None

        self.canvas.bind("<Motion>", self.update_lines)
        self.canvas.bind("<Button-1>", self.set_initial_position)

        self.stop_button = tk.Button(root, text="Draw the plot", command=self.stop_animation)
        self.stop_button.pack()

        self.particles = []

        self.animation_running = False

        self.time_data = []
        self.weighted_uncovered_area_data = []

        self.num_grid_points = 1000000

        self.grid_density = int(np.ceil(np.sqrt(self.num_grid_points)))

        x_grid, y_grid = np.meshgrid(
            np.linspace(self.fixed_circle_x - self.fixed_circle_radius,
                        self.fixed_circle_x + self.fixed_circle_radius,
                        self.grid_density),
            np.linspace(self.fixed_circle_y - self.fixed_circle_radius,
                        self.fixed_circle_y + self.fixed_circle_radius,
                        self.grid_density)
        )

        self.x_grid = x_grid.flatten()
        self.y_grid = y_grid.flatten()

        # Filter out points that are outside the circle
        distances_from_center = np.sqrt((self.x_grid - self.fixed_circle_x) ** 2 +
                                        (self.y_grid - self.fixed_circle_y) ** 2)
        in_circle_mask = distances_from_center <= self.fixed_circle_radius

        self.x_grid = self.x_grid[in_circle_mask]
        self.y_grid = self.y_grid[in_circle_mask]

        self.distances_from_center = np.sqrt(
            (self.x_grid - self.fixed_circle_x) ** 2 + (self.y_grid - self.fixed_circle_y) ** 2)
        self.initial_weights = 1000 - (999 * (self.distances_from_center / self.fixed_circle_radius))
        self.total_initial_weight = np.sum(self.initial_weights)

        self.selected_particle = None
        self.first_plot = True

        self.particle_buttons_frame = tk.Frame(self.root)
        self.particle_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.particle_types = []
        self.particle_type_buttons = []

        self.start_simulation_button = tk.Button(self.root, text="Start Simulation", command=self.start_simulation)
        self.start_simulation_button.pack()

        self.recent_particles = deque(maxlen=2)

        self.real_time_data = []
        self.real_time_plot_window = None
        self.canvas_agg = None

        # Setup real-time plot window
        self.setup_real_time_plot_window()

    def start(self):

        self.canvas.delete("all")
        self.canvas.config(bg='white')

        self.draw_fixed_circle()

        self.start_button.destroy()
        self.add_particle_button = tk.Button(self.root, text="Add Particle", command=self.add_particle)
        self.add_particle_button.pack()

        self.particle_selection_frame = tk.Frame(self.root)
        self.particle_selection_frame.pack()

    def simulate_click(self):
        """模拟用户点击事件，横坐标固定为800，纵坐标随机。"""
        random_y = random.randint(0, self.canvas.winfo_height())
        self.set_initial_position(800, random_y)
        self.schedule_next_simulate_click()  # 调度下一次模拟点击

    def schedule_next_simulate_click(self):
        """调度下一次模拟点击事件，时间间隔在1至3秒之间。"""
        delay = random.randint(1000, 3000)  # 将时间间隔转换为毫秒
        self.root.after(delay, self.simulate_click)

    def start_simulation(self):
        """当用户点击'Start Simulation'按钮时，开始模拟点击。"""
        self.simulate_click()

    def add_particle(self):
        particle_frame = tk.Frame(self.particle_selection_frame)
        particle_frame.pack()

        radius_label = tk.Label(particle_frame, text="Radius (μm):")
        radius_label.pack(side=tk.LEFT)
        radius_entry = tk.Entry(particle_frame)
        radius_entry.pack(side=tk.LEFT)

        speed_label = tk.Label(particle_frame, text="Speed:")
        speed_label.pack(side=tk.LEFT)
        speed_scale = tk.Scale(particle_frame, from_=1, to=20, orient=tk.HORIZONTAL)
        speed_scale.pack(side=tk.LEFT)

        number_label = tk.Label(particle_frame, text="Number of Particles:")
        number_label.pack(side=tk.LEFT)
        number_entry = tk.Entry(particle_frame)
        number_entry.pack(side=tk.LEFT)

        add_button = tk.Button(particle_frame, text="Add",
                               command=lambda: self.add_particle_to_list(radius_entry, speed_scale, number_entry))
        add_button.pack(side=tk.LEFT)

    def add_particle_to_list(self, radius_entry, speed_scale, number_entry):
        radius = int(radius_entry.get())
        speed = speed_scale.get()
        number = int(number_entry.get())

        particle_key = (radius, speed)
        if particle_key not in self.particle_types:
            self.particle_types.append(particle_key)
            particle_info = {'total': number, 'sent': 0}

            particle_name = f"Radius: {radius} μm, Speed: {speed}, Number: {particle_info['total']}"
            particle_button = tk.Button(self.particle_buttons_frame, text=particle_name,
                                        command=lambda: self.select_particle(radius, speed, particle_info))
            particle_button.pack(side=tk.LEFT, padx=5)

            # 修改这里，现在我们把 particle_info 也添加到列表中
            self.particle_type_buttons.append((particle_button, particle_key, particle_info))
        else:
            index = self.particle_types.index(particle_key)
            particle_button, _, particle_info = self.particle_type_buttons[index]  # 注意这里的解包
            particle_button.configure(text=f"Radius: {radius} μm, Speed: {speed}, Number: {number}")
            particle_info['total'] = number  # 更新 particle_info 的 total 值

    def select_particle(self, radius, speed, particle_info):
        self.selected_particle = (radius, speed, particle_info)

    def draw_fixed_circle(self):
        gradient_image = create_radial_gradient((2 * self.fixed_circle_radius, 2 * self.fixed_circle_radius),
                                                (255, 0, 0), (255, 255, 255))
        gradient_photo = ImageTk.PhotoImage(gradient_image)
        self.canvas.create_image(self.fixed_circle_x, self.fixed_circle_y, image=gradient_photo)
        self.canvas.image = gradient_photo

    def update_lines(self, event):
        if self.selected_particle is None or self.upper_line is None or self.lower_line is None:
            return

        mouse_y = event.y
        self.canvas.coords(self.upper_line, 0, mouse_y - self.selected_particle[0] * self.scale_factor, 800,
                           mouse_y - self.selected_particle[0] * self.scale_factor)
        self.canvas.coords(self.lower_line, 0, mouse_y + self.selected_particle[0] * self.scale_factor, 800,
                           mouse_y + self.selected_particle[0] * self.scale_factor)

    def set_initial_position(self, x, y):

        if not self.particle_types:
            return

        particle_key = random.choice(self.particle_types)

        particle_info = None
        for _, key, info in self.particle_type_buttons:
            if key == particle_key:
                particle_info = info
                break

        if particle_info is None or particle_info['sent'] >= particle_info['total']:
            return

        radius, speed = particle_key
        move_circle_radius = radius * self.scale_factor

        move_circle_x = x
        move_circle_y = y

        particle = {
            'id': len(self.particles),
            'radius': radius,
            'speed': speed,
            'move_circle_radius': move_circle_radius,
            'move_circle_x': move_circle_x,
            'move_circle_y': move_circle_y,
            'oval': self.canvas.create_oval(move_circle_x - move_circle_radius,
                                            move_circle_y - move_circle_radius,
                                            move_circle_x + move_circle_radius,
                                            move_circle_y + move_circle_radius,
                                            fill='black')
        }

        self.particles.append(particle)
        particle_info['sent'] += 1


        if self.upper_line is None:
            self.upper_line = self.canvas.create_line(0, move_circle_y - move_circle_radius, 800,
                                                      move_circle_y - move_circle_radius, fill='gray', dash=(4, 2))
            self.lower_line = self.canvas.create_line(0, move_circle_y + move_circle_radius, 800,
                                                      move_circle_y + move_circle_radius, fill='gray', dash=(4, 2))

        if not self.animation_running:
            self.animation_running = True
            self.animate(0)

    def animate(self, t):
        if not self.animation_running:
            return

        all_particles_finished = True
        for particle in self.particles:
            if self.canvas.coords(particle['oval'])[2] > 0:
                all_particles_finished = False
                self.canvas.move(particle['oval'], -particle['speed'], 0)

        if all_particles_finished:
            self.animation_running = False
            self.plot_weighted_uncovered_area_vs_time()
            return

        weighted_uncovered_area = self.calculate_weighted_uncovered_area()
        self.time_data.append(t)
        self.weighted_uncovered_area_data.append(weighted_uncovered_area)

        # Update real-time plot data
        self.real_time_data.append(weighted_uncovered_area)
        self.line.set_data(self.time_data, self.real_time_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas_agg.draw()

        self.root.after(50, self.animate, t + 0.05)

    def stop_animation(self):
        self.animation_running = False
        if self.first_plot:
            self.plot_weighted_uncovered_area_vs_time()
            self.first_plot = False
        self.time_data.clear()
        self.weighted_uncovered_area_data.clear()

    def calculate_weighted_uncovered_area(self):
        weights = np.copy(self.initial_weights)

        for particle in self.particles:
            move_circle_coords = self.canvas.coords(particle['oval'])
            current_move_circle_x = (move_circle_coords[0] + move_circle_coords[2]) / 2
            current_move_circle_y = (move_circle_coords[1] + move_circle_coords[3]) / 2
            current_move_circle_radius = (move_circle_coords[2] - move_circle_coords[0]) / 2

            distances_to_moving_center = np.sqrt(
                (self.x_grid - current_move_circle_x) ** 2 + (self.y_grid - current_move_circle_y) ** 2)
            covered_indices = distances_to_moving_center <= current_move_circle_radius

            weights[covered_indices] = 0

        total_weighted_uncovered_area = np.sum(weights)

        return total_weighted_uncovered_area

    def plot_weighted_uncovered_area_vs_time(self):
        fig, ax = plt.subplots()
        ax.plot(self.time_data, self.weighted_uncovered_area_data, label="Weighted Uncovered Area")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Weighted Uncovered Area")
        ax.set_title("Weighted Uncovered Area vs. Time")
        ax.legend()
        plt.show()

    def setup_real_time_plot_window(self):
        self.real_time_plot_window = tk.Toplevel(self.root)
        self.real_time_plot_window.title("Real-Time Weighted Uncovered Area")
        self.real_time_plot_window.geometry("600x400")

        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Weighted Uncovered Area")
        self.ax.set_title("Real-Time Weighted Uncovered Area")

        self.canvas_agg = FigureCanvasTkAgg(self.fig, master=self.real_time_plot_window)
        self.canvas_agg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.line, = self.ax.plot([], [], 'r-')


class ManualMode:
    def __init__(self, root):
        self.root = root
        self.root.title("Particle Simulation (Manual Mode)")

        image_path = r'C:\Users\dell\Desktop\background.jpg'
        self.bg_image = Image.open(image_path)
        self.bg_image = ImageTk.PhotoImage(self.bg_image)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        self.fixed_circle_radius = 100
        self.fixed_circle_x = 400
        self.fixed_circle_y = 300

        self.scale_factor = 100 / 15

        self.start_button = tk.Button(root, text="Start", command=self.start, width=10, height=2)
        self.start_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.upper_line = None
        self.lower_line = None

        self.canvas.bind("<Motion>", self.update_lines)
        self.canvas.bind("<Button-1>", self.set_initial_position)

        self.stop_button = tk.Button(root, text="Draw the plot", command=self.stop_animation)
        self.stop_button.pack()

        self.particles = []

        self.animation_running = False

        self.time_data = []
        self.weighted_uncovered_area_data = []

        self.num_grid_points = 1000000

        self.grid_density = int(np.ceil(np.sqrt(self.num_grid_points)))

        # Generate a uniform grid of points over the square
        x_grid, y_grid = np.meshgrid(
            np.linspace(self.fixed_circle_x - self.fixed_circle_radius,
                        self.fixed_circle_x + self.fixed_circle_radius,
                        self.grid_density),
            np.linspace(self.fixed_circle_y - self.fixed_circle_radius,
                        self.fixed_circle_y + self.fixed_circle_radius,
                        self.grid_density)
        )

        # Flatten the grids to a list of points
        self.x_grid = x_grid.flatten()
        self.y_grid = y_grid.flatten()

        # Filter out points that are outside the circle
        distances_from_center = np.sqrt((self.x_grid - self.fixed_circle_x) ** 2 +
                                        (self.y_grid - self.fixed_circle_y) ** 2)
        in_circle_mask = distances_from_center <= self.fixed_circle_radius

        # Apply the mask to keep only the points inside the circle
        self.x_grid = self.x_grid[in_circle_mask]
        self.y_grid = self.y_grid[in_circle_mask]

        self.distances_from_center = np.sqrt(
            (self.x_grid - self.fixed_circle_x) ** 2 + (self.y_grid - self.fixed_circle_y) ** 2)
        self.initial_weights = 1000 - (999 * (self.distances_from_center / self.fixed_circle_radius))
        self.total_initial_weight = np.sum(self.initial_weights)

        self.selected_particle = None
        self.first_plot = True

        self.particle_buttons_frame = tk.Frame(self.root)
        self.particle_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def start(self):
        # Clear all elements on the canvas and switch to white background
        self.canvas.delete("all")
        self.canvas.config(bg='white')

        # Redraw fixed circle on the white background
        self.draw_fixed_circle()

        # Destroy the start button and continue with the rest of the initialization
        self.start_button.destroy()
        self.add_particle_button = tk.Button(self.root, text="Add Particle", command=self.add_particle)
        self.add_particle_button.pack()

        self.particle_selection_frame = tk.Frame(self.root)
        self.particle_selection_frame.pack()

    def add_particle(self):
        particle_frame = tk.Frame(self.particle_selection_frame)
        particle_frame.pack()

        radius_label = tk.Label(particle_frame, text="Radius (μm):")
        radius_label.pack(side=tk.LEFT)
        radius_entry = tk.Entry(particle_frame)
        radius_entry.pack(side=tk.LEFT)

        speed_label = tk.Label(particle_frame, text="Speed:")
        speed_label.pack(side=tk.LEFT)
        speed_scale = tk.Scale(particle_frame, from_=1, to=20, orient=tk.HORIZONTAL)
        speed_scale.pack(side=tk.LEFT)

        add_button = tk.Button(particle_frame, text="Add",
                               command=lambda: self.add_particle_to_list(radius_entry, speed_scale))
        add_button.pack(side=tk.LEFT)

    def add_particle_to_list(self, radius_entry, speed_scale):
        radius = int(radius_entry.get())
        speed = speed_scale.get()

        particle_name = f"Radius: {radius} μm, Speed: {speed}"
        particle_button = tk.Button(self.particle_buttons_frame, text=particle_name,
                                    command=lambda: self.select_particle(radius, speed))
        particle_button.pack(side=tk.LEFT, padx=5)

    def select_particle(self, radius, speed):
        self.selected_particle = (radius, speed)

    def draw_fixed_circle(self):
        # Create a radial gradient image for the fixed circle
        gradient_image = create_radial_gradient((2 * self.fixed_circle_radius, 2 * self.fixed_circle_radius),
                                                (255, 0, 0), (255, 255, 255))
        gradient_photo = ImageTk.PhotoImage(gradient_image)

        # Draw the gradient-filled circle on the canvas
        self.canvas.create_image(self.fixed_circle_x, self.fixed_circle_y, image=gradient_photo)
        self.canvas.image = gradient_photo  # Keep a reference to avoid garbage collection

    def update_lines(self, event):
        if self.selected_particle is None or self.upper_line is None or self.lower_line is None:
            return

        mouse_y = event.y
        self.canvas.coords(self.upper_line, 0, mouse_y - self.selected_particle[0] * self.scale_factor, 800,
                           mouse_y - self.selected_particle[0] * self.scale_factor)
        self.canvas.coords(self.lower_line, 0, mouse_y + self.selected_particle[0] * self.scale_factor, 800,
                           mouse_y + self.selected_particle[0] * self.scale_factor)

    def set_initial_position(self, event):
        if self.selected_particle is None:
            return

        radius, speed = self.selected_particle
        move_circle_radius = radius * self.scale_factor

        move_circle_x = event.x
        move_circle_y = event.y

        particle = {
            'id': len(self.particles),
            'radius': radius,
            'speed': speed,
            'move_circle_radius': move_circle_radius,
            'move_circle_x': move_circle_x,
            'move_circle_y': move_circle_y,
            'oval': self.canvas.create_oval(move_circle_x - move_circle_radius,
                                            move_circle_y - move_circle_radius,
                                            move_circle_x + move_circle_radius,
                                            move_circle_y + move_circle_radius,
                                            fill='black')
        }

        self.particles.append(particle)

        if self.upper_line is None:
            self.upper_line = self.canvas.create_line(0, move_circle_y - move_circle_radius, 800,
                                                      move_circle_y - move_circle_radius, fill='gray', dash=(4, 2))
            self.lower_line = self.canvas.create_line(0, move_circle_y + move_circle_radius, 800,
                                                      move_circle_y + move_circle_radius, fill='gray', dash=(4, 2))

        if not self.animation_running:
            self.animation_running = True
            self.animate(0)

    def animate(self, t):
        if not self.animation_running:
            return

        all_particles_finished = True
        for particle in self.particles:
            if self.canvas.coords(particle['oval'])[2] > 0:
                all_particles_finished = False
                self.canvas.move(particle['oval'], -particle['speed'], 0)

        if all_particles_finished:
            self.animation_running = False
            self.plot_weighted_uncovered_area_vs_time()
            return

        weighted_uncovered_area = self.calculate_weighted_uncovered_area()
        self.time_data.append(t)
        self.weighted_uncovered_area_data.append(weighted_uncovered_area)

        self.root.after(50, self.animate, t + 0.05)

    def stop_animation(self):
        self.animation_running = False
        if self.first_plot:
            self.plot_weighted_uncovered_area_vs_time()
            self.first_plot = False
        self.time_data.clear()
        self.weighted_uncovered_area_data.clear()

    def calculate_weighted_uncovered_area(self):
        weights = np.copy(self.initial_weights)

        for particle in self.particles:
            move_circle_coords = self.canvas.coords(particle['oval'])
            current_move_circle_x = (move_circle_coords[0] + move_circle_coords[2]) / 2
            current_move_circle_y = (move_circle_coords[1] + move_circle_coords[3]) / 2
            current_move_circle_radius = (move_circle_coords[2] - move_circle_coords[0]) / 2

            distances_to_moving_center = np.sqrt(
                (self.x_grid - current_move_circle_x) ** 2 + (self.y_grid - current_move_circle_y) ** 2)
            covered_indices = distances_to_moving_center <= current_move_circle_radius

            weights[covered_indices] = 0

        total_weighted_uncovered_area = np.sum(weights)

        return total_weighted_uncovered_area

    def plot_weighted_uncovered_area_vs_time(self):
        fig, ax = plt.subplots()
        ax.plot(self.time_data, self.weighted_uncovered_area_data, label="Weighted Uncovered Area")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Weighted Uncovered Area")
        ax.set_title("Weighted Uncovered Area vs. Time")
        ax.legend()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    start_screen = StartScreen(root)
    root.mainloop()

