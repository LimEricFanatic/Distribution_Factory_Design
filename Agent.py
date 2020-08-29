from utils.Point2D import Point2D
from enum import Enum
import logging
import geatpy as ea
import math
import numpy as np

from Factory import Factory
from GaCode import GaCode


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
        self.travel_cost = travel_cost        # per unit time
        self.overtime_cost = overtime_cost    # per unit time

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
#            if self.day_working_duration > self.max_working_duration:
#                self.logger.error('{self.env.time}: failure, working more than max hours')
#                return math.inf                                                 #Not perfect
            if self.day_working_duration > self.std_working_duration:
                cost += self.overtime_cost * self.env.DELTA_TIME

        if self.state == Agent.AgentState.IDLE:
            self.target_asset = self.action()
            if isinstance(self.target_asset, Factory):
                self.logger.debug(f'{self.env.time}: going to {self.target_asset}')
                self.state = Agent.AgentState.TRAVEL

        elif self.state == Agent.AgentState.TRAVEL:
            target_asset = self.action()        # reevaluate
            if target_asset != self.target_asset:
                self.target_asset = target_asset
                self.logger.debug(f'{self.env.time}: change destination to {self.target_asset}')

            target_vector = self.target_asset.position - self.position
            target_dis = abs(target_vector)
            if target_dis <= self.env.DELTA_TIME * self.velocity: # reachable
                cost += target_dis * self.travel_cost
                self.position = self.target_asset.position
                if isinstance(self.target_asset, Factory):
                    self.logger.debug(f'{self.env.time}: start repair {self.target_asset}')
                    self.target_asset.repairs()
                    self.state = Agent.AgentState.REPAIR
                    self.env.total_journey.append(self.target_asset.name)
                else:  # back to depot
                    self.logger.debug('{self.env.time}: going back to depot}')
                    self.state = Agent.AgentState.IDLE
            else: # not reachable in this step
                cost += self.velocity * self.env.DELTA_TIME * self.travel_cost
                self.position += target_vector * \
                    (self.velocity * self.env.DELTA_TIME / target_dis)

        elif self.state == Agent.AgentState.REPAIR:
            if self.target_asset.state == Factory.State.GOOD:
                self.target_asset = self.action()
                self.logger.debug(f'{self.env.time}: repair done, going to {self.target_asset}')
                self.state = Agent.AgentState.TRAVEL

        return cost

    def action(self):
        """
        this should output a Asset object
        """

        best_journey = np.array([])
        best_predict_total_cost = 0        # the min total cost in predictable future
        current_failure_number = 0

        current_failure_number = len(self.env.get_failure_factories_information())
        if current_failure_number != 0:
            """===============================实例化问题对象============================"""
            problem = GaCode(self.env)  # 生成问题对象
            """=================================种群设置==============================="""
            Encoding = 'P'  # 编码方式
            NIND = 100  # 种群规模
            Field = ea.crtfld(Encoding, problem.varTypes, problem.ranges, problem.borders)  # 创建区域描述器
            population = ea.Population(Encoding, Field, NIND)  # 实例化种群对象（此时种群还没被初始化，仅仅是完成种群对象的实例化）
            """===============================算法参数设置============================="""
            myAlgorithm = ea.soea_studGA_templet(problem, population)  # 实例化一个算法模板对象
            myAlgorithm.MAXGEN = 100  # 最大进化代数
            myAlgorithm.drawing = 0  # 设置绘图方式（0：不绘图；1：绘制结果图；2：绘制目标空间过程动画；3：绘制决策空间过程动画）
            """==========================调用算法模板进行种群进化======================="""
            [population, obj_trace, var_trace] = myAlgorithm.run()  # 执行算法模板，得到最后一代种群以及进化记录器
            population.save()  # 把最后一代种群的信息保存到文件中
            # 输出结果
            best_gen = np.argmin(obj_trace[:, 1])  # 记录最优种群是在哪一代
            best_ObjV = np.min(obj_trace[:, 1])
            if best_ObjV == 666666666:
                best_predict_total_cost = 0
                best_journey = [self.env.depot]           
            else:
                failure_factories = self.env.get_failure_factories_information()
                failure_factories = np.array(failure_factories)
                best_gen_matrix = var_trace[best_gen].astype(int)
                best_journey = failure_factories[best_gen_matrix]
                best_predict_total_cost = best_ObjV

            print("current journey has been calculated!") 

            # screen show
            print("TIME:")
            print(self.env.time)
            print("Agent's Position:")
            print(self.position)
            print("Current failure number:")
            print(current_failure_number)
            print("best journey is:")
            for factory in best_journey:
                print(factory.name)
            print('Minimum Cost：%s' % best_predict_total_cost)

            if best_journey[0].name == "Factory0":
                return self.env.factories[0]
            elif best_journey[0].name == "Factory1":
                return self.env.factories[1]
            elif best_journey[0].name == "Factory2":
                return self.env.factories[2]
            elif best_journey[0].name == "Factory3":
                return self.env.factories[3]
            elif best_journey[0].name == "Factory4":
                return self.env.factories[4]
            else:
                return self.env.depot
        else: 
            # Screen Show
            print("TIME:")
            print(self.env.time)
            print("Agent's Position:")
            print(self.position)
            print("Current failure number:")
            print(current_failure_number)
            print("best journey is: depot")
            print('Minimum Cost：%s' % best_predict_total_cost)

            return self.env.depot


