#import sys
#sys.path.insert(0,'Robots/MrIfOffline/')
#sys.path.insert(0,'Robots/MrIfOffline/MCTS')
#sys.path.insert(0,'Robots/MrIfOffline/ScenarioGenerator')
#sys.path.insert(0, 'Robots/MrSMG/')

from MrGreed import MrGreed
from MrIf import MrIf
from MrRandom import MrRandom
#from .MrSMG.MrSMG import MrSMG
#from MrZeroTreeSimple import MrZeroTreeSimple

robot_list = [MrGreed,MrIf,MrRandom]
robot_dict = dict([(rb.family_name(),rb) for rb in robot_list])
