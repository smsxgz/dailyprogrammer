import turtle

turtle.tracer(0, 0)
t = turtle.Turtle()
for x in range(0, 501, 2):
    t.left(89.5)
    t.forward(x)

turtle.getscreen().getcanvas().postscript(file='sample.eps')
turtle.done()
# turtle.update()
