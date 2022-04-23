# from collections import deque

COLOR = {
    "Black":  "\033[30m",
    "Red":    "\033[41m",
    "Green":  "\033[42m",
    "Yellow": "\033[43m",
    "Blue":   "\033[44m",
    "White":  "\033[107m",
    "Reset":  "\033[0m",
}


class Grid:
    def __init__(self, color: str = "White", size: int = 2):
        self.color = color
        self.size = size

    def __str__(self):
        return COLOR[self.color] + " " * self.size + COLOR["Reset"]


class Point:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def move(self, direction):
        self.row += direction.row
        self.col += direction.col


class Shape:
    def __init__(self, outline_color: str = "Black", filled_color: str = None):
        self.outline_color = outline_color
        self.filled_color = filled_color

    def generate_grids(self):
        pass

    def move(self, direction: Point):
        pass


class Line(Shape):
    def __init__(self, point_1: Point, point_2: Point, outline_color: str = "Black"):
        super().__init__(outline_color=outline_color)
        self.point_1 = point_1
        self.point_2 = point_2

    def generate_grids(self):
        # (x - x1) / (x2 - x1) = (y - y1) / (y2 - y1)
        r1, c1, r2, c2 = self.point_1.row, self.point_1.col, self.point_2.row, self.point_2.col
        if abs(r1 - r2) > abs(c1 - c2):
            if r1 > r2:
                r1, r2 = r2, r1
                c1, c2 = c2, c1
            for r in range(r1, r2 + 1):
                c = (r - r1) * (c2 - c1) / (r2 - r1) + c1
                yield (r, round(c), Grid(color=self.outline_color))
        else:
            if c1 > c2:
                r1, r2 = r2, r1
                c1, c2 = c2, c1
            for c in range(c1, c2 + 1):
                r = (r2 - r1) * (c - c1) / (c2 - c1) + r1
                yield (round(r), c, Grid(color=self.outline_color))

    def move(self, direction: Point):
        self.point_1.move(direction)
        self.point_2.move(direction)


class Rectangle(Shape):
    def __init__(self, point_1: Point, point_2: Point, outline_color: str = "Black", filled_color=None):
        super().__init__(outline_color=outline_color, filled_color=filled_color)
        self.point_1 = point_1
        self.point_2 = point_2

    def generate_grids(self):
        r_min, r_max = min(self.point_1.row, self.point_2.row), max(self.point_1.row, self.point_2.row) 
        c_min, c_max = min(self.point_1.col, self.point_2.col), max(self.point_1.col, self.point_2.col)
        for c in range(c_min, c_max + 1):
            yield (r_min, c, Grid(color=self.outline_color))
            yield (r_max, c, Grid(color=self.outline_color))
        for r in range(r_min, r_max + 1):
            yield (r, c_min, Grid(color=self.outline_color))
            yield (r, c_max, Grid(color=self.outline_color))
        if self.filled_color is not None:
            for r in range(r_min + 1, r_max):
                for c in range(c_min + 1, c_max):
                    yield (r, c, Grid(color=self.filled_color))

    def move(self, direction: Point):
        self.point_1.move(direction)
        self.point_2.move(direction)


class Board:
    def __init__(self, row: int, col: int, background_color: str = "White"):
        self.row_len = row
        self.col_len = col
        self.shapes = dict()  # <Shape, int_layer>
        self.layers = list()
        self.matrix = None
        self.background_color = background_color

    def clear(self):
        # self.matrix = deque([deque([Grid(color=self.background_color) for _ in range(self.col_len)]) for _ in range(self.row_len)])
        self.matrix = [[Grid(color=self.background_color) for _ in range(self.col_len)] for _ in range(self.row_len)]

    def expand(self, row, col):
        while row >= len(self.matrix):
            self.matrix.append([Grid(color=self.background_color) for _ in range(self.col_len)])
        self.row_len = len(self.matrix)
        while col >= len(self.matrix[0]):
            for r in range(self.row_len):
                self.matrix[r].append(Grid(color=self.background_color))
        self.col_len = len(self.matrix[0])

    def print(self):
        self.clear()
        for shapes in self.layers:
            for s in shapes:
                for r, c, g in s.generate_grids():
                    self.expand(r, c)
                    self.matrix[r][c] = g
        for r in range(self.row_len):
            for c in range(self.col_len):
                print(self.matrix[r][c], end="")
            print()

    def draw(self, shape: Shape, layer: int = -1):
        if layer == -1:
            self.layers.append(set())
            layer = len(self.layers) - 1
        while layer > len(self.layers) - 1:
            self.layers.append(set())
        self.shapes[shape] = layer
        self.layers[layer].add(shape)

    def layer_move(self, shape: Shape, layer_offset: int):
        if shape in self.shapes:
            layer = self.shapes[shape]
            self.layers[layer].remove(shape)
            self.draw(shape, layer + layer_offset)

    def layer_swap(self, shape_1: Shape, shape_2: Shape):
        if shape_1 in self.shapes and shape_2 in self.shapes:
            layer_1, layer_2 = self.shapes[shape_1], self.shapes[shape_2]
            if layer_1 != layer_2:
                self.layers[layer_1].remove(shape_1)
                self.layers[layer_2].remove(shape_2)
                self.draw(shape_1, layer_2)
                self.draw(shape_2, layer_1)

    def delete(self, shape: Shape):
        if shape in self.shapes:
            layer = self.shapes[shape]
            del self.shapes[shape]
            self.layers[layer].remove(shape)


print("Draw a line, a blue rectangle and a green square with red border")
board = Board(9, 9)
line = Line(Point(1, 7), Point(7, 1))
board.draw(line)
rectangle_1 = Rectangle(Point(1, 1), Point(3, 4), outline_color="Blue", filled_color="Blue")
rectangle_2 = Rectangle(Point(3, 4), Point(6, 7), outline_color="Red", filled_color="Green")
board.draw(rectangle_1)
board.draw(rectangle_2)
board.print()
print("Move the square up by 1 step and left by 2 steps")
rectangle_2.move(Point(-1, -2))
board.print()
print("Layer up the blue rectangle")
board.layer_move(rectangle_1, 1)
board.print()
print("Layer swap the blue rectangle and the red/green square")
board.layer_swap(rectangle_2, line)
board.print()
print("Delete the red/green square")
board.delete(rectangle_2)
board.print()
print("Move the line out of the border and force the board to expand")
line.move(Point(3, 4))
board.print()





