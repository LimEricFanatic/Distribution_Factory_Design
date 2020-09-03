import logging
import matplotlib.pyplot as plt

from Environment import Environment
from GetPlot import GetPlot


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
    fig = GetPlot(env)
    plt.figure()
    plt.ion()
    for i in range(env.PERIOD * 240):
        error = env.step()
        fig.run()
        if error:
            break
    fig.get_cdf()
    plt.ioff()
    plt.show()