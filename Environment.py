import logging
import numpy as np
import math
import matplotlib.pyplot as plt

from Asset import Asset
from Factory import Factory
from Agent import Agent
from utils.Point2D import Point2D


class Environment:
    DELTA_TIME = 0.1 # in hours, should divide 24
    PERIOD = 30  # in days

    def __init__(self):
        self.logger = logging.getLogger("environment")
        self.logger.setLevel(logging.DEBUG)
        self.time = 0
        self.total_cost = 0
        self.total_journey = []
        self.factories = [
            Factory(self, Point2D(1, 1), "Factory0", 2, 2497, 1, 200, 1, 3, 2, 1),
            Factory(self, Point2D(3, 1), "Factory1", 2, 2497, 1, 200, 1, 3, 2, 1),
            Factory(self, Point2D(3, 2), "Factory2", 2, 2497, 1, 200, 1, 3, 2, 1),
            Factory(self, Point2D(1, 4), "Factory3", 2, 2497, 1, 200, 1, 3, 2, 1),
        ]
        self.depot = Asset(self, Point2D(0, 0), "depot")
        self.agent = Agent(self, 1, 8, 10, 1, 2)

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
        if math.isinf(step_cost):
            return True
        self.total_cost += factory_cost + agent_cost
        return False
        
    def get_plot(self):
        # 绘图
        # 清除原有图像
        plt.cla()

        # 设定标题等
        plt.title("DIsPlay")
        plt.grid(True)

        # 生成测试数据 (agent & factories)

        #agent
        x = self.agent.position.x
        y = self.agent.position.y

        # 设置X轴
        plt.xlabel("X轴")
        plt.xlim(-10, 10)
        plt.xticks(np.linspace(-10, 10, 9, endpoint=True))

        # 设置Y轴
        plt.ylabel("Y轴")
        plt.ylim(-10, 10)
        plt.yticks(np.linspace(-10, 10, 9, endpoint=True))

        # Agent Position
        plt.scatter(x, y, s=36, c='blue', marker="+")
        
        # Factories Position & Situation
        factories_x_index = 0
        factories_y_index = 0
        for factory in self.factories:
            factory_situation = 'green'
            if factory.state == Factory.State.GOOD:
                factory_situation = 'green'
            elif factory.state == Factory.State.DOWN:
                factory_situation = 'black'
            elif factory.state == Factory.State.MAINTAIN:
                factory_situation = 'red'
            elif factory.state == Factory.State.REPAIR:
                factory_situation = 'yellow'         
            factories_x_index = factory.position.x
            factories_y_index = factory.position.y           
            plt.scatter(factories_x_index, factories_y_index, s=50, c=factory_situation)


        # 设置图例位置,loc可以为[upper, lower, left, right, center]
        plt.legend(loc="upper left", shadow=True)

        # 暂停
        plt.pause(0.05)

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

    def run(self):
        for i in range(self.PERIOD * 24):
            error = self.step()
            if error:
                break


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
    plt.figure()
    plt.ion()
    for i in range(env.PERIOD * 24):
        error = env.step()
        env.get_plot()
        if error:
            break
    plt.ioff()
    plt.show()
