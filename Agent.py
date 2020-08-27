from utils.Point2D import Point2D
from enum import Enum
import logging

from Factory import Factory


class Agent:
    class AgentState(Enum):
        IDLE = 1
        TRAVEL = 2
        REPAIR = 3

    def __init__(self, env, velocity, std_working_duration,
                 max_working_duration, travel_cost, overtime_cost):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.env = env
        self.velocity = velocity
        self.std_working_duration = std_working_duration
        self.max_working_duration = max_working_duration
        self.travel_cost = travel_cost
        self.overtime_cost = overtime_cost

        self.day_working_duration = 0
        self.position = Point2D(0, 0)
        self.state = Agent.AgentState.IDLE
        self.target_asset = None

    def step(self):
        if (self.env.time // self.env.DELTA_TIME) % (24 // self.env.DELTA_TIME) == 0:
            self.day_working_duration = 0

        cost = 0
        if self.state != Agent.AgentState.IDLE:
            self.day_working_duration += self.env.DELTA_TIME
            if self.day_working_duration > self.max_working_duration:
                self.logger.error('{self.env.time}: failure, working more than max hours')
                return math.inf
            if self.day_working_duration > self.std_working_duration:
                cost += self.overtime_cost * self.env.DELTA_TIME

        if self.state == Agent.AgentState.IDLE:
            self.target_asset = self.action()
            if isinstance(self.target_asset, Factory):
                self.logger.debug(f'{self.env.time}: going to {self.target_asset}')
                self.state = Agent.AgentState.TRAVEL

        elif self.state == Agent.AgentState.TRAVEL:
            target_asset = self.action() # reevaluate
            if target_asset != self.target_asset:
                self.target_asset = target_asset
                self.logger.debug(f'{self.env.time}: change destination to {self.target_asset}')

            target_vector = self.target_asset - self.position
            target_dis = abs(target_vector)
            if target_dis <= self.env.DELTA_TIME * self.velocity: # reachable
                cost += target_dis * self.travel_cost
                self.position = self.target_asset.position
                if isinstance(self.target_asset, Factory):
                    self.logger.debug(f'{self.env.time}: start repair {self.target_asset}')
                    self.target_asset.repairs()
                    self.state = Agent.AgentState.REPAIR
                else: # back to depot
                    self.logger.debug('{self.env.time}: going back to depot}')
                    self.state = Agent.AgentState.IDLE
            else: # not reachable in this step
                cost += self.velocity * self.env.DELTA_TIME * self.travel_cost
                self.position += target_vector * \
                    (self.velocity * self.env.DELTA_TIME / target_dis)

        elif self.state == Agent.AgentState.REPAIR:
            if self.target_asset.state == Factory.State.GOOD:
                self.target_asset = action()
                self.logger.debug(f'{self.env.time}: repair done, going to {self.target_asset}')
                self.state = Agent.AgentState.TRAVEL

        return cost

    def action(self):
        """
        this should output a Asset object
        """
        return self.env.depot #RTB
        # return self.env.factories[0]
        # return self.env.factories[1]
