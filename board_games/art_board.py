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
    def __init__(self, row: int, col: int):
        self.row_max = row
        self.col_max = col
        self.layer_max = 0
        self.shapes = list()
        self.matrix = [[None for _ in range(col)] for _ in range(row)]

    def clear(self):
        for r in range(self.row_max):
            for c in range(self.col_max):
                self.matrix[r][c] = Grid(color="White")

    def print(self):
        self.clear()
        for s in self.shapes:
            for r, c, g in s.generate_grids():
                self.matrix[r][c] = g
        for r in range(self.row_max):
            for c in range(self.col_max):
                print(self.matrix[r][c], end="")
            print()

    def draw(self, shape: Shape):
        self.shapes.append(shape)



board = Board(9, 9)
line = Line(Point(2, 7), Point(7, 2))
board.draw(line)
rectangle = Rectangle(Point(2, 3), Point(6, 5), outline_color="Green", filled_color="Green")
board.draw(rectangle)
board.print()
print()
rectangle.move(Point(-1, -2))
board.print()




