from Utils import log
import time,random

class Robot:
    def __init__(self,room,place,name,create_room = False):
        self.place = place
        self.room = room
        self.name = name
        self.players_information = [None, None, None, None]
        self.cards_list = []
        self.initial_cards = []
        self.history = []
        self.cards_on_table = []
        self.game_mode = 4
        self.scores = [[],[],[],[]]

        #things should not realize by Robot class
        self.scores_num = [0,0,0,0]
        self.state = 'logout'
        self.creator = create_room
        self.master = 'MrComputer'

        #things I even do not know what it is
        self.res = []

    def pick_a_card(self):
        self.mycards = {"S": [], "H": [], "D": [], "C": [], "J": []}
        for i in self.cards_list:
            self.mycards[i[0]].append(i[1:])

        suit = 'A' if len(self.cards_on_table) == 1 else self.cards_on_table[1][0]

        while True:
            if suit == 'H':
                if suit not in self.mycards:
                    if 'J' not in self.mycards:
                        suit = random.choice(list(self.mycards.keys()))
                    else:
                        suit = 'J'
            elif suit == 'J':
                if suit not in self.mycards:
                    if 'H' not in self.mycards:
                        suit = random.choice(list(self.mycards.keys()))
                    else:
                        suit = 'H'

            else:
                if suit not in self.mycards:
                    suit = random.choice(list(self.mycards.keys()))

            if len(self.mycards[suit]) == 0:
                self.mycards.pop(suit)
                continue
            else:
                break

        i = random.randint(0, len(self.mycards[suit]) - 1)

        print("{} plays {}".format(self.name,suit + self.mycards[suit][i]))

        return suit + self.mycards[suit][i]

    def __str__(self):
        return 'name:{} state:{}'.format(self.name,self.state)

    def shuffle(self):
        pass

    def update(self):
        pass

    def trickend(self):
        pass

    def gameend(self):
        # self.players_information looks like [['Sun', True, False], ['Miss.if0', True, True], ['Miss.if1', True, True], ['Miss.if2', True, True]]
        self.res.append(self.scores_num[self.place])
        should_record = True
        for i in range(self.place):
            if self.players_information[i][2]:
                should_record = False
                break
        if should_record:
            log("I, %s, should record."%(self.name))
            s = "\n".join([", ".join([str(i) for i in trick]) for trick in self.history])
            s += '\nresult: %s\n\n'%(", ".join([str(n) for n in self.scores_num]))
            fname = [pl[0] for pl in self.players_information]
            fname = "Records/" + "_".join(fname) + ".txt"
            log("writing to %s:\n%s"%(fname,s))
            with open(fname, 'a') as f:
                f.write(s)

    @staticmethod
    def family_name():
        return 'Coucou'
