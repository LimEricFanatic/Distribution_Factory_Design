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

    def __init__(self, env, position, name,  A, LAMBDA, K, failure_cost,
                 downtime_duration, downtime_duration_cost, maintenance_cost,
                 repair_duration, pre_repair_cost, tol_up):
 #       self.name = f"{__name__}{self.get_factory_cnt()}"       
        self.name = name        
        super().__init__(env, position, self.name)
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
        self.pre_repair_cost = pre_repair_cost
        self.tol_up = tol_up

        self.state = Factory.State.GOOD
        self.state_transition_time = 0
        self.repair_time_array = [0]         # finish time records
        self.repair_times = 0
        self.broken_prob = 0
        self.prob_list = [0]
        self.cdf_list = [0]
        self.cdf = 0
        self.pre_repair_flag = True

    def step(self):
        cost = 0
        if self.state == Factory.State.GOOD:
            self.broken_prob = self.get_failure_prob(
                self.env.time - self.repair_time_array[-1] - self.env.DELTA_TIME,
                self.env.time - self.repair_time_array[-1]
            )
            self.cdf = self.get_failure_cdf(self.env.time - self.repair_time_array[-1])
            if random.random() < self.broken_prob:
                self.logger.debug(f'{self.env.time}: {repr(self)} downs')
                self.broken_prob = 1.0
                self.cdf = 1.0
                self.state = Factory.State.DOWN
                self.state_transition_time = self.env.time + self.downtime_duration

        elif self.state == Factory.State.DOWN:
            if self.pre_repair_flag == True:
                self.pre_repair_flag = False
            cost += self.downtime_duration_cost * self.env.DELTA_TIME
            if self.env.time >= self.state_transition_time:
                self.logger.debug(f'{self.env.time}: {repr(self)} maintenance starts')
                self.state = Factory.State.MAINTAIN

        elif self.state == Factory.State.MAINTAIN:
            cost += self.maintenance_cost * self.env.DELTA_TIME

        elif self.state == Factory.State.REPAIR:
            if self.env.time >= self.state_transition_time:
                self.logger.debug(f'{self.env.time}: {repr(self)} repaired')
                if self.pre_repair_flag:       # repair before DOWN
                    cost += self.pre_repair_cost
                else:                      #repair after DOWN
                    cost += self.failure_cost
                self.repair_time_array.append(self.env.time)
                self.repair_times += 1 
                self.pre_repair_flag = True
                self.state = Factory.State.GOOD

        self.prob_list.append(self.broken_prob)
        self.cdf_list.append(self.cdf)
        return cost

    def get_failure_prob(self, t1, t2):
        """
        this function returns the failure prob of this factory between t1 and t2
        """
        return (self.get_failure_cdf(t2) / (1 - self.get_failure_cdf(t1)))

    def get_failure_cdf(self, x): 
        return (1 - math.exp(-(x / self.LAMBDA) ** self.K))    
 
    def repairs(self):
        self.state = Factory.State.REPAIR
        self.state_transition_time = self.env.time + self.repair_duration

    def __repr__(self):
        return self.name
    

