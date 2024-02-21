"""
    More thorough testing of transition condition and transition action system
"""

import sys

import scene
import game
import data_store


class Entry(scene.Scene):
    @classmethod
    def update(cls, game) -> None:
        print("Update for entry scene")
        game.data[cls].num += 1

    @scene.transition_condition("Second")
    def is1(cls, game):
        return game.data[cls].num == 1

    @scene.transition_condition("Second")
    def is3(cls, game):
        return game.data[cls].num == 3

    @is1.transition_action
    def act1(cls, dest, game):
        print("act1")

    @is3.transition_action
    @is1.transition_action
    def act2(cls, dest, game):
        print("act2")

    @is3.transition_action
    def act3(cls, dest, game):
        print("act3")


class Second(scene.Scene):
    @classmethod
    def update(cls, game) -> None:
        print("Update for second scene")
        game.data[cls].num += 1

    @scene.transition_action(dest=Entry)
    @scene.transition_action(src="Third")
    def act4(src, dest, game):
        print(f"act4 while leaving {src.__name__} and entering {dest.__name__}")

    @scene.transition_condition(dest="Entry")
    def is2(cls, game):
        return game.data[cls].num == 2

    @scene.transition_condition(dest="Third")
    def is4(cls, game):
        return game.data[cls].num == 4


class Third(scene.Scene):
    @classmethod
    def update(cls, game):
        print("Done.")
        sys.exit()


@scene.transition_action(src="Second", dest=Third)
def act5(src, dest, game):
    print("act5")


class GameData:
    num: int = 0,   data_store.Access.game()


class TestGame(game.Game):
    def run(self):
        while True:
            self.update()


scene.Scene.assert_no_classnames()


def main():
    game = TestGame(GameData, Entry)
    game.run()


if __name__ == '__main__':
    main()
