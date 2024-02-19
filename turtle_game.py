import turtle

import game


class TurtleGame(game.Game):
    update_interval = 10

    def run(self) -> None:
        self.update()
        turtle.update()
        turtle.ontimer(lambda: self.run(), self.update_interval)
