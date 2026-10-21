from elevator_template import *

def test(elevator_type: type[Elevator]) -> None:

    e = elevator_type(max_floor=10)
    e.add_task(Task(2, "up", lambda: {8}))
    e.add_task(Task(5, "up", lambda: {9}))
    e.add_task(Task(6, "down", lambda: {1}))

    e.move(4)
    print(e.curr_pos)
    print(e.internal_lit_floors)
    print(e.direction)

    e.move(4)
    print(e.curr_pos)
    print(e.internal_lit_floors)
    print(e.direction)

    e.move(3)
    print(e.curr_pos)
    print(e.internal_lit_floors)
    print(e.direction)

    e.move(5)
    print(e.curr_pos)
    print(e.internal_lit_floors)
    print(e.direction)

def starve(elevator_type: type[Elevator]) -> None:

    e = elevator_type(max_floor = 10)
    e.add_task(Task(2, "up", lambda: {7}))
    e.add_task(Task(7, "down", lambda: {2}))
    e.move(1.5)
    e.add_task(Task(1, "up", lambda: {9}))

    for i in range(10030):
        e.move(0.1)
        if isclose(e.curr_pos, 4.5):
            if e.direction == "down":
                e.add_task(Task(7, "down", lambda: {2}))
            else:
                e.add_task(Task(2, "up", lambda: {7}))

    print(f"{e.curr_task = }")
    print(f"{e.pending_tasks = }")
    print(f"{(e.curr_pos, e.direction) = }")