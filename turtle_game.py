import turtle
import scene


class TurtleGame(scene.Cursor):
    update_interval = 10

    def run(self) -> None:
        self.update()
        turtle.update()
        turtle.ontimer(lambda: self.run(), self.update_interval)
