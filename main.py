import state
import turtle_game
from dataclasses import dataclass

sm = state.StateMachine()


@dataclass
class PlayData:
    pass

@sm.register("play")
class Gameplay(state.State):
    data = PlayData

    def enter(self, leaving: state.State) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


@dataclass
class DeathData:
    pass

@sm.register("deathscreen")
class Death(state.State):
    data = DeathData

    def enter(self, leaving: state.State) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


@dataclass
class LeaderboardData:
    pass

@sm.register("leaderboard")
class Leaderboard(state.State):
    data = LeaderboardData

    def enter(self, leaving: state.State) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass


class FlappyBird(turtle_game.TurtleGame):
    start_state_id = "play"


def main():
    pass


if __name__ == '__main__':
    main()
