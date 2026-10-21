import math
import turtle
import tkinter as tk
from collections import deque

STEP_FRAMES = 6   # frames it takes a robot to glide from one cell to the next
FRAME_MS = 16     # delay between frames (~60fps)

# one colour per robot; bfs hands out the next one every time a branch splits off
ROBOT_COLORS = ['#4361ee', '#f77f00', '#2a9d8f', '#7209b7', '#e63946', '#3a86ff',
                '#8ac926', '#fb8500', '#06aed5', '#9d4edd', '#c1121f', '#588157']
DEAD_END_COLOR = '#dcd7cc'
PATH_COLOR = '#ff006e'

_robot_images = {} # (colour, subsample) -> tinted PhotoImage, built once and reused across runs


def lighten(color, amount=0.6):
    """Mix a hex colour with white; used for the trail so robots stand out on it."""
    r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(round(v + (255 - v) * amount) for v in (r, g, b))


def robot_shape(screen, color, cell_size):
    """Register (once) a copy of robot.png recoloured to `color` and sized to fit a cell; return its shape name."""
    if 'full' not in _robot_images:
        _robot_images['full'] = tk.PhotoImage(file='robot.png')
    full = _robot_images['full']
    # PhotoImage can only shrink by whole numbers, so pick the factor that gets closest to ~85% of a cell
    factor = max(1, math.ceil(full.width() / (cell_size * 0.85)))

    name = f'robot{color}x{factor}'
    if (color, factor) not in _robot_images:
        if ('base', factor) not in _robot_images:
            _robot_images[('base', factor)] = full.subsample(factor)
        base = _robot_images[('base', factor)]
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
        _robot_images[(color, factor)] = image

    screen.register_shape(name, turtle.Shape('image', _robot_images[(color, factor)]))
    return name


class Robot:
    def __init__(self, maze, on_status=lambda text: None):
        # share the same grid and screen from the maze class with the robot class
        self.grid = maze.grid
        self.rows = len(maze.grid)
        self.cols = len(maze.grid[0])
        self.screen = maze.screen
        self.maze = maze
        self.on_status = on_status # called with a line of text to show under the maze

    def solve_maze(self, algorithm):
        # algorithm is the name of a solver method: 'dfs' or 'bfs'
        return getattr(self, algorithm)()

    def center(self, cell):
        return self.maze.cell_center(*cell)

    def fill(self, cell, color):
        x, y = self.maze.cell_top_left(*cell)
        self.maze.fill_cell(x, y, self.maze.cell_size, color)

    def new_robot(self, color, cell):
        robot = turtle.Turtle()
        robot.hideturtle()
        robot.shape(robot_shape(self.screen, color, self.maze.cell_size))
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
        pen.pensize(max(2, self.maze.cell_size // 5))
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

    def neighbors(self, cell):
        """Open cells next to `cell` (not walls, not off the grid)."""
        r, c = cell
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != 1:
                yield (nr, nc)

    def shortest_path_length(self):
        """Fewest moves from entrance to exit; plain bfs with no drawing, to score a manual solve."""
        start, goal = (0,1), (self.rows - 1, self.cols - 2)
        distance = {start: 0}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            if cell == goal:
                return distance[cell]
            for nxt in self.neighbors(cell):
                if nxt not in distance:
                    distance[nxt] = distance[cell] + 1
                    queue.append(nxt)
        return None

    def manual(self):
        """Let the player steer the robot with the arrow keys or WASD."""
        start, goal = (0,1), (self.rows - 1, self.cols - 2)
        color = ROBOT_COLORS[0]
        robot = self.new_robot(color, start)
        path = [start] # the player's route so far, with detours cut out
        state = {'moving': False, 'moves': 0, 'done': False}

        def move(dr, dc):
            # ignore key presses while the robot is still gliding, so holding a key moves one cell at a time
            if self.cancelled or state['moving'] or state['done']:
                return
            here = path[-1]
            there = (here[0] + dr, here[1] + dc)
            if there not in self.neighbors(here):
                return # wall or edge of the grid

            state['moving'] = True
            state['moves'] += 1
            if there in path:
                # walked back onto the route: everything after that cell was a detour
                i = path.index(there)
                for cell in path[i+1:]:
                    self.fill(cell, DEAD_END_COLOR)
                del path[i+1:]
            else:
                path.append(there)
                self.fill(there, lighten(color))
            self.on_status(f"Moves: {state['moves']}")

            def arrived():
                state['moving'] = False
                if there == goal:
                    state['done'] = True
                    self.on_status(f"Solved in {state['moves']} moves! "
                                   f"Shortest possible: {self.shortest_path_length()}")
                    self.animate(self.draw_path(path))

            self.animate(self.glide([(robot, here, there)]), on_done=arrived)

        for keys, (dr, dc) in [(('Up', 'w'), (-1, 0)), (('Down', 's'), (1, 0)),
                               (('Left', 'a'), (0, -1)), (('Right', 'd'), (0, 1))]:
            for key in keys:
                self.screen.onkeypress(lambda dr=dr, dc=dc: move(dr, dc), key)
        self.screen.listen() # give the canvas keyboard focus
        self.on_status('Use the arrow keys or WASD to reach the yellow exit')

    def animate(self, steps, on_done=None):
        """Run a generator one frame at a time, then call on_done once it finishes."""
        def tick():
            if self.cancelled:
                return
            try:
                next(steps)
                self.screen.ontimer(tick, FRAME_MS)
            except StopIteration:
                if on_done:
                    on_done()

        tick()

    def run_solver(self, algorithm='dfs'):
        self.cancelled = False
        if algorithm == 'manual':
            self.manual()
        else:
            self.on_status(f'Solving with {algorithm.upper()}')
            self.animate(self.solve_maze(algorithm))
