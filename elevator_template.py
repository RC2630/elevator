from typing import NamedTuple, Literal, Callable, Any
from math import isclose
from abc import ABC, abstractmethod

class Task(NamedTuple):

    floor: int
    direction: Literal["up", "down"]
    user_destination_floors: Callable[[], set[int]]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Task):
            return False
        return self.floor == other.floor and self.direction == other.direction

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash((self.floor, self.direction))

    def merge(self, other_task: Task) -> Task:
        assert self == other_task
        return Task(
            self.floor, self.direction,
            lambda: self.user_destination_floors() | other_task.user_destination_floors()
        )

    def __repr__(self) -> str:
        return str((self.floor, self.direction))

class Elevator(ABC):

    def __init__(self, max_floor: int, start_pos: float = 1) -> None:
        '''
        feel free to add other internal fields if necessary.
        `curr_task` is the current task being handled.
        while handling it, don't keep it in `pending_tasks`.
        instead, pop it from `pending_tasks` and assign it to `curr_task`.
        keep the order of tasks in `pending_tasks` ordered by the order in which the tasks came.
        a task comes from someone pressing an up or down button from outside the elevator.
        `internal_lit_floors` tracks which floor numbers have been selected from inside
        the elevator and this not need to be kept in order (hence a set).
        '''
        assert max_floor >= 2 and 1 <= start_pos <= max_floor
        self.curr_pos: float = start_pos
        self.max_floor: int = max_floor
        self.direction: Literal["up", "down", "rest"] = "rest"
        self.internal_lit_floors: set[int] = set()
        self.curr_task: Task | None = None
        self.pending_tasks: list[Task] = []

    def __repr__(self) -> str:
        return str((
            float(f"{self.curr_pos:.2f}"), self.direction,
            sorted(self.internal_lit_floors), self.curr_task, self.pending_tasks
        ))

    @abstractmethod
    def move(self, units: float) -> None:
        '''
        moves `units` of distance (both directions count),
        handling all tasks (i.e. picking up users) AND dropping off users in the process.
        tasks do not need to be handled in the order they came in,
        as long as they are handled in a reasonable manner.
        if the elevator receives a new task while handling a current task, if reasonable,
        it is permitted to put the current task into `pending_tasks` (at the front)
        and handle the new task instead.
        '''
        raise NotImplementedError

    def add_task(self, task: Task) -> None:
        '''
        do not change this method.
        this is called whenever a button from outside the elevator is pressed.
        `task.user_destination_floors()` gives the floors that the user(s) waiting outside the
        elevator will press once the elevator picks them up and lets them into the elevator.
        do not invoke this callback until the elevator actually picked up the user(s) at their
        starting floor. use `pick_up_users_for_curr_task()` instead.
        '''
        assert 1 <= task.floor <= self.max_floor
        if task.floor == 1:
            assert task.direction == "up"
        elif task.floor == self.max_floor:
            assert task.direction == "down"
        if self.curr_task is None:
            self.curr_task = task
        elif task == self.curr_task:
            self.curr_task = self.curr_task.merge(task)
        elif task not in self.pending_tasks:
            self.pending_tasks.append(task)
        else:
            i: int = self.pending_tasks.index(task)
            orig_task: Task = self.pending_tasks[i]
            new_task: Task = orig_task.merge(task)
            self.pending_tasks[i] = new_task

    def pick_up_users_for_curr_task(self) -> None:
        '''
        this should be called whenever the elevator reached the starting floor of the user(s)
        who issued the task that is the elevator's current task, and picked up said user(s).
        if some other user(s) coincidentally want to be dropped off at this floor, that needs to
        be handled separately and before picking up the user(s) for the current task.
        '''
        assert self.curr_task is not None and isclose(self.curr_task.floor, self.curr_pos)
        assert self.curr_task.floor not in self.internal_lit_floors
        new_floors_to_light: set[int] = self.curr_task.user_destination_floors()
        assert len(new_floors_to_light) > 0 and all(
            floor != self.curr_task.floor and 1 <= floor <= self.max_floor
            for floor in new_floors_to_light
        )
        self.internal_lit_floors.update(new_floors_to_light)

    def get_all_tasks(self) -> list[Task]:
        return ([self.curr_task] if self.curr_task is not None else []) + self.pending_tasks

    def activate_task(self, task: Task) -> None:
        if task is self.curr_task:
            return
        assert any(candidate is task for candidate in self.pending_tasks)
        for i, candidate in enumerate(self.pending_tasks):
            if candidate is task:
                self.pending_tasks.pop(i)
                break
        if self.curr_task is not None:
            self.pending_tasks.insert(0, self.curr_task)
        self.curr_task = task

    def finish_curr_task(self) -> None:
        self.curr_task = self.pending_tasks.pop(0) if len(self.pending_tasks) > 0 else None