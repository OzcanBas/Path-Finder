import turtle
import random

FLOOR_COLOR = '#f4f1ea'
WALL_COLOR = '#2b2d42'
START_COLOR = '#06d6a0'
EXIT_COLOR = '#ffd166'

MIN_SIZE, MAX_SIZE = 5, 60   # allowed number of rows/cols
MIN_CELL, MAX_CELL = 8, 40   # cell size in pixels is picked between these to fit the screen
MARGIN = 40                  # space around the maze inside the window
CONTROLS_HEIGHT = 80         # room for the button bar and status line under the canvas

class Maze:
    def __init__(self, rows=30, cols=24):
        self.pen = turtle.Turtle()
        self.screen = turtle.Screen()
        self.set_size(rows, cols)

    def set_size(self, rows, cols):
        """Change the maze dimensions and pick the biggest cell size that still fits on screen."""
        self.rows = max(MIN_SIZE, min(MAX_SIZE, rows))
        self.cols = max(MIN_SIZE, min(MAX_SIZE, cols))

        root = self.screen.getcanvas().winfo_toplevel()
        max_width = root.winfo_screenwidth() * 0.9 - MARGIN
        max_height = root.winfo_screenheight() * 0.85 - MARGIN - CONTROLS_HEIGHT
        cell = int(min(max_width / self.cols, max_height / self.rows))
        self.cell_size = max(MIN_CELL, min(MAX_CELL, cell))

        self.width = self.cols * self.cell_size + MARGIN
        self.height = self.rows * self.cell_size + MARGIN + CONTROLS_HEIGHT

    def cell_top_left(self, r, c):
        """Screen position of the top left corner of grid cell (r, c)."""
        return (-(self.cols * self.cell_size) // 2 + self.cell_size * c,
                (self.rows * self.cell_size) // 2 - self.cell_size * r)

    def cell_center(self, r, c):
        x, y = self.cell_top_left(r, c)
        return x + self.cell_size / 2, y - self.cell_size / 2

    def generate_maze(self):
        self.screen.title('The Maze')
        self.screen.setup(width=self.width, height=self.height) # screen window size

        self.grid = self.build_grid()
        self.draw_maze()

    def draw_maze(self):
        """Draw the current grid without generating a new one."""
        self.screen.bgcolor(FLOOR_COLOR)
        self.screen.tracer(0)
        self.pen.hideturtle()
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                x, y = self.cell_top_left(i, j)
                if cell == 1:
                    self.fill_cell(x, y, self.cell_size, WALL_COLOR)
                elif cell == 2:
                    self.fill_cell(x, y, self.cell_size, START_COLOR if i == 0 else EXIT_COLOR)
        self.screen.update() # draw the whole maze in one go


    def fill_cell(self, x, y, size, color):
        """Fill a single grid cell at position top_left=(x, y) with given color. This is a helper function."""
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.setheading(0)
        self.pen.pendown()
        self.pen.color(color)
        self.pen.begin_fill()
        for _ in range(4):
            self.pen.forward(size)
            self.pen.right(90)
        self.pen.end_fill()
        self.pen.up()

    def build_grid(self):
        """This function generates the actual maze/grid as a 2D array."""
        # 0 = path, 1 = wall, 2 = entrance/exit
        grid = [[1] * self.cols for _ in range(self.rows)]
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                grid[r][c] = 0

        def divide(r0, r1, c0, c1):
            # chamber is the open region self.rows r0..r1, self.cols c0..c1
            h, w = r1 - r0 + 1, c1 - c0 + 1

            # a wall may only go where both of its ends hit solid wall (not a gap)
            horiz = [y for y in range(r0 + 1, r1)
                    if grid[y][c0 - 1] == 1 and grid[y][c1 + 1] == 1]
            vert = [x for x in range(c0 + 1, c1)
                    if grid[r0 - 1][x] == 1 and grid[r1 + 1][x] == 1]

            if not horiz and not vert:
                return

            # prefer cutting across the longer side
            if horiz and (not vert or h > w or (h == w and random.random() < 0.5)):
                y = random.choice(horiz)
                gap = random.randint(c0, c1)
                for c in range(c0, c1 + 1):
                    if c != gap:
                        grid[y][c] = 1
                divide(r0, y - 1, c0, c1)
                divide(y + 1, r1, c0, c1)
            else:
                x = random.choice(vert)
                gap = random.randint(r0, r1)
                for r in range(r0, r1 + 1):
                    if r != gap:
                        grid[r][x] = 1
                divide(r0, r1, c0, x - 1)
                divide(r0, r1, x + 1, c1)

        divide(1, self.rows - 2, 1, self.cols - 2)

        grid[0][1] = 2
        grid[self.rows - 1][self.cols - 2] = 2
        return grid
