from utils.Point2D import Point2D
from enum import Enum
import logging
import geatpy as ea
import math
import numpy as np
import itertools

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
        self.travel_cost = travel_cost        # per unit distance
        self.overtime_cost = overtime_cost    # per unit time

        self.day_working_duration = 0        # day working duration
        self.position = Point2D(0, 0)
        self.state = Agent.AgentState.IDLE
        self.target_asset = None
        self.predict_route = []
        self.predict_cost = 0
        self.reachable_flag = False

    def step(self):
        if (self.env.time // self.env.DELTA_TIME) % (24 // self.env.DELTA_TIME) == 0:
            self.day_working_duration = 0

        cost = 0
        if self.state != Agent.AgentState.IDLE:
            self.day_working_duration += self.env.DELTA_TIME
            if self.day_working_duration > self.std_working_duration:
                self.logger.error('{self.env.time}: working more than standard working hours')
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
                self.reachable_flag = True
                cost += (target_dis * self.travel_cost)
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
                self.reachable_flag =False
                cost += (self.velocity * self.env.DELTA_TIME * self.travel_cost)
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
        route_cost_plan = []               
        TO_go_factories = []
        viable_route_cost_plan = []
        TO_go_factories_num = len(self.env.get_failure_factories_information())
        TO_go_prob_factories_num = len(self.env.get_prob_failure_factories_information())
        circle_flag = False
        no_rest_flag = False
        no_same_flag = False
        
        if self.position == self.env.depot.position:          # fasten the decision
            for factory in self.env.factories:
                action_duration = 2 * abs(self.position - factory.position) / self.velocity + factory.repair_duration
                left_duration = self.max_working_duration - self.day_working_duration
                if ((action_duration <= left_duration) and(factory.state != factory.State.GOOD)):
                    no_rest_flag = True
            if no_rest_flag == False:
                self.predict_route = [self.env.depot]
                self.predict_cost = -1
                return self.env.depot
        if ((self.state == Agent.AgentState.TRAVEL or self.state == Agent.AgentState.IDLE) and self.reachable_flag == False):
            if len(self.env.get_failure_factories_information()) != 0:
                for factory in self.env.get_failure_factories_information():
                    if factory not in self.predict_route:
                        no_same_flag = True
            else:
                for factory in self.env.get_prob_failure_factories_information():
                    if factory not in self.predict_route:
                        no_same_flag = True
            if no_same_flag == False:
                if len(self.predict_route) == 0:
                    return self.env.depot
                else:
                    return self.predict_route[0]

        if ((TO_go_factories_num == 0) and (TO_go_prob_factories_num == 0)):
            direct_distance = abs(self.position - self.env.depot.position)
            direct_duration = direct_distance / self.velocity
            if (self.day_working_duration + direct_duration) <= self.std_working_duration:    # arrive depot in std time
                self.predict_cost = direct_distance * self.travel_cost + self.env.total_cost
            else:  # arrive in overtime
                if self.day_working_duration < self.std_working_duration:
                    self.predict_cost = (self.day_working_duration + direct_duration - self.std_working_duration) * self.overtime_cost \
                        + direct_distance * self.travel_cost + self.env.total_cost
                else:
                    self.predict_cost = direct_duration * self.overtime_cost + direct_distance * self.travel_cost + self.env.total_cost      
            self.predict_route = [self.env.depot]
            return self.env.depot
        elif (TO_go_factories_num != 0):
            TO_go_factories = self.env.get_failure_factories_information()
        else:
            TO_go_factories_num = TO_go_prob_factories_num            # predict repair
            TO_go_factories = self.env.get_prob_failure_factories_information()
        
        route_cost_plan.append(self.get_route_and_cost(TO_go_factories))
        
        if route_cost_plan[0][1] == 999999999.0:     # over time work
            circle_flag = True
            while((TO_go_factories_num > 0) and (circle_flag)):
                new_TO_go_factories = list(itertools.combinations(TO_go_factories, TO_go_factories_num))
                for i in range(len(new_TO_go_factories)):
                    route_cost_plan.append(self.get_route_and_cost(new_TO_go_factories[i]))
                for i in range(len(route_cost_plan)):
                    if route_cost_plan[i][1] != 999999999.0:
                        viable_route_cost_plan.append(route_cost_plan[i])
                if (len(viable_route_cost_plan)) != 0:    # have viable result
                    temp_predict_route = viable_route_cost_plan[0][0]
                    temp_predict_cost = viable_route_cost_plan[0][1]
                    for i in range(len(viable_route_cost_plan)):
                        if viable_route_cost_plan[i][1] < temp_predict_cost:
                            temp_predict_route = viable_route_cost_plan[i][0]
                            temp_predict_cost = viable_route_cost_plan[i][1]
                    self.predict_route = temp_predict_route
                    self.predict_cost = temp_predict_cost
                    circle_flag = False
                    self.logger.debug(f'{self.env.time}: Agent cannot go for all')
                else:      # have not got viable result
                    TO_go_factories_num -= 1

            if TO_go_factories_num == 0:
                self.predict_cost = -1               # agent need to back right now!
                self.logger.debug(f'{self.env.time}: Agent need to back right now!')
                self.predict_route = [self.env.depot]
                return self.env.depot

        else:         # common work
            self.predict_route = route_cost_plan[0][0]
            self.predict_cost = route_cost_plan[0][1]
        
        
        self.logger.debug("current journey has been calculated!") 
        target = self.get_target()
        return target

    def get_route_and_cost(self, TO_go_factories):
        
        """
        this return route & cost
        """
        
        best_journey = np.array([])
        best_predict_total_cost = 0        # the min total cost in predictable future
        current_failure_number = 0
        last_one_back_depot_duration = 0
        direct_back_depot_duration = 0
        last_one_back_depot_flag = False
        direct_back_depot_flag = False

        current_failure_number = len(TO_go_factories)
        if current_failure_number != 0:
            """===============================实例化问题对象============================"""
            problem = GaCode(self.env, TO_go_factories)  # 生成问题对象
            """=================================种群设置==============================="""
            Encoding = 'P'  # 编码方式
            NIND = 200  # 种群规模
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

            failure_factories = TO_go_factories
            failure_factories = np.array(failure_factories)
            best_gen_matrix = var_trace[best_gen].astype(int)
            best_journey = failure_factories[best_gen_matrix]
            best_journey = np.array(best_journey)
            best_predict_total_cost = best_ObjV
            return best_journey, best_predict_total_cost

    def get_target(self):
        if self.predict_route[0].name == "Factory0":
            return self.env.factories[0]
        elif self.predict_route[0].name == "Factory1":
            return self.env.factories[1]
        elif self.predict_route[0].name == "Factory2":
            return self.env.factories[2]
        elif self.predict_route[0].name == "Factory3":
            return self.env.factories[3]
        elif self.predict_route[0].name == "Factory4":
            return self.env.factories[4]
        else:
            return self.env.depot


