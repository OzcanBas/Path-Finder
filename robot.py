import turtle
import tkinter as tk

class Robot:
    def __init__(self, maze):
        # share the same grid and screen from the maze class with the robot class
        self.grid = maze.grid
        self.rows = len(maze.grid)
        self.cols = len(maze.grid[0])
        self.screen = maze.screen
        self.maze = maze
        print(self.rows)
        print(self.cols)

    def solve_maze(self):
        stack = [(0,1)]

        rows = len(self.grid)
        cols = len(self.grid[0])

        visited = {(0,1)}
        goal = (rows - 1, cols - 2)

        # create robot
        photo = tk.PhotoImage(file='robot.png')
        photo_small = photo.subsample(25)
        self.screen.register_shape('robot', turtle.Shape('image', photo_small))
        robot = turtle.Turtle()
        robot.shape('robot')
        robot.penup()
        robot.speed(0)  # no glide animation; each step jumps straight to the next cell
        robot.goto(-30*(self.cols)//2 + 30 + 15, 30*(self.rows)//2 - 15)

        while stack:
            r, c = stack[-1]

            if (r,c) == goal:
                print(f'winning solution is: {stack}')
                return stack

            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and self.grid[nr][nc] != 1
                        and (nr, nc) not in visited):
                    
                    visited.add((nr, nc))
                    stack.append((nr, nc))
                    self.maze.fill_cell(-30*(self.cols)//2 + 30*nc , 30*(self.rows)//2 - 30*nr, 30, 'green')
                    robot.goto(-30*(self.cols)//2 + 30*nc + 15, 30*(self.rows)//2 - 30*nr - 15)
                    self.screen.update()

                    yield
                    break

            else:
                stack.pop()

        return None

    def run_solver(self):
        self.cancelled = False
        steps = self.solve_maze()

        def tick():
            if self.cancelled:
                return
            try:
                next(steps)
                self.screen.ontimer(tick, 200)
            except StopIteration:
                pass

        tick()