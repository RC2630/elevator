from elevator_template import *
from math import isfinite
from typing import override

class SweepingElevator(Elevator):

    """
    Direction-preserving LOOK sweep, with direction-aware hall pickups.
    Stops are instantaneous, capacity is unlimited, and passengers requesting
    UP/DOWN are assumed to select destinations above/below their pickup floor.
    """

    _FLOOR_EPS = 1e-9

    @override
    def move(self, units: float) -> None:
        if not isfinite(units) or units < 0:
            raise ValueError('units must be finite and nonnegative')
        remaining = float(units)

        while True:
            tasks = self.get_all_tasks()
            stops = self.internal_lit_floors | {t.floor for t in tasks}
            if not stops:
                self.direction = 'rest'
                return

            # Treat near-exact arrivals as the corresponding integer floor.
            # Use an absolute tolerance (not isclose's relative tolerance),
            # so high floor numbers don't widen the arrival window.
            near = [f for f in stops if abs(self.curr_pos - f) <= self._FLOOR_EPS]
            floor_here = near[0] if near else None
            if floor_here is not None:
                self.curr_pos = float(floor_here)
            pos = self.curr_pos
            if self.direction == 'rest':
                # At wake-up, head straight for the nearest waiting caller.
                # For a caller on our current floor, orient to their request.
                nearest = (
                    min(tasks, key=lambda t: (abs(t.floor - pos), t.floor))
                    if tasks else None
                )
                if nearest is not None:
                    if nearest.floor > pos:
                        self.direction = 'up'
                    elif nearest.floor < pos:
                        self.direction = 'down'
                    else:
                        self.direction = nearest.direction
                else:
                    closest = min(stops, key=lambda f: (abs(f-pos), f))
                    self.direction = 'up' if closest > pos else 'down'

            sign = 1 if self.direction == 'up' else -1
            ahead = [f for f in stops if sign * (f - pos) > 0]
            at_matching = any(
                t.floor == floor_here and t.direction == self.direction for t in tasks
            )
            at_dropoff = floor_here in self.internal_lit_floors

            # Turn only when there is no unfinished business farther ahead.
            # If there is an opposite-direction hall call at our current floor,
            # it can be boarded immediately after turning.
            if not ahead and not at_matching and not at_dropoff:
                self.direction = 'down' if self.direction == 'up' else 'up'
                sign = -sign
                ahead = [f for f in stops if sign * (f - pos) > 0]

            # Dropoffs take precedence over pickups at the same floor.
            did_stop = False
            if floor_here in self.internal_lit_floors:
                self.internal_lit_floors.remove(floor_here)
                did_stop = True

            # A current-floor hall call is served only in its requested
            # direction (after any necessary turn).
            while True:
                matching = next((t for t in self.get_all_tasks()
                                 if t.floor == floor_here and t.direction == self.direction), None)
                if matching is None:
                    break
                self.activate_task(matching)
                self.pick_up_users_for_curr_task()
                self.finish_curr_task()
                did_stop = True

            if did_stop:
                # A pickup might have lit destinations; reconsider the sweep.
                continue

            if remaining == 0:
                return

            # Travel past opposite-direction hall calls unless they are at
            # the turning point. Only compatible pickups and dropoffs are
            # intermediate stops.
            events = [f for f in self.internal_lit_floors if sign*(f-pos) > 0]
            events += [t.floor for t in self.get_all_tasks()
                       if t.direction == self.direction and sign*(t.floor-pos) > 0]
            if events:
                goal = min(events, key=lambda f: sign * (f - pos)) # type: ignore
                # If opposite calls lie beyond every compatible stop, we'll
                # reconsider after serving that stop.
            else:
                ahead = [
                    f for f in (self.internal_lit_floors | {t.floor for t in self.get_all_tasks()})
                    if sign*(f-pos) > 0
                ]
                if not ahead:
                    # Only possible if there is a current-floor opposite call;
                    # next iteration will turn toward it.
                    continue
                # The furthest outstanding call is the turn boundary; a
                # nearer opposite call can be served on the return sweep.
                goal = max(ahead, key=lambda f: sign * (f - pos)) # type: ignore

            distance = abs(goal - pos)
            traveled = min(remaining, distance)
            self.curr_pos = pos + sign * traveled if traveled < distance else float(goal)
            remaining -= traveled
            if traveled < distance:
                return