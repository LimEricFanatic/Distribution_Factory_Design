import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms

from Factory import Factory

class GetPlot:
    def __init__(self, env):
        self.env = env

    def run(self):
        plt.cla()
        self.get_map()
        self.get_date()
        plt.pause(0.05)


    def get_map(self):
        # 绘制上方动态图像
        plt.subplot(2,2,1)

        # 设定标题等
        plt.title("MAP")
        plt.grid(True)

        #agent
        agent_x = self.env.agent.position.x
        agent_y = self.env.agent.position.y

        # 设置X轴
        plt.xlabel("X轴")
        plt.xlim(-10, 10)
        plt.xticks(np.linspace(-10, 10, 9, endpoint=True))

        # 设置Y轴
        plt.ylabel("Y轴")
        plt.ylim(-10, 10)
        plt.yticks(np.linspace(-10, 10, 9, endpoint=True))

        # Agent Position
        plt.scatter(agent_x, agent_y, s=36, c='blue', marker="P")
        plt.text(agent_x+0.1, agent_y+0.1, 'Agent', horizontalalignment='left',
            verticalalignment='bottom')
        
        # Arrow Part
        now_position_x = agent_x
        now_position_y = agent_y
        next_position_x = agent_x
        next_position_y = agent_y
        for factory in self.env.agent.predict_route:
            next_position_x = factory.position.x
            next_position_y = factory.position.y
            self.plt_arrow(now_position_x, now_position_y, next_position_x ,next_position_y)
            now_position_x = next_position_x
            now_position_y = next_position_y
        if (next_position_x != self.env.depot.position.x) and (next_position_y != self.env.depot.position.y):
            next_position_x = self.env.depot.position.x
            next_position_y = self.env.depot.position.y
            self.plt_arrow(now_position_x, now_position_y, next_position_x ,next_position_y)
        
        # Factories Position & Situation
        factories_x_index = 0
        factories_y_index = 0 
        for factory in self.env.factories:
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
            plt.text(factories_x_index, factories_y_index+0.7, f'{factory.name}',
                size = 10, alpha = 0.5, horizontalalignment='center',verticalalignment='center')
            plt.text(factories_x_index, factories_y_index-0.7, f'{factory.state}',
                size = 10, alpha = 0.5, horizontalalignment='center',verticalalignment='center',)
    def get_date(self):

        plt.text(15, 10, f'DAY {int(self.env.time // 24) + 1}        TIME: {(self.env.time % 24):8.2f}', ha='left', va='center')                                               # time
        plt.text(15, 8, f'TOTAL COST: {self.env.total_cost:8.2f}', ha='left', va='center')                                    # total cost
        plt.text(15, 6, f'Day Working Duration: {self.env.agent.day_working_duration:8.2f}         (MAX is {self.env.agent.max_working_duration})', ha='left', va='center')               
        plt.text(15, 4, f'Agent position: ({self.env.agent.position.x:8.1f},{self.env.agent.position.y:8.1f})' )
        plt.text(15, 2, f'Predict journey: {self.env.agent.predict_route}', ha='left', va='center')                           # working plan
        if self.env.agent.predict_cost != -1:                                                                                 # working plan cost
            plt.text(15,0, f'Predict cost: {self.env.agent.predict_cost:8.2f}', ha='left', va='center')
        else:
            plt.text(15,0, f'Predict cost: Agent need rest, cannot work', ha='left', va='center')
        i = 0
        for factory in self.env.factories:
            i = i - 2
            plt.text(15, i, f'{factory.name} failure cdf: {factory.cdf:8.5}')
            plt.text(25, i, f'repair times:{factory.repair_times}')
        i = i - 2
        plt.text(15, i, f'MODE: {self.env.MODE}')

    def get_cdf(self):

        plt.subplot(2,1,2)
        color_list = ['red', 'black', 'blue', 'purple', 'green']
        i = 0
        for factory in self.env.factories:
            plt.yscale('log')
            plt.plot(self.env.t_list, factory.cdf_list, c=color_list[i])
            i += 1
    
    def plt_arrow(self,x_begin,y_begin,x_end,y_end):
        plt.arrow(x_begin, y_begin, x_end - x_begin, y_end - y_begin,
             length_includes_head=True,     # 增加的长度包含箭头部分
             head_width = 0.3, head_length =0.3, fc="black", ec="black",linestyle='--',linewidth=0.5)
    