from elevator_template import *
from typing import override
from math import isfinite

class SimpleElevator(Elevator):

    @override
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
        if not isfinite(units) or units < 0:
            raise ValueError("units must be finite and nonnegative")

        remaining = float(units)

        while True:
            jobs = (
                ([self.curr_task] if self.curr_task is not None else [])
                + self.pending_tasks
            )

            # No more work: stay where we are.
            if not jobs and not self.internal_lit_floors:
                self.direction = "rest"
                break

            if self.internal_lit_floors:
                # Passengers inside take priority.
                # Maintain our direction if a dropoff lies ahead.
                ahead = [
                    f for f in self.internal_lit_floors
                    if (
                        self.direction == "up" and f > self.curr_pos
                    ) or (
                        self.direction == "down" and f < self.curr_pos
                    )
                ]

                if ahead:
                    target = (
                        min(ahead) if self.direction == "up"
                        else max(ahead)
                    )
                else:
                    # No dropoff ahead: choose the closest one.
                    target = min(
                        self.internal_lit_floors,
                        key=lambda f: (abs(f - self.curr_pos), f)
                    )
            else:
                # Empty elevator: choose the nearest hall call.
                # Ties preserve current/queue priority.
                chosen = min(
                    jobs,
                    key=lambda t: abs(t.floor - self.curr_pos)
                )
                self.activate_task(chosen)
                target = chosen.floor

            step = (
                1 if target > self.curr_pos
                else -1 if target < self.curr_pos
                else 0
            )

            if step == 0:
                # Handle events at our current position without
                # consuming any movement.
                self.internal_lit_floors.discard(target)

                if (
                    self.curr_task is not None
                    and self.curr_task.floor == target
                ):
                    self.pick_up_users_for_curr_task()
                    self.finish_curr_task()

                continue

            heading = "up" if step == 1 else "down"

            # Find compatible hall calls on the path to our target.
            eligible = [
                t for t in jobs
                if t.direction == heading
                and 0 <= step * (t.floor - self.curr_pos)
                    <= step * (target - self.curr_pos)
            ]

            # An empty elevator may approach its assigned pickup
            # from either direction.
            if (
                not self.internal_lit_floors
                and self.curr_task is not None
            ):
                if all(t is not self.curr_task for t in eligible):
                    eligible.append(self.curr_task)

            # The next stop is either the planned target or
            # an earlier compatible pickup.
            stop = target

            if eligible:
                stop = min(
                    [target] + [t.floor for t in eligible],
                    key=lambda f: step * (f - self.curr_pos)
                )

            distance = abs(stop - self.curr_pos)
            self.direction = heading

            if remaining < distance:
                # We cannot reach the next stop yet.
                self.curr_pos += step * remaining
                break

            # Reach the next stop exactly.
            remaining -= distance
            self.curr_pos = float(stop)

            # Always drop off BEFORE picking up.
            self.internal_lit_floors.discard(stop)

            hall = [t for t in eligible if t.floor == stop]

            if hall:
                # Prefer the active task if it is among the calls.
                pickup = next(
                    (t for t in hall if t is self.curr_task),
                    hall[0]
                )

                self.activate_task(pickup)
                self.pick_up_users_for_curr_task()
                self.finish_curr_task()

            # Repeat: the newly boarded users may have introduced
            # additional stops, even with zero distance remaining.