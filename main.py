from src.maze import Maze, MIN_SIZE, MAX_SIZE
from src.robot import Robot
import turtle
import tkinter as tk

current = {}

def restart(new_maze):
    if 'robot' in current:
        current['robot'].cancelled = True
    maze.screen.clearscreen()
    maze.pen = turtle.Turtle()
    if new_maze:
        maze.generate_maze()
    else:
        maze.draw_maze() # same maze, wipe the previous solver's path
    current['robot'] = Robot(maze, show_status)
    current['robot'].run_solver(algorithm.get())

def show_status(text):
    status.config(text=text)

def read_size(var, fallback):
    try:
        value = int(var.get())
    except ValueError:
        value = fallback # not a number, keep the current size
    value = max(MIN_SIZE, min(MAX_SIZE, value))
    var.set(value) # show the clamped value back in the box
    return value

def generate_new_maze():
    maze.set_size(read_size(rows, maze.rows), read_size(cols, maze.cols))
    restart(new_maze=True)

def solve_current_maze():
    restart(new_maze=False)



if __name__ == '__main__':
    maze = Maze(30, 24)
    maze.generate_maze()

    root = maze.screen.getcanvas().winfo_toplevel()
    algorithm = tk.StringVar(root, value='dfs')

    controls = tk.Frame(root)
    controls.pack()

    # maze size; takes effect on 'New Maze' (or pressing Enter in either box)
    rows = tk.StringVar(root, value=maze.rows)
    cols = tk.StringVar(root, value=maze.cols)
    for label, var in [('Rows', rows), ('Cols', cols)]:
        tk.Label(controls, text=label).pack(side='left')
        box = tk.Spinbox(controls, from_=MIN_SIZE, to=MAX_SIZE, textvariable=var, width=4)
        box.bind('<Return>', lambda event: generate_new_maze())
        box.pack(side='left', padx=(0, 8))

    tk.Button(controls, text='New Maze', command=generate_new_maze).pack(side='left')
    # indicatoron=0 draws the radio buttons as toggle buttons; the selected one stays pressed
    for label, name in [('DFS', 'dfs'), ('BFS', 'bfs'), ('Manual', 'manual')]:
        tk.Radiobutton(controls, text=label, value=name, variable=algorithm,
                       indicatoron=0, width=6, command=solve_current_maze).pack(side='left')

    status = tk.Label(root)
    status.pack()
    # clicking the maze takes keyboard focus back from the size boxes, for manual mode
    maze.screen.getcanvas().bind('<Button-1>', lambda event: maze.screen.getcanvas().focus_set(), add='+')

    robot = Robot(maze, show_status)
    current['robot'] = robot
    robot.run_solver(algorithm.get())

    maze.screen.mainloop()
