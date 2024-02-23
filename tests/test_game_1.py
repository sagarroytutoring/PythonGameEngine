"""
    Initial testing of scene transitions
"""

from typing import Optional, Type

import scene
import data_store
from time import time
import random

from util.rand import rand_prob


class Play(scene.Scene):
    @scene.transition_condition("Death")
    def dead(cls, game, ctx):
        return game.data[cls].health <= 0

    @dead.transition_action
    def death_msg(src, dest, game, ctx):
        print("You died")

    @scene.transition_condition("Leaderboard")
    def won(cls, game, ctx):
        return game.data[cls].enemies == 0

    @won.transition_action
    def win_msg(src, dest, game, ctx):
        print("You won!")

    @scene.transition_action(src="Leaderboard")
    def restart_msg(src, dest, game, ctx):
        print("Now that you've seen the winners, let's play again.")

    @classmethod
    def leave(cls, game, entering, ctx) -> None:
        super().leave(game, entering, ctx)
        print("Game over")

    @staticmethod
    def choose_attack_defend():
        while True:
            choice = input("Do you attack or defend?: ")
            if not choice:
                print("You didn't make a choice!")
                continue
            first_let = choice[0].lower()
            if first_let != 'a' and first_let != 'd':
                print("Please type attack or defend")
                continue
            break
        return first_let

    @classmethod
    def update(cls, game, ctx) -> None:
        super().update(game, ctx)

        print(f"There are {game.data[cls].enemies} enemies left")
        choice = cls.choose_attack_defend()

        # Attacking
        defending = False
        if choice == 'a':
            print("You chose to attack. You kill an enemy!")
            game.data[cls].enemies -= 1
        elif choice == 'd':
            print("You chose to defend.")
            defending = True

        for en_num in range(game.data[cls].enemies):
            print(f"Enemy {en_num+1} attacks you!")

            if rand_prob(game.data[cls].enemy_hit_prob):
                print("The enemy hits you", end='')
                if defending:
                    print(", but you defend", end='')
                else:
                    enemy_dmg = random.randint(*game.data[cls].enemy_dmg_range)
                    game.data[cls].health -= enemy_dmg
                    print(f" and does {enemy_dmg} damage!")
                    print(f"You have {game.data[cls].health} health left", end='')
                print("!")
            else:
                print("The enemy misses.")


class Death(scene.Scene):
    TIMEOUT = 5

    @classmethod
    def enter(cls, game, leaving, ctx) -> None:
        super().enter(game, leaving, ctx)
        print("Enjoy 5 seconds of afterlife.")

    @scene.transition_condition("Leaderboard")
    def timed_out(cls, game, ctx):
        return time() - game.data[cls].start_time >= cls.TIMEOUT


class Leaderboard(scene.Scene):
    @scene.transition_condition(Play)
    def restart(cls, data, ctx):
        return True

    @classmethod
    def update(cls, game, ctx) -> None:
        super().update(game, ctx)

        print("Here are the leaders:")
        for pos, (name, score) in enumerate(game.data[cls].topscores, start=1):
            print(f"{pos}. {name}\t{score}")
        print("Press enter to continue")
        input()


@scene.transition_action(Leaderboard, Death)
def other_didnt_die(src, dest, game, ctx):
    print("You may have died, but here's some winners who didn't!")


class GameData:
    health: int = 100,                      data_store.StoreField.Transient(Play)
    enemies: int = 5,                       data_store.StoreField.Transient(Play)
    name: str = "",                         data_store.StoreField.Global()
    topscores: dict[str, int] = [],         data_store.StoreField.Static(Play, Leaderboard)
    start_time: float = -1,                 data_store.StoreField.Transient(Play, Death, Leaderboard, factory=lambda _: time())

    # You can make config vars for a certain scene by making them Static for that scene only
    enemy_dmg_range: tuple[int, int] = (5, 10),     data_store.StoreField.Static(Play)
    enemy_hit_prob: float = 0.5,                    data_store.StoreField.Static(Play)


class SampleGame(scene.Cursor):
    def run(self) -> None:
        while True:
            self.update()


def main():
    game = SampleGame(GameData, Play)
    game.run()


if __name__ == '__main__':
    main()
