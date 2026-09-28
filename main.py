from maze import Maze
from robot import Robot
import turtle
import tkinter as tk

current = {}

def generate_new_maze():
    if 'robot' in current:
        current['robot'].cancelled = True
    maze.screen.clearscreen()
    maze.pen = turtle.Turtle()
    maze.generate_maze()
    current['robot'] = Robot(maze)
    current['robot'].run_solver()



if __name__ == '__main__':
    maze = Maze(30, 24)
    grid = maze.build_grid()
    maze.generate_maze()

    root = maze.screen.getcanvas().winfo_toplevel()
    tk.Button(root, text='New Maze', command=generate_new_maze).pack()


    print('maze has been generated')
    robot = Robot(maze)
    current['robot'] = robot
    robot.run_solver()

    maze.screen.mainloop()

    

