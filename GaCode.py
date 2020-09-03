import geatpy as ea
import numpy as np
import math


class GaCode(ea.Problem):
    def __init__(self, env, TO_go_factories):
        self.env = env
        self.TO_go_factories = TO_go_factories
        name = 'Maintenance scheduling of geographically distributed assets with prognostics information'
        M = 1
        max_or_min = [1] * M
        Dim = len(self.TO_go_factories)
        varTypes = [0] * Dim
        lb = [0] * Dim
        ub = [Dim - 1] * Dim
        l_bin = [1] * Dim
        u_bin = [1] * Dim
        ea.Problem.__init__(self, name, M, max_or_min, Dim, varTypes, lb, ub, l_bin, u_bin)

    def aimFunc(self, pop):
        decision_matrix = pop.Phen.copy()
        ObjV = []
        for i in range(pop.sizes):
            failure_factories = np.array(self.TO_go_factories)
            decision_matrix = decision_matrix.astype(int)
            now_decision_line = decision_matrix[i, :]
            journey = failure_factories[now_decision_line]
            predict_total_cost = self.get_predict_total_cost(journey)
            ObjV.append(predict_total_cost)
        pop.ObjV = np.array([ObjV]).T

    def get_predict_total_cost(self, predict_journey):
        current_cost = self.env.total_cost
        current_time = self.env.time
        current_day_working_duration = self.env.agent.day_working_duration
        current_std_working_duration = self.env.agent.std_working_duration
        current_max_working_duration = self.env.agent.max_working_duration

        current_max_downtime_duration = []
        for factory in predict_journey:
            current_max_downtime_duration.append(factory.downtime_duration)

        # velocity part
        predict_velocity = self.env.agent.velocity

        # distance part
        now_position = self.env.agent.position
        predict_distance = []
        for i in range(self.Dim):
            next_target_position = predict_journey[i].position
            target_vector = next_target_position - now_position
            target_distance = abs(target_vector)
            predict_distance.append(target_distance)
            now_position = next_target_position
        back_to_depot_vector = now_position - self.env.depot.position  # Finish -> Depot
        back_to_depot_dis = abs(back_to_depot_vector)
        predict_distance.append(back_to_depot_dis)

        # time part
        predict_arrive_time = []
        predict_leave_time = []
        predict_arrive_duration = []  # the duration spend to arrive
        predict_downtime_duration = []
        predict_maintenance_duration = []
        unplaned_factories = []    
        predict_travel_duration = 0  # duration spend in pure travel
        predict_day_std_working_duration = 0
        predict_day_overworking_duration = 0
        now_travel_duration = 0



        for i in range(len(predict_distance)):
            now_travel_duration = predict_distance[i] / predict_velocity
            predict_travel_duration += now_travel_duration
            if i == 0:
                now_arrive_time = current_time + now_travel_duration
                predict_arrive_time.append(now_arrive_time)
            else:
                now_arrive_time = predict_leave_time[i-1] + now_travel_duration
                predict_arrive_time.append(now_arrive_time)
            if i != (len(predict_distance) - 1):
                now_factory = predict_journey[i]
                next_leave_time = predict_arrive_time[i] + now_factory.repair_duration
                predict_leave_time.append(next_leave_time)
            else:     #arrive depot
                next_leave_time = predict_arrive_time[i]
                predict_leave_time.append(next_leave_time)
        predict_arrive_duration[:] = [x - current_time for x in predict_arrive_time]
        
        factory_temp_index = 0
        for factory in predict_journey:
            if factory.state == factory.State.GOOD:
                factory.state_transition_time = current_time + factory.downtime_duration    #prob failure
            if factory.state_transition_time > predict_arrive_time[factory_temp_index]:    # arrive before transition
                predict_downtime_duration.append((predict_arrive_time[factory_temp_index] - current_time))
                predict_maintenance_duration.append(0)
            else:    # arrive after transition
                if current_time < factory.state_transition_time:   # factory downing
                    predict_downtime_duration.append(factory.state_transition_time - current_time)
                    predict_maintenance_duration.append(
                        (predict_arrive_time[factory_temp_index] - factory.state_transition_time))
                else:  #factory maintaining
                    predict_downtime_duration.append(0)
                    predict_maintenance_duration.append(
                        predict_arrive_time[factory_temp_index] - current_time)
            factory_temp_index += 1
        factory_temp_index = 0
        predict_plan_duration = predict_leave_time[-1] - current_time

        predict_day_working_duration = current_day_working_duration + predict_plan_duration
        if predict_day_working_duration > current_max_working_duration:    #reach upper limit
            return 999999999.0
        elif predict_day_working_duration > current_std_working_duration:  # overtime work
            if current_day_working_duration < current_std_working_duration:
                predict_day_overworking_duration = predict_day_working_duration - current_std_working_duration
            else:
                predict_day_overworking_duration= predict_day_working_duration - current_day_working_duration
        
        # unplaned factories
        unplaned_factories = []
        planed_factory_name = []
        for factory in predict_journey:
            planed_factory_name.append(factory.name)
        if (len(self.env.get_failure_factories_information()) != 0):
            for factory in self.env.get_failure_factories_information():
                if factory.name not in planed_factory_name:
                    unplaned_factories.append(factory)
        else:
            for factory in self.env.get_prob_failure_factories_information():
                if factory.name not in planed_factory_name:
                    unplaned_factories.append(factory)

        # cost part
        # factory cost part
        predict_failure_cost = 0
        predict_downtime_duration_cost = 0
        predict_maintenance_cost = 0
        # agent cost part
        predict_overtime_cost = 0
        predict_travel_cost = 0
        predict_overtime_cost = predict_day_overworking_duration * self.env.agent.overtime_cost
        predict_travel_cost = predict_travel_duration * self.env.agent.travel_cost * self.env.agent.velocity        
        
        # planed factories cost part
        planed_predict_downtime_duration_cost = 0
        planed_predict_maintenance_cost = 0 
        planed_predict_failure_cost = 0

        for factory in predict_journey:
            if factory.pre_repair_flag == True:
                planed_predict_failure_cost += factory.pre_repair_cost
            else:
                planed_predict_failure_cost += factory.failure_cost
        
        factory_temp_index = 0 
        for factory in predict_journey:
            planed_predict_downtime_duration_cost += (factory.downtime_duration_cost * \
                (predict_downtime_duration[factory_temp_index]) * factory.cdf)
            factory_temp_index += 1

        factory_temp_index = 0
        for factory in predict_journey:
            planed_predict_maintenance_cost += (factory.maintenance_cost * \
                predict_maintenance_duration[factory_temp_index] * factory.maintenance_punishment_factor * factory.cdf)
            factory_temp_index += 1
        
        # unplaned fatories cost part                      failure!!! 跨两天发生transition不行
        unplaned_predict_downtime_duration_cost = 0
        unplaned_predict_maintenance_cost = 0
        unplaned_predict_failure_cost = 0

        for factory in unplaned_factories:
            if factory.pre_repair_flag == True:
                unplaned_predict_failure_cost += factory.pre_repair_cost              #?????咋整
            else:
                unplaned_predict_failure_cost += factory.failure_cost
        
        for factory in unplaned_factories:
            if factory.state_transition_time <= self.env.time:
                unplaned_predict_maintenance_cost += ((24 - current_day_working_duration) * factory.maintenance_punishment_factor * \
                    factory.maintenance_cost * factory.cdf)
            else:
                unplaned_predict_downtime_duration_cost += ((factory.state_transition_time - self.env.time) * factory.downtime_duration_cost * factory.cdf)
                unplaned_predict_maintenance_cost += ((24 - (factory.state_transition_time % 24)) * factory.maintenance_cost * factory.cdf)

        predict_failure_cost = planed_predict_failure_cost + unplaned_predict_failure_cost 
        predict_maintenance_cost = planed_predict_maintenance_cost + unplaned_predict_maintenance_cost
        predict_downtime_duration_cost = planed_predict_downtime_duration_cost + unplaned_predict_downtime_duration_cost

        predict_total_cost = current_cost + predict_failure_cost + predict_downtime_duration_cost + predict_maintenance_cost\
             + predict_travel_cost + predict_overtime_cost

        return predict_total_cost
