import entity
import turtle


class TurtleEntity(entity.Entity):
    def __init__(self, shape: str, x=0, y=0, hitwidth=0, hitheight=0):
        super().__init__(x, y, hitwidth, hitheight)
        self.turtle = self.create_default_turtle()
        self.turtle.shape(shape)

    @classmethod
    def create_default_turtle(cls):
        t = turtle.Turtle()
        t.speed(0)
        t.up()
        return t

    @classmethod
    def create_text_turtle(cls, color):
        t = cls.create_default_turtle()
        t.hideturtle()
        t.color(color)
        return t


class TurtleGifEntity(TurtleEntity, entity.AnimatedEntity):
    def __init__(self, folderpath, x=0, y=0, hitwidth=0, hitheight=0, file_ext="gif"):
        super(entity.AnimatedEntity).__init__(folderpath, x, y, hitwidth, hitheight, file_ext)
        for frame in self.frames:
            turtle.addshape(frame)
        super().__init__(self.frames[0], x, y, hitwidth, hitheight)
