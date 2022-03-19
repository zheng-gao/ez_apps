import argparse
import os
from typing import List


class MatrixIterator:
    def __init__(self, matrix: List[list], row: int = 0, col: int = 0, direction: str="horizontal"):
        self.matrix = matrix
        self.row_len = len(matrix)
        self.col_len = len(matrix[0])
        self.row = row
        self.col = col
        self.direction = direction
        self.valid_directions = {"horizontal", "vertical", "ascending-diagonal", "descending-diagonal"}
        if direction not in self.valid_directions:
            raise ValueError(f"Invalid direction \"{self.direction}\", choose from {self.valid_directions}")

    def __iter__(self):
        return self

    def __next__(self):
        if self.direction == "horizontal":
            if self.col < self.col_len:
                data = self.matrix[self.row][self.col]
                self.col += 1
                return data
        elif self.direction == "vertical":
            if self.row < self.row_len:
                data = self.matrix[self.row][self.col]
                self.row += 1
                return data
        elif self.direction == "ascending-diagonal":
            if self.row >= 0 and self.col < self.col_len:
                data = self.matrix[self.row][self.col]
                self.row -= 1
                self.col += 1
                return data
        else:  # "descending-diagonal"
            if self.row < self.row_len and self.col < self.col_len:
                data = self.matrix[self.row][self.col]
                self.row += 1
                self.col += 1
                return data
        raise StopIteration


class ConnectFour:
    def __init__(self, row: int = 6, col: int = 7, players: List[str] = ["X", "O"]):
        self.row_len = row
        self.col_len = col
        self.board = [[-1] * self.col_len for _ in range(self.row_len)]
        self.game_over = False
        self.turn = 0
        self.players = players

    def __str__(self):
        output = "\n"
        for row in range(self.row_len):
            for col in range(self.col_len):
                turn = self.board[row][col]
                output += f"[{self.players[turn]}]" if turn >= 0 else "[ ]"
            output += "\n"
        return output

    def print_board(self, clear=False):
        if clear:
            os.system("clear")
        print(self)

    def next_turn(self):
        self.turn = (self.turn + 1) % len(self.players)

    def validate_selection(self, selection: str) -> (bool, int):
        try:
            column = int(selection)
        except ValueError:
            print(f"[Error] Invalid selection \"{selection}\"")
            return False, -1
        if column < 0 or column >= self.col_len:
            print(f"[Error] Invalid selection \"{selection}\"")
            return False, -1
        if self.board[0][column] != -1:
            print(f"[Error] Column {column} is full!")
            return False, -1
        return True, column

    def prompt_for_selection(self):
        while True:
            prompt = f"User \"{self.players[self.turn]}\", please select column from (0 ~ {self.col_len - 1}): "
            valid_input, column = self.validate_selection(input(prompt))
            if valid_input:
                return column

    def drop_piece(self, column):
        for row in range(self.row_len - 1, -1, -1):
            if self.board[row][column] < 0:
                self.board[row][column] = self.turn
                break

    def check_line(self, line_iterator) -> bool:
        count = 0
        for data in line_iterator:
            count = count + 1 if data == self.turn else 0
            if count == 4:
                return True
        return False

    def check_for_winner(self):
        for row in range(self.row_len):
            if self.check_line(MatrixIterator(self.board, row, 0, "horizontal")):
                return True
            if self.check_line(MatrixIterator(self.board, row, 0, "ascending-diagonal")):
                return True
            if self.check_line(MatrixIterator(self.board, row, 0, "descending-diagonal")):
                return True
        for col in range(self.col_len):
            if self.check_line(MatrixIterator(self.board, 0, col, "vertical")):
                return True
            if col > 0 and self.check_line(MatrixIterator(self.board, self.row_len - 1, col, "ascending-diagonal")):
                return True
            if col > 0 and self.check_line(MatrixIterator(self.board, 0, col, "descending-diagonal")):
                return True
        return False

    def run(self):
        self.print_board()
        while not self.game_over:
            self.drop_piece(self.prompt_for_selection())
            self.print_board()
            if self.check_for_winner():
                print(f"Winner is player \"{self.players[self.turn]}\"")
                self.game_over = True
            else:
                self.next_turn()


parser = argparse.ArgumentParser(description="Connect Four")
parser.add_argument("-r", "--row", dest="row", type=int, default=6, help="Number of rows")
parser.add_argument("-c", "--column", dest="col", type=int, default=7, help="Number of columns")
parser.add_argument("-p", "--players", dest="players", default="X,O", help="Letters separated by comma")
args = parser.parse_args()
if __name__ == "__main__":
    players = args.players.split(",")
    for player in players:
        if len(player) != 1:
            print(f"Invalid player: \"{player}\"")
            exit(1)
    ConnectFour(row=args.row, col=args.col, players=players).run()

    