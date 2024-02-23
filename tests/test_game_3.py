"""
    Testing of subcursor system
"""

from typing import Iterable, Optional

import scene
import data_store

import util.maze


class MazeCharacter(scene.Cursor):
    pass


class Player(MazeCharacter):
    pass


class Runner(MazeCharacter):
    pass


class Hunter(MazeCharacter):
    pass


class MazeGameData:
    pass


class MazeGame(scene.Cursor):
    def run(self) -> None:
        while True:
            self.update()


def main():
    pass


if __name__ == '__main__':
    main()
