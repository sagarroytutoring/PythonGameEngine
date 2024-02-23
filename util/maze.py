from typing import Iterable


class MazeChars:
    def __init__(self, maze_str: str):
        """
        To define a set of maze characers for drawing, pass in a string such as this:

        ╭─┬─╮
        │ │ │
        ├─┼─┤
        │ │ │
        ╰─┴─╯
         ╵ 
        ╴·╶
         ╷ 

        :param maze_str: a string of a 2x2 grid with all the needed , then a cross
        """

        (
            top_row, row2, mid_row, row4, bot_row,  # 2x2 portion
            self.top, (self.left, self.mid, self.right), self.bot  # cross portion
        ) = map(str.strip, maze_str.strip().split('\n'))

        self.topleft, horiz1, self.top_t, horiz2, self.topright = top_row
        if horiz1 != horiz2:
            raise ValueError("Horizontal bars in top row do not match")
        self.horiz = horiz1

        vert1, space1, vert2, space2, vert3 = row2
        if not vert1 == vert2 == vert3:
            raise ValueError("Vertical bars in second row do not match")
        if not space1 == space2 == ' ':
            raise ValueError("Second row is missing spaces")
        self.vert = vert1

        self.left_t, horiz1, self.mid_t, horiz2, self.right_t = mid_row
        if horiz1 != horiz2:
            raise ValueError("Horizontal bars in middle row do not match")
        if self.horiz != horiz1:
            raise ValueError("Horizontal bars in middle row do not match horizontal bars in top row")

        if row4 != row2:
            raise ValueError("Row 4 does not match row 2")

        self.botleft, horiz1, self.bot_t, horiz2, self.botright = bot_row
        if horiz1 != horiz2:
            raise ValueError("Horizontal bars in bottom row do not match")
        if self.horiz != horiz1:
            raise ValueError("Horizontal bars in bottom row do not match horizontal bars in other rows")

        self.chars = [
            # No Wall Up
            [
                # No Wall Right
                [
                    # No Wall Down
                    [
                        # No Wall Left
                        self.mid,
                        # Wall Left
                        self.left
                    ],
                    # Wall Down
                    [
                        # No Wall Left
                        self.bot,
                        # Wall Left
                        self.topright
                    ]
                ],
                # Wall Right
                [
                    # No Wall Down
                    [
                        # No Wall Left
                        self.right,
                        # Wall Left
                        self.horiz
                    ],
                    # Wall Down
                    [
                        # No Wall Left
                        self.topleft,
                        # Wall Left
                        self.top_t
                    ]
                ]
            ],
            # Wall Up
            [
                # No Wall Right
                [
                    # No Wall Down
                    [
                        # No Wall Left
                        self.top,
                        # Wall Left
                        self.botright
                    ],
                    # Wall Down
                    [
                        # No Wall Left
                        self.vert,
                        # Wall Left
                        self.right_t
                    ]
                ],
                # Wall Right
                [
                    # No Wall Down
                    [
                        # No Wall Left
                        self.botleft,
                        # Wall Left
                        self.bot_t
                    ],
                    # Wall Down
                    [
                        # No Wall Left
                        self.left_t,
                        # Wall Left
                        self.mid_t
                    ]
                ]
            ]
        ]


rounded_maze_chars = MazeChars(
"""
╭─┬─╮
│ │ │
├─┼─┤
│ │ │
╰─┴─╯
 ╵ 
╴·╶
 ╷ 
"""
)

doubleline_maze_chars = MazeChars(
"""
╔═╦═╗
║ ║ ║
╠═╬═╣
║ ║ ║
╚═╩═╝
 ╨ 
╡◦╞
 ╥ 
"""
)

ascii_maze_chars = MazeChars(
"""
+-+-+
| | |
+-+-+
| | |
+-+-+
 | 
-+-
 | 
"""
)


class Maze:
    def __init__(self, chars: MazeChars, walls: list[list[int | bool]]):
        self.chars = chars
        self.walls = walls
        self.height = len(walls)
        self.width = len(walls[0])

    def wall_dirs(self, row, col):
        return [
            row > 0             and self.walls[row-1][col],
            col < self.width-1  and self.walls[row][col+1],
            row < self.height-1 and self.walls[row+1][col],
            col > 0             and self.walls[row][col-1]
        ]

    def draw(self, symbols: Iterable[tuple[str, int, int]] = None):
        symbols = [] if symbols is None else symbols
        symbols_dict = {(row, col): symbol for symbol, row, col in symbols}

        for row_num, row in enumerate(self.walls):
            for col_num, wall in enumerate(row):
                if wall:
                    up, right, down, left = self.wall_dirs(row_num, col_num)
                    print(self.chars.chars[up][right][down][left], end='')
                else:
                    print(symbols_dict.get((row_num, col_num), ' '), end='')
            print()


if __name__ == "__main__":
    grid_1 = [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 0, 1, 1],
        [0, 1, 0, 0],
        [1, 0, 1, 1],
        [1, 1, 1, 0],
        [1, 0, 1, 0],
        [1, 1, 1, 1],
        [1, 0, 1, 0]
    ]
    maze = Maze(doubleline_maze_chars, grid_1)
    maze.draw([('*', 1, 1), ('+', 3, 1)])

