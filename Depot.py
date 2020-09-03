import math
import logging
import random
from enum import Enum

from utils import Point2D
from Asset import Asset


class Depot(Asset):
    def __init__(self, env, position, name):    
        self.name = name        
        super().__init__(env, position, self.name)
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)