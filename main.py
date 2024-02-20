import scene
import turtle_game
import data_store

sm = scene.StateMachine()

@sm.register
class Gameplay(scene.Scene): pass

@sm.register
class DeathScreen(scene.Scene): pass

@sm.register
class Leaderboard(scene.Scene): pass


sm.finalize()

class FlappyBirdData:
    turtle: int = 0,            data_store.Access.transient(Gameplay)
    pipes: int = 1,             data_store.Access.transient(Gameplay)
    topscores: dict = {},       data_store.Access.game()
    test_static: int = 5,       data_store.Access.static(DeathScreen, Leaderboard)
    test_transient: int = 6,    data_store.Access.transient(Gameplay, Leaderboard)


class FlappyBird(turtle_game.TurtleGame): pass


def main():
    game = FlappyBird(FlappyBirdData, Gameplay)
    game.run()


if __name__ == '__main__':
    main()
