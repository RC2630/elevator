from elevator_template import *
from typing import override
from math import floor, ceil

class RoyalElevator(Elevator):

    def update_direction(self) -> None:
        if self.curr_task is None and len(self.internal_lit_floors) == 0:
            self.direction = "rest"
        elif isclose(self.curr_pos, 1):
            self.direction = "up"
        elif isclose(self.curr_pos, self.max_floor):
            self.direction = "down"

    def has_useful_work_ahead(self) -> bool:
        assert self.direction != "rest" and isclose(self.curr_pos, round(self.curr_pos))
        curr_floor: int = round(self.curr_pos)
        if self.direction == "up":
            if any(floor > curr_floor for floor in self.internal_lit_floors):
                return True
            elif any(task.floor > curr_floor for task in self.get_all_tasks()):
                return True
            return False
        else:
            if any(floor < curr_floor for floor in self.internal_lit_floors):
                return True
            elif any(task.floor < curr_floor for task in self.get_all_tasks()):
                return True
            return False

    def handle_at_integer(self) -> None:
        floor: int = round(self.curr_pos)
        if floor in self.internal_lit_floors:
            self.internal_lit_floors.remove(floor)
        self.update_direction()
        if self.direction == "rest":
            return
        matching_task = Task(floor, self.direction, lambda: set())
        if matching_task in self.pending_tasks:
            task: Task = self.pending_tasks[self.pending_tasks.index(matching_task)]
            self.activate_task(task)
        if self.curr_task == matching_task:
            self.pick_up_users_for_curr_task()
            self.finish_curr_task()
        if not self.has_useful_work_ahead():
            self.direction = "down" if self.direction == "up" else "up"
            self.handle_at_integer()

    def distance_to_next_integer(self) -> float:
        assert self.direction != "rest"
        if isclose(self.curr_pos, round(self.curr_pos)):
            return 1
        if self.direction == "up":
            next: int = ceil(self.curr_pos)
            return next - self.curr_pos
        else:
            next = floor(self.curr_pos)
            return self.curr_pos - next

    def handle_initial_rest(self) -> None:
        assert len(self.internal_lit_floors) == 0
        if self.curr_task is None:
            return
        if isclose(self.curr_pos, round(self.curr_pos)):
            for task in self.get_all_tasks():
                if task.floor == round(self.curr_pos):
                    self.direction = task.direction
                    break
            self.handle_at_integer()
            if self.direction != "rest":
                return
            if self.curr_task is None:
                if len(self.internal_lit_floors) == 0:
                    return
                assert all(
                    not isclose(floor, self.curr_pos)
                    for floor in self.internal_lit_floors
                )
                higher: int = sum(floor > self.curr_pos for floor in self.internal_lit_floors)
                lower: int = len(self.internal_lit_floors) - higher
                if higher >= lower:
                    self.direction = "up"
                else:
                    self.direction = "down"
                return
        if self.curr_task.floor >= self.curr_pos:
            self.direction = "up"
        else:
            self.direction = "down"

    @override
    def move(self, units: float) -> None:
        assert units >= 0
        if self.direction == "rest":
            self.handle_initial_rest()
            if self.direction == "rest":
                return
        elif isclose(self.curr_pos, round(self.curr_pos)):
            self.handle_at_integer()
            if self.direction == "rest":
                return
        while not isclose(units, 0):
            d: float = self.distance_to_next_integer()
            if d <= units or isclose(d, units):
                self.curr_pos += d if self.direction == "up" else -d
                units -= d
                self.handle_at_integer()
                if self.direction == "rest":
                    return
            else:
                self.curr_pos += units if self.direction == "up" else -units
                return