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


@dataclass
class DeathData:
    pass

@sm.register("deathscreen")
class Death(scene.Scene):
    data = DeathData


@dataclass
class LeaderboardData:
    pass

@sm.register("leaderboard")
class Leaderboard(scene.Scene):
    data = LeaderboardData


class FlappyBird(turtle_game.TurtleGame):
    start_scene_id = "play"


def main():
    pass


if __name__ == '__main__':
    main()
