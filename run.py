from elevator_template import *
from time import sleep
from datetime import datetime
from threading import Thread, Lock
from functools import partial
from random import randint, expovariate
from numpy.random import geometric

HALL_CALLS_FILE: str = "data/hall_calls.txt"
BUTTONS_FILE: str = "data/buttons.txt"
LOG_FILE: str = "data/run.log"

FILE_LOCK = Lock()
LOG_LOCK = Lock()

USED_IDS: set[int] = set()
BIG_NUMBER: int = 10 ** 15

def generate_unique_id() -> int:
    id: int = randint(0, BIG_NUMBER)
    while id in USED_IDS:
        id = randint(0, BIG_NUMBER)
    USED_IDS.add(id)
    return id

def parse_buttons(id: int) -> set[int]:
    numbers: set[int] = set()
    lines: list[str] = []
    with FILE_LOCK:
        with open(BUTTONS_FILE, "r") as f:
            for line in f.read().splitlines():
                if line == "":
                    continue
                parts: list[int] = [int(n) for n in line.split(" ")]
                if parts[0] == id:
                    numbers = set(parts[1:])
                else:
                    lines.append(line)
        with open(BUTTONS_FILE, "w") as f:
            f.write("\n".join(lines) + "\n")
    assert len(numbers) > 0
    return numbers

def parse_hall_calls() -> list[Task]:
    with FILE_LOCK:
        with open(HALL_CALLS_FILE, "r") as f:
            content: str = f.read()
        with open(HALL_CALLS_FILE, "w") as f:
            f.write("")
    tasks: list[Task] = []
    for line in content.splitlines():
        if line == "":
            continue
        parts: list[str] = line.split(" ")
        floor: int = int(parts[0])
        direction: str = parts[1]
        id: int = int(parts[2])
        if direction in ("up", "down"):
            tasks.append(Task(floor, direction, partial(parse_buttons, id)))
    return tasks

def run_elevator(
    elevator: Elevator, tick_seconds: float,
    floors_per_second: float, approx_seconds_per_log: float
) -> None:
    iterations: int = 0
    while True:
        if iterations % max(1, round(approx_seconds_per_log / tick_seconds)) == 0:
            with LOG_LOCK:
                with open(LOG_FILE, "a") as f:
                    f.write(f"[{datetime.now()}] Elevator: {elevator}\n")
        for task in parse_hall_calls():
            try:
                elevator.add_task(task)
            except AssertionError:
                pass
        elevator.move(floors_per_second * tick_seconds)
        sleep(tick_seconds)
        iterations += 1

def is_eligible(
    dest_floor: int, curr_floor: int, direction: Literal["up", "down"], max_floor: int
) -> bool:
    if dest_floor < 1 or dest_floor > max_floor:
        return False
    if direction == "up":
        return dest_floor > curr_floor
    else:
        return dest_floor < curr_floor

def generate_direction(floor: int, max_floor: int) -> Literal["up", "down"]:
    if floor == 1:
        return "up"
    elif floor == max_floor:
        return "down"
    else:
        return "up" if randint(0, 1) == 1 else "down"

def add_tasks(max_floor: int, avg_gap_seconds: float, prob_single_dest: float) -> None:
    while True:
        sleep(expovariate(1 / avg_gap_seconds))
        floor: int = randint(1, max_floor)
        direction: Literal["up", "down"] = generate_direction(floor, max_floor)
        destinations: set[int] = set()
        eligible: list[int] = [
            f for f in range(1, max_floor + 1)
            if is_eligible(f, floor, direction, max_floor)
        ]
        for i in range(geometric(prob_single_dest)):
            destinations.add(eligible[randint(0, len(eligible) - 1)])
        id: int = generate_unique_id()
        nums_to_write: str = " ".join(str(n) for n in destinations)
        with LOG_LOCK:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{datetime.now()}] New Task: "
                        f"{(floor, direction, sorted(destinations))}\n")
        with FILE_LOCK:
            with open(HALL_CALLS_FILE, "a") as f:
                f.write(f"{floor} {direction} {id}\n")
            with open(BUTTONS_FILE, "a") as f:
                f.write(f"{id} {nums_to_write}\n")

def main(
    elevator_type: type[Elevator], max_floor: int = 10,
    avg_gap_seconds: float = 2, prob_single_dest: float = 0.5,
    tick_seconds: float = 0.01, floors_per_second: float = 1,
    approx_seconds_per_log: float = 1, start_pos: float = 1
) -> None:
    with open(HALL_CALLS_FILE, "w") as f:
        f.write("")
    with open(BUTTONS_FILE, "w") as f:
        f.write("")
    with open(LOG_FILE, "w") as f:
        f.write("")
    Thread(target = partial(
        run_elevator, elevator_type(max_floor, start_pos),
        tick_seconds, floors_per_second, approx_seconds_per_log
    ), daemon = True).start()
    Thread(target = partial(
        add_tasks, max_floor, avg_gap_seconds, prob_single_dest
    ), daemon = True).start()