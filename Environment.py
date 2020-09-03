import logging
import numpy as np
import math
import matplotlib.pyplot as plt

from Asset import Asset
from Factory import Factory
from Depot import Depot
from Agent import Agent
from utils.Point2D import Point2D


class Environment:
    DELTA_TIME = 0.1 # in hours, should divide 24
    PERIOD = 31  # in days

    def __init__(self):
        self.logger = logging.getLogger("environment")
        self.logger.setLevel(logging.DEBUG)
        self.time = 0
        self.total_cost = 0
        self.factories = [
            Factory(self, Point2D(7, 1), "Factory0", 2, 2497, 1, 200, 1, 30, 10, 1, 50, 0.005),
            Factory(self, Point2D(-8, 6), "Factory1", 2, 2497, 1, 200, 1, 30, 10, 1, 50, 0.005),
            Factory(self, Point2D(3, -9), "Factory2", 2, 2497, 1, 200, 1, 30, 10, 1, 50, 0.005),
            Factory(self, Point2D(-1, -3), "Factory3", 2, 2497, 1, 200, 1, 30, 10, 1, 50, 0.005),
        ]
        self.depot = Depot(self, Point2D(0, 0), "Depot")
        self.agent = Agent(self, 8, 5, 12, 100, 20)
        self.total_journey = []
        self.t_list = [0]
        self.MODE = 'Pre_Repair'

    def step(self):
        """
        simulating the next DELTA_TIME
        returns: failure
        """
        self.time += self.DELTA_TIME                    # plus one unit time
        factory_cost = 0                                # the Factory cost in per unit time
        for factory in self.factories:
            factory_cost += factory.step()
        agent_cost = self.agent.step()
        step_cost = factory_cost + agent_cost
        self.t_list.append(self.time)
        if math.isinf(step_cost):
            return True
        self.total_cost += (factory_cost + agent_cost)
        return False
    
    def get_failure_factories_information(self):
        """
        get current failure factories' information
        :return: matrix of ( 1 * n ) 
        """
        failure_factories = []
        for factory in self.factories:
            if factory.state == factory.State.DOWN:
                failure_factories.append(factory)
            elif factory.state == factory.State.MAINTAIN:
                failure_factories.append(factory)
        return failure_factories

    def get_prob_failure_factories_information(self):
        """
        when failure prob >= 0.005, it will be counted
        """
        prob_failure_factories = []
        for factory in self.factories:
            if factory.state == factory.State.GOOD:
                if factory.broken_prob >= factory.tol_up:
                    prob_failure_factories.append(factory)
        if self.MODE == 'Pre_Repair':
            return prob_failure_factories
        else:
            return []


    def run(self):
        for i in range(self.PERIOD * 24):
            error = self.step()
            if error:
                break