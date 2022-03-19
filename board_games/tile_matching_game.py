import argparse
import os
import random
from enum import Enum

COLOR = {
    "Red":    "\033[41m",
    "Green":  "\033[42m",
    "Yellow": "\033[43m",
    "Blue":   "\033[44m",
    "White":  "\033[107m",
    "Reset":  "\033[0m",
}


class BoardState(Enum):
    UNKNOWN = 0
    SUCCEEDED = 1
    FAILED = 2

class TileMatchingError(Exception):
    pass


class Tile:
    def __init__(self, color: str, size: int = 2):
        self.color = color
        self.size = size

    def __str__(self):
        return COLOR[self.color] + " " * self.size + COLOR["Reset"]


class TileMatching:
    def __init__(self, row: int = 10, col: int = 10, tiles: list = [Tile("Red"), Tile("Green"), Tile("Yellow"), Tile("Blue"), Tile("White")]):
        self.row_len, self.col_len = row, col
        self.board = [[-1] * self.col_len for _ in range(self.row_len)]
        self.game_over = False
        self.tiles = tiles
        if row > 10 or col > 10:
            raise TileMatchingError("[Error] Board cannot be larger than 10 x 10")

    def __str__(self):
        output = "\n    "
        for col in range(self.col_len):
            output += f"{str(col).rjust(2, ' ')}"
        output += "\n"
        for row in range(self.row_len):
            output += f"{str(row).rjust(3, ' ')} "
            for col in range(self.col_len):
                tile_id = self.board[row][col]
                output += f"{self.tiles[tile_id]}" if tile_id >= 0 else " " * self.tiles[0].size
            output += "\n"
        return output

    def print_board(self, clear=False):
        if clear:
            os.system("clear")
        print(self)

    def build_board(self):
        while self.check_board_state() != BoardState.UNKNOWN:
            for row in range(self.row_len):
                for col in range(self.col_len):
                    self.board[row][col] = random.randrange(len(self.tiles))

    def validate_selection(self, selection: str) -> (bool, int):
        numbers = selection.split(",")
        if len(numbers) != 2:
            raise TileMatchingError(f"[Error] Invalid delimiter: \"{selection}\"")
        try:
            row, col = int(numbers[0]), int(numbers[1])
        except ValueError:
            raise TileMatchingError(f"[Error] Invalid selection: \"{selection}\"")
        if row < 0 or row >= self.row_len:
            raise TileMatchingError(f"[Error] Invalid row: \"{row}\"")
        if col < 0 or col >= self.col_len:
            raise TileMatchingError(f"[Error] Invalid column: \"{col}\"")
        if self.board[row][col] == -1:
            raise TileMatchingError(f"[Error] Board[{row}][{col}] is empty!")
        if not self.match_blocks(row, col):
            raise TileMatchingError(f"[Error] Board[{row}][{col}] unmatch!")
        return row, col

    def prompt_for_selection(self):
        while True:
            prompt = f"Please select row from [0 ~ {self.row_len - 1}] and " \
                   + f"column from [0 ~ {self.col_len - 1}], separated by comma: "
            try:
                row, col = self.validate_selection(input(prompt))
                return row, col
            except TileMatchingError as e:
                print(e)

    def move_blocks_down(self, row, col):
        for r in range(row - 1, -1, -1):
            self.board[r + 1][col] = self.board[r][col]
        self.board[0][col] = -1

    def match_blocks(self, row, col):
        matched_blocks, block = list(), self.board[row][col]
        if block == -1:
            return list()
        if row > 0 and self.board[row - 1][col] == block:
            matched_blocks.append((-1, 0))
        matched_blocks.append((0, 0))  # Trick!
        if row < self.row_len - 1 and self.board[row + 1][col] == block:
            matched_blocks.append((1, 0))
        if col > 0 and self.board[row][col - 1] == block:
            matched_blocks.append((0, -1))
        if col < self.col_len - 1 and self.board[row][col + 1] == block:
            matched_blocks.append((0, 1))
        return matched_blocks if len(matched_blocks) >= 3 else list()

    def check_board_state(self):
        is_empty, matched_blocks = True, list()
        for row in range(self.row_len):
            for col in range(self.col_len):
                if self.board[row][col] != -1:
                    is_empty = False
                matched_blocks.extend(self.match_blocks(row, col))
        if is_empty:
            return BoardState.SUCCEEDED
        if len(matched_blocks) == 0:
            return BoardState.FAILED
        return BoardState.UNKNOWN

    def run(self):
        self.build_board()
        self.print_board()
        while not self.game_over:
            row, col = self.prompt_for_selection()
            matched_blocks = self.match_blocks(row, col)
            for x, y in matched_blocks:
                self.move_blocks_down(row + x, col + y)
            self.print_board()
            board_state = self.check_board_state()
            if board_state == BoardState.SUCCEEDED:
                print("[Succeeded] You are the winner!")
                self.game_over = True
            elif board_state == BoardState.FAILED:
                print("[Failed] No removable blocks found!")
                self.game_over = True



parser = argparse.ArgumentParser(description="Tile Matching")
parser.add_argument("-r", "--row", dest="row", type=int, default=10, help="Number of rows")
parser.add_argument("-c", "--column", dest="col", type=int, default=10, help="Number of columns")
args = parser.parse_args()
if __name__ == "__main__":
    TileMatching(row=args.row, col=args.col).run()


