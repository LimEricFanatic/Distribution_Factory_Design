import logging
import numpy as np
import math

from Asset import Asset
from Factory import Factory
from Agent import Agent
from utils.Point2D import Point2D

class Environment:
    DELTA_TIME = 0.1 # in hours, should divide 24

    def __init__(self):
        self.logger = logging.getLogger("environment")
        self.logger.setLevel(logging.DEBUG)
        self.time = 0
        self.total_cost = 0

        self.factories = [
            Factory(self, Point2D(1, 1), 1.04, 2497, 2.86, 200, 1, 3, 2, 1),
            Factory(self, Point2D(3, 1), 1.04, 2497, 2.86, 200, 1, 3, 2, 1),
            Factory(self, Point2D(3, 2), 1.04, 2497, 2.86, 200, 1, 3, 2, 1),
            Factory(self, Point2D(3, 3), 1.04, 2497, 2.86, 200, 1, 3, 2, 1),
        ]
        self.depot = Asset(self, Point2D(0, 0))
        self.agent = Agent(self, 1, 8, 10, 1, 2)

    def step(self):
        """
        simulating the next DELTA_TIME
        returns: failure
        """
        self.time += self.DELTA_TIME
        factory_cost = 0
        for factory in self.factories:
            factory_cost += factory.step()

        agent_cost = self.agent.step()

        step_cost = factory_cost + agent_cost
        if math.isinf(step_cost):
            return True
        self.total_cost += factory_cost + agent_cost
        return False


if __name__ == '__main__':
    # https: // docs.python.org / 3 / howto / logging - cookbook.html
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='log',
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    env = Environment()
    for i in range(10000):
        error = env.step()
        if error:
            break