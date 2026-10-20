import turtle
import tkinter as tk

CELL_SIZE = 30
STEP_FRAMES = 6   # frames it takes a robot to glide from one cell to the next
FRAME_MS = 16     # delay between frames (~60fps)

# one colour per robot; bfs hands out the next one every time a branch splits off
ROBOT_COLORS = ['#4361ee', '#f77f00', '#2a9d8f', '#7209b7', '#e63946', '#3a86ff',
                '#8ac926', '#fb8500', '#06aed5', '#9d4edd', '#c1121f', '#588157']
DEAD_END_COLOR = '#dcd7cc'
PATH_COLOR = '#ff006e'

_robot_images = {} # colour -> tinted PhotoImage, built once and reused across runs


def lighten(color, amount=0.6):
    """Mix a hex colour with white; used for the trail so robots stand out on it."""
    r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(round(v + (255 - v) * amount) for v in (r, g, b))


def robot_shape(screen, color):
    """Register (once) a copy of robot.png recoloured to `color` and return its shape name."""
    name = f'robot{color}'
    if color not in _robot_images:
        if 'base' not in _robot_images:
            _robot_images['base'] = tk.PhotoImage(file='robot.png').subsample(48) # ~26px, fits in a cell
        base = _robot_images['base']
        cr, cg, cb = (int(color[i:i+2], 16) for i in (1, 3, 5))

        image = tk.PhotoImage(width=base.width(), height=base.height())
        for x in range(base.width()):
            for y in range(base.height()):
                if base.transparency_get(x, y):
                    continue
                # dark pixels take the robot colour, light pixels stay light
                light = sum(base.get(x, y)) / 765
                pixel = tuple(round(v * (1 - light) + 255 * light) for v in (cr, cg, cb))
                image.put('#%02x%02x%02x' % pixel, (x, y))
        _robot_images[color] = image

    screen.register_shape(name, turtle.Shape('image', _robot_images[color]))
    return name


class Robot:
    def __init__(self, maze):
        # share the same grid and screen from the maze class with the robot class
        self.grid = maze.grid
        self.rows = len(maze.grid)
        self.cols = len(maze.grid[0])
        self.screen = maze.screen
        self.maze = maze

    def solve_maze(self, algorithm):
        # algorithm is the name of a solver method: 'dfs' or 'bfs'
        return getattr(self, algorithm)()

    def center(self, cell):
        r, c = cell
        return (-CELL_SIZE*self.cols//2 + CELL_SIZE*c + CELL_SIZE//2,
                CELL_SIZE*self.rows//2 - CELL_SIZE*r - CELL_SIZE//2)

    def fill(self, cell, color):
        r, c = cell
        self.maze.fill_cell(-CELL_SIZE*self.cols//2 + CELL_SIZE*c,
                            CELL_SIZE*self.rows//2 - CELL_SIZE*r, CELL_SIZE, color)

    def new_robot(self, color, cell):
        robot = turtle.Turtle()
        robot.hideturtle()
        robot.shape(robot_shape(self.screen, color))
        robot.penup()
        robot.speed(0)  # no built-in animation; glide() moves it frame by frame
        robot.goto(self.center(cell))
        robot.showturtle()
        return robot

    def raise_robots(self):
        # canvas items stack in creation order, so cells filled after a robot was
        # created end up on top of it. Robots are the only images on the canvas.
        canvas = self.screen.getcanvas()
        for item in canvas.find_all():
            if canvas.type(item) == 'image':
                canvas.tag_raise(item)

    def glide(self, moves):
        """Animate every (robot, from_cell, to_cell) in `moves` at the same time."""
        self.raise_robots()
        for frame in range(1, STEP_FRAMES + 1):
            t = frame / STEP_FRAMES
            t = t * t * (3 - 2*t) # ease in and out instead of moving at a constant speed
            for robot, start, end in moves:
                (x0, y0), (x1, y1) = self.center(start), self.center(end)
                robot.goto(x0 + (x1 - x0)*t, y0 + (y1 - y0)*t)
            self.screen.update()
            yield

    def draw_path(self, path):
        """Trace the winning route through the cell centres, one cell per frame."""
        pen = turtle.Turtle()
        pen.hideturtle()
        pen.penup()
        pen.pensize(6)
        pen.pencolor(PATH_COLOR)
        pen.goto(self.center(path[0]))
        pen.pendown()
        for cell in path[1:]:
            pen.goto(self.center(cell))
            self.raise_robots()
            self.screen.update()
            yield

    def dfs(self):
        start = (0,1)
        stack = [start]

        rows = len(self.grid)
        cols = len(self.grid[0])

        visited = {start}
        goal = (rows - 1, cols - 2)

        color = ROBOT_COLORS[0]
        robot = self.new_robot(color, start)

        while stack:
            r, c = stack[-1]

            if (r,c) == goal:
                print(f'winning solution is: {stack}')
                yield from self.draw_path(stack)
                return stack

            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r+dr, c+dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and self.grid[nr][nc] != 1
                        and (nr, nc) not in visited):

                    visited.add((nr, nc))
                    stack.append((nr, nc))
                    self.fill((nr, nc), lighten(color))
                    yield from self.glide([(robot, (r, c), (nr, nc))])
                    break

            else:
                # dead end: grey it out and walk back to the previous cell
                stack.pop()
                self.fill((r, c), DEAD_END_COLOR)
                if stack:
                    yield from self.glide([(robot, (r, c), stack[-1])])

        return None

    def bfs(self):
        start = (0,1)
        visited = {start}
        parent = {start: None}

        rows = len(self.grid)
        cols = len(self.grid[0])

        goal = (rows - 1, cols - 2)

        # expand one whole level per step; every cell on the frontier has its own robot
        frontier = [start]
        robots = {start: (self.new_robot(ROBOT_COLORS[0], start), ROBOT_COLORS[0])}
        colors_used = 1

        while frontier:
            next_frontier = []
            moves = []

            for node in frontier:
                r, c = node
                if (r,c) == goal:
                    path = []
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    path.reverse()

                    print(f'winning solution is: {path}')
                    yield from self.draw_path(path)

                children = []
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r+dr, c+dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and self.grid[nr][nc] != 1
                            and (nr, nc) not in visited):

                        visited.add((nr, nc))
                        parent[(nr, nc)] = node
                        children.append((nr, nc))

                robot, color = robots.pop(node)
                if not children:
                    robot.hideturtle() # dead end, this branch stops here

                for i, child in enumerate(children):
                    # the first branch keeps this robot, every extra branch gets a new colour
                    if i == 0:
                        child_robot, child_color = robot, color
                    else:
                        child_color = ROBOT_COLORS[colors_used % len(ROBOT_COLORS)]
                        colors_used += 1
                        child_robot = self.new_robot(child_color, node)

                    self.fill(child, lighten(child_color))
                    moves.append((child_robot, node, child))
                    robots[child] = (child_robot, child_color)
                    next_frontier.append(child)

            frontier = next_frontier
            yield from self.glide(moves)

        return None

    def run_solver(self, algorithm='dfs'):
        self.cancelled = False
        steps = self.solve_maze(algorithm)

        def tick():
            if self.cancelled:
                return
            try:
                next(steps)
                self.screen.ontimer(tick, FRAME_MS)
            except StopIteration:
                pass

        tick()
