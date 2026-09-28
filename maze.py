import turtle
import random

class Maze:
    def __init__(self, height=30, width=24):
        self.cols = width
        self.rows = height
        self.width = width*40
        self.height = height*35
        self.pen = turtle.Turtle()
        self.screen = turtle.Screen()

    def generate_maze(self):
        self.screen.title('The Maze')
        self.screen.setup(width=self.width, height=self.height) # width of 24, height of 30
        self.screen.bgcolor('white')

        self.grid = self.build_grid()
        CELL_SIZE = 30

        self.screen.tracer(0) # stop redrawing after every pen move
        self.pen.hideturtle()
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                x = -(self.cols * CELL_SIZE) / 2 + (CELL_SIZE * j)
                y = (self.rows * CELL_SIZE) / 2 - (CELL_SIZE * i)
                if cell == 1:
                    self.fill_cell(x, y, CELL_SIZE, 'red')
                elif cell == 2:
                    self.fill_cell(x, y, CELL_SIZE, 'green')
        self.screen.update() # draw the whole maze in one go


    def fill_cell(self, x, y, size, color):
        """Fill a single grid cell at position (x, y) with given color."""
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.setheading(0)
        self.pen.pendown()
        self.pen.fillcolor(color)
        self.pen.begin_fill()
        for _ in range(4):
            self.pen.forward(size)
            self.pen.right(90)
        self.pen.end_fill()
        self.pen.up()

    def build_grid(self):
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



    