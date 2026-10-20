from src.maze import Maze
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
    current['robot'] = Robot(maze)
    current['robot'].run_solver(algorithm.get())

def generate_new_maze():
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
    tk.Button(controls, text='New Maze', command=generate_new_maze).pack(side='left')
    # indicatoron=0 draws the radio buttons as toggle buttons; the selected one stays pressed
    for label, name in [('DFS', 'dfs'), ('BFS', 'bfs')]:
        tk.Radiobutton(controls, text=label, value=name, variable=algorithm,
                       indicatoron=0, width=6, command=solve_current_maze).pack(side='left')

    robot = Robot(maze)
    current['robot'] = robot
    robot.run_solver(algorithm.get())

    maze.screen.mainloop()
