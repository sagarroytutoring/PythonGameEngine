import scene
import turtle_game
from dataclasses import dataclass

sm = scene.StateMachine()


@dataclass
class PlayData:
    pass

@sm.register("play")
class Gameplay(scene.Scene):
    data = PlayData

    def enter(self, leaving: scene.Scene) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


@dataclass
class DeathData:
    pass

@sm.register("deathscreen")
class Death(scene.Scene):
    data = DeathData

    def enter(self, leaving: scene.Scene) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


@dataclass
class LeaderboardData:
    pass

@sm.register("leaderboard")
class Leaderboard(scene.Scene):
    data = LeaderboardData

    def enter(self, leaving: scene.Scene) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


class FlappyBird(turtle_game.TurtleGame):
    start_scene_id = "play"


def main():
    pass


if __name__ == '__main__':
    main()
