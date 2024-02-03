# SPDX-License-Identifier: BSD-3-Clause

from typing import Literal, Union

import numpy as np

from lunarlander import Instructions


def rotate(current: float, target: float) -> Union[Literal["left", "right"], None]:
    if abs(current - target) < 0.5:
        return
    return "left" if current < target else "right"


def find_landing_site(terrain: np.ndarray) -> Union[int, None]:
    # Find largest landing site
    n = len(terrain)
    # Find run starts
    loc_run_start = np.empty(n, dtype=bool)
    loc_run_start[0] = True
    np.not_equal(terrain[:-1], terrain[1:], out=loc_run_start[1:])
    run_starts = np.nonzero(loc_run_start)[0]

    # Find run lengths
    run_lengths = np.diff(np.append(run_starts, n))

    # Find largest run
    imax = np.argmax(run_lengths)
    start = run_starts[imax]
    end = start + run_lengths[imax]

    # Return location if large enough
    if (end - start) > 32:
        loc = int(start + (end - start) * 0.5)
        # print("Found landing site at", loc)
        return loc

def should_stop(target, current) -> bool:
    d = target - current
    if d < 0:
        d += 1920
    # print("distance to target", d)
    m = 2
    if abs(254-d) < m:
        # print("should stop", d, current, target)
        return True
    return False

def at_target(target, current) -> bool:
    d = target - current
    if d < 0:
        d += 1920
    m = 4
    if abs(d) < m:
        return True

def straight_enough(head) -> bool:
    if abs(head) < 1:
        return True
    return False

class Bot:
    """
    This is the lander-controlling bot that will be instantiated for the competition.
    """

    def __init__(self):
        self.team = "Eagle"  # This is your team name
        self.avatar = 0  # Optional attribute
        self.flag = "nl"  # Optional attribute
        self.initial_manoeuvre = True
        self.target_site = None
        self.stopping = False
        self.stopped = False
        self.done_x = 0
        self.stopping_distance = 254
        self.braking_zone = 0
        print("Prepare for boarding")

    def run(
        self,
        t: float,
        dt: float,
        terrain: np.ndarray,
        players: dict,
        asteroids: list,
    ):
        """
        This is the method that will be called at every time step to get the
        instructions for the ship.

        Parameters
        ----------
        t:
            The current time in seconds.
        dt:
            The time step in seconds.
        terrain:
            The (1d) array representing the lunar surface altitude.
        players:
            A dictionary of the players in the game. The keys are the team names and
            the values are the information about the players.
        asteroids:
            A list of the asteroids currently flying.
        """
        instructions = Instructions()

        me = players[self.team]
        x, y = me.position
        vx, vy = me.velocity
        head = me.heading

        # Perform an initial rotation to get the LEM pointing upwards
        if self.initial_manoeuvre:
            command = rotate(current=head, target=0)
            if command == "left":
                instructions.left = True
            elif command == "right":
                instructions.right = True
            else:
                self.initial_manoeuvre = False
                self.done_x = x
                # print("Straightened at x", x, "y", y, "vx", vx, "vy", vy, "head", head)
            return instructions
        

        # Search for a suitable landing site
        if self.target_site is None:
            self.target_site = find_landing_site(terrain)
        elif not self.stopped and not self.stopping and should_stop(self.target_site, x):
            # print("Stopping at target site", self.target_site, "x:", x, "distance:", x - self.done_x)
            self.stopping = True

        if self.stopping:
            # turn to 70 degrees and stop rocket
            command = rotate(current=head, target=70)
            if command == "left":
                instructions.left = True
            elif command == "right":
                instructions.right = True
            
            if vx > 0.1:
                # print("firing to stop")
                instructions.main = True
                self.stopping = True
                return instructions
            else:
                self.stopped = True
                self.stopping = False
                # print("Stopped at x:", x, "target:", self.target_site, "distance:", x - self.done_x)
                # print("Stopping distance:", x - self.done_x)

        if self.stopped:
            slow_done_please = False
            if self.braking_zone == 0: self.braking_zone = (y- terrain[self.target_site]) // 2
            command = rotate(current=head, target=0)
            if command == "left":
                instructions.left = True
                return instructions
            elif command == "right":
                instructions.right = True
                return instructions
            else:
                current_height = y - terrain[self.target_site]
                slow_done_please = current_height < self.braking_zone
                # print("current height", current_height, "braking zone", self.braking_zone, "should stop", slow_done_please)
                if not slow_done_please:
                    # print("falling down")
                    instructions.main = False
                    return instructions
                elif vy < -4.5:
                    # print("firing to land")
                    instructions.main = True
                return instructions

        # if straight_enough(head) and self.target_site and abs(self.target_site - x) < 4 and vy < -4:
        #     print("firing to land")
        #     instructions.main = True
        elif straight_enough(head) and vy < 0:
            # print("firing to hover")
            instructions.main = True
       

        # If no landing site had been found, just hover at 900 altitude.
        # if (self.target_site is None) and (y < 900) and (vy < 0):
        #     instructions.main = True

        # if self.target_site is not None:
        #     command = None
        #     diff = self.target_site - x
        #     if np.abs(diff) < 50:
        #         # Reduce horizontal speed
        #         if abs(vx) <= 0.1:
        #             command = rotate(current=head, target=0)
        #         elif vx > 0.1:
        #             command = rotate(current=head, target=90)
        #             instructions.main = True
        #         else:
        #             command = rotate(current=head, target=-90)
        #             instructions.main = False

        #         if command == "left":
        #             instructions.left = True
        #         elif command == "right":
        #             instructions.right = True

        #         if (abs(vx) < 0.5) and (vy < -3):
        #             instructions.main = True
        #     else:
        #         # Stay at constant altitude while moving towards target
        #         if vy < 0:
        #             instructions.main = True

        return instructions
