import math
import logging
import random
from enum import Enum

from utils import Point2D
from Asset import Asset


class Factory(Asset):
    class State(Enum):
        GOOD = 1
        DOWN = 2
        MAINTAIN = 3
        REPAIR = 4

    factory_cnt = 0
    @classmethod
    def get_factory_cnt(cls):
        cls.factory_cnt += 1
        return cls.factory_cnt - 1

    def __init__(self, env, position,  A, LAMBDA, K, failure_cost,
                 downtime_duration, downtime_duration_cost, maintenance_cost,
                 repair_duration):
        super().__init__(env, position)
        self.name = f"{__name__}{self.get_factory_cnt()}"
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        random.seed()

        self.A = A
        self.LAMBDA = LAMBDA
        self.K = K
        self.failure_cost = failure_cost       # once end
        self.downtime_duration = downtime_duration     # upper limit of downtime
        self.downtime_duration_cost = downtime_duration_cost   # per unit time
        self.maintenance_cost = maintenance_cost    # per unit time
        self.repair_duration = repair_duration

        self.state = Factory.State.GOOD
        self.state_transition_time = 0
        self.repair_time_array = []
        self.failure_cdf = lambda x: 1 - math.exp(-(x / self.LAMBDA) ** self.K)

    def step(self):
        cost = 0
        if self.state == Factory.State.GOOD:
            broken_prob = self.get_failure_prob(
                self.env.time - self.env.DELTA_TIME,
                self.env.time
            )
            if random.random() < broken_prob:
                self.logger.debug(f'{self.env.time}: {repr(self)} downs')
                cost += self.failure_cost
                self.state = Factory.State.DOWN
                self.state_transition_time = self.env.time + self.downtime_duration

        elif self.state == Factory.State.DOWN:
            cost += self.downtime_duration_cost * self.env.DELTA_TIME
            if self.env.time >= self.state_transition_time:
                self.logger.debug(f'{self.env.time}: {repr(self)} maintenance starts')
                self.state = Factory.State.MAINTAIN

        elif self.state == Factory.State.MAINTAIN:
            cost += self.maintenance_cost * self.env.DELTA_TIME

        elif self.state == Factory.State.REPAIR:
            if self.time >= self.state_transition_time:
                self.logger.debug(f'{self.env.time}: {repr(self)} repaired')
                self.failure_cdf = lambda t: self.A * self.failure_cdf(t - time)
                self.repair_time_array.append(time)
                self.state = Factory.State.GOOD

        return cost

    def get_failure_prob(self, t1, t2):
        """
        this function returns the failure prob of this factory between t1 and t2
        """
        return self.failure_cdf(t2) / (1 - self.failure_cdf(t1))

    def repairs(self):
        self.state = Factory.State.REPAIR
        self.state_transition_time = self.env.time + self.repair_duration

    def __repr__(self):
        return self.name
