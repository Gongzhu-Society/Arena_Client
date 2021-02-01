#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sys
# Import your robots
sys.path.insert(0,'..')
#from MrRandTree import MrRandTree
from MrZeroTree import MrZeroTree

robot_list = [MrZeroTree,]
robot_dict = dict([(rb.family_name(),rb) for rb in robot_list])

import time,traceback,math,json,copy
LOGLEVEL={0:"DEBUG",1:"INFO",2:"WARN",3:"ERR",4:"FATAL"}
LOGFILE=sys.argv[0].split(".")
LOGFILE[-1]="log"
LOGFILE=".".join(LOGFILE)
def log(msg,l=1,end="\n",logfile=None,fileonly=False):
    st=traceback.extract_stack()[-2]
    lstr=LOGLEVEL[l]
    now_str="%s %03d"%(time.strftime("%y/%m/%d %H:%M:%S",time.localtime()),math.modf(time.time())[0]*1000)
    if l<3:
        tempstr="%s [%s,%s:%d] %s%s"%(now_str,lstr,st.name,st.lineno,str(msg),end)
    else:
        tempstr="%s [%s,%s:%d] %s:\n%s%s"%(now_str,lstr,st.name,st.lineno,str(msg),traceback.format_exc(limit=5),end)
    if not fileonly:
        print(tempstr,end="")
    if l>=1 or fileonly:
        if logfile==None:
            logfile=LOGFILE
        with open(logfile,"a") as f:
            f.write(tempstr)

import socketio
import numpy as np

Recording_History = True

class RobotFamily:
    def __init__(self,url):
        self.members = []
        self.sio = socketio.Client()
        self.url = url

        pt = self
        self.a = 0
        self.turn = 0

        @self.sio.event
        def connect():
            log("connecting to server %s" % (pt.url))
            self.sendmsg('update_sid',{'user':''})
            if self.turn == 10000: #?
                for pl in self.members:
                    resnp = np.array(pl.res) #?
                    print('{} mean:{} var:{}'.format(pl.name,resnp.mean(),math.sqrt(resnp.var())))
                self.sio.disconnect()
                return
            for rb in self.members:
                self.sendmsg('request_info',{'user':rb.name})
            pt.a = time.time()

        @self.sio.event
        def disconnect():
            self.turn += 1 #? sometimes self sometimes pt?
            log("disconnect from server %s" % (pt.url))

        @self.sio.on('login_reply')
        def login_reply(data):
            pt.loginreply(data)

        @self.sio.on('create_room_reply')
        def create_room_reply(data):
            pt.createroomreply(data)

        @self.sio.on('enter_room_reply')
        def enter_room_reply(data):
            pt.enterroomreply(data)

        @self.sio.on('ready_for_start_reply')
        def ready_for_start_reply(data):
            pt.readyforstartreply(data)

        @self.sio.on('player_info')
        def player_info(data):
            pt.playerinfo(data)

        @self.sio.on('shuffle')
        def shuffle(data):
            pt.shuffle(data)

        @self.sio.on('update')
        def update(data):
            pt.update(data)

        @self.sio.on('your_turn')
        def your_turn(data):
            pt.yourturn(data)

        @self.sio.on('my_choice_reply')
        def my_choice_reply(data):
            pt.mychoicereply(data)

        @self.sio.on('logout_reply')
        def logout_reply(data):
            pt.logoutreply(data)

        @self.sio.on('trick_end')
        def trickend(data):
            pt.trickend(data)

        @self.sio.on('game_end')
        def game_end(data):
            pt.gameend(data)

        @self.sio.on('new_game_reply')
        def newgamereply(data):
            pt.newgamereply(data)

        @self.sio.on('choose_place_reply')
        def choose_place_reply(data):
            pt.chooseplacereply(data)

        @self.sio.on('request_info_reply')
        def request_info_reply(data):
            pt.recovery(data)

        @self.sio.on('error')
        def error(data):
            pt.error(data)

        @self.sio.on('add_robot')
        def add_robot(data):
            pt.addrobot(data)

        @self.sio.on('cancel_player')
        def cancel(data):
            print('cancel this robot')
            data = self.strip_data(data)
            name = data['user']
            self.cancel_player(name)

    def recovery(self,data): #?
        data = self.strip_data(data)
        if isinstance(data, int): #?
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        player.state = data['state']

        if player.state == 'logout':
            #self.cancel_player(player.name)
            return
        if player.state == 'login':
            if player.room > 0:
                self.sendmsg('enter_room',{'user':player.name,'room':player.room})
            else:
                pass
                #self.cancel_player(player.name)
            return
        if player.state == 'room':
            if player.room > 0:
                self.sendmsg('choose_place', {'user': player.name, 'room': player.room, 'place': player.place})
            else:
                #self.cancel_player(player.name)
                pass
            return

        player.room = data['room']
        player.place = data['place']
        player.players_information = copy.deepcopy(data['players'])
        if player.state == 'wait':
            self.sendmsg('ready_for_start', {'user': player.name})
            return

        player.cards_list = copy.deepcopy(data['cards_remain'])
        player.cards_on_table = []
        player.cards_on_table.append(data['trick_start'])
        player.cards_on_table.extend(data['this_trick'])
        player.history = copy.deepcopy(data['history'])
        player.initial_cards = copy.deepcopy(data['initial_cards'])

        if player.state == 'end':
            player.scores = copy.deepcopy(data['scores'])
            player.scores_num = copy.copy(data['scores_num'])
            player.gameend()
            self.sendmsg('new_game',{'user':player.name})
            return
        if player.state == 'play_a_card':
            card = player.pick_a_card()
            print('sending choice')
            time.sleep(2)
            self.sendmsg('my_choice', {'user': player.name, 'card': card})
            return

    def connect(self):
        self.sio.connect(self.url)

    def sendmsg(self, cmd, dict):
        log("sending %s: %s to server" % (cmd, dict))
        for retry_num in range(2):  # default not retry
            try:
                self.sio.emit(cmd, json.dumps(dict))
                break
            except:
                log("unknown error, retry_num: %d" % (retry_num), l=3)
        else:
            log("send failed", l=2)
            return 2
        return 0

    def strip_data(self,data):
        try:
            data = json.loads(data)
        except:
            log("parse data error: %s" % (data), l=2)
            self.sendmsg('error', {'detail': 'json.load(data) error'})
            return 1
        try:
            assert 'user' in data
        except:
            log('data lack element: %s' % (data), l=2)
            self.sendmsg('error', {'detail': 'data lack element'})
            return 2
        return data

    def make_a_name(self,robot):
        ap = 0
        Flag = True
        name = ''
        while (Flag):
            Flag = False
            name = robot.family_name() + str(ap)
            for rb in self.members:
                if name == rb.name:
                    ap += 1
                    Flag = True
                    break
        return name

    def add_member(self, room, place, robot, master = 'MrLi'):
        name = self.make_a_name(robot)
        rb = robot(room, place, name)
        rb.master = master
        self.members.append(rb)
        #'login': {"user": "name", "user_pwd": "pwd", "room": roomid}
        #TODO:place, robot password #?
        self.sendmsg('login',{"user":name,"user_pwd":-1,"is_robot":True,"robot_type":robot.family_name()})
        return name

    def find_player(self,name):
        for rb in self.members:
            if rb.name == name:
                return rb
        return None

    def loginreply(self,data):
        data = self.strip_data(data)
        if isinstance(data,int):
            print('data error')
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error',{'detail':"no such player"})
            return
        if not player.state == 'logout':

            return
        player.state = 'login'
        if not player.creator:
            self.sendmsg('enter_room',{'user':player.name,'room':player.room})
        else:
            self.sendmsg('create_room', {'user': player.name, 'room':'Q'})
        #player.players_information = copy.deepcopy(data["players"])

    def createroomreply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return
        if not player.state == 'login':
            return

        player.state = 'wait'
        player.room = data['room_id']
        player.place = 0
        player.players_information = copy.deepcopy(data["players"])
        self.sendmsg('ready_for_start', {'user': player.name})

    def enterroomreply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return
        if not player.state == 'login':
            return

        player.state = 'room'
        self.sendmsg('choose_place', {'user':player.name,'room':player.room,'place':player.place,'master':player.master})

    def chooseplacereply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'user':player.name,'detail': "no such player"})
            return
        if not player.state == 'room':
            return

        if not data['success']:
            self.sendmsg('error',{'user':player.name,'detail':'robot can\'t sit down'})
            return

        player.state = 'wait'
        self.sendmsg('ready_for_start',{'user':player.name})

    def readyforstartreply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return
        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'user': player.name, 'detail': "no such player"})
            return
        if not player.state == 'wait':
            return

        player.state = 'before_start'

    def playerinfo(self,data):
        data = self.strip_data(data)
        if isinstance(data,int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return
        player.players_information = copy.deepcopy(data["players"])

    def shuffle(self,data):
        #print('processin shuffle')
        data = self.strip_data(data)
        if isinstance(data, int):
            return
        player = self.find_player(data['user'])

        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'before_start':
            return

        player.history = []
        player.cards_on_table = []

        player.initial_cards = copy.deepcopy(data["cards"])
        player.cards_list = copy.deepcopy(data["cards"])
        player.state = 'trick_before_play'
        player.shuffle()

    def update(self,data):
        #print('processing update')
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        cards_on_table = copy.deepcopy(data['this_trick'])
        start = data['trick_start']

        player.cards_on_table = []
        player.cards_on_table.append(start)
        player.cards_on_table.extend(cards_on_table)
        player.update()

    def yourturn(self,data):
        #print('processing youturn')
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'trick_before_play':
            print(player.state)
            return
        player.state = 'play_a_card'

        start_time = time.time()
        card = player.pick_a_card()
        end_time = time.time()
        all_time = float(end_time) - float(start_time)

        try:
            if all_time<1 and not player.train:
                time.sleep(1-all_time)
        except:
            if all_time<1:
                time.sleep(1-all_time)
        #print('sending choice')
        self.sendmsg('my_choice', {'user': player.name, 'card':card})

    def mychoicereply(self,data):
        #print('enter reply')
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'play_a_card':
            return

        tmp = len(player.cards_list)
        player.cards_list= copy.deepcopy(data['your_remain'])
        if not tmp == len(player.cards_list):
            player.state = 'trick_after_play'
            #self.sendmsg('error', {'user': player.name, 'detail': 'just test'})
            #('recevive choice reply')
        else:
            card = player.pick_a_card()
            self.sendmsg('my_choice', {'user': player.name, 'card': card})


    def logoutreply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        index = 0
        for i,mem in enumerate(self.members):
            if mem.name == data['user']:
                index = i
                break

        self.members.pop(index)

    def trickend(self,data):
        #print('receive trick end')
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'trick_after_play':
            return

        if player.place == 0:
            print()

        player.scores = copy.deepcopy(data['scores'])
        player.history.append(player.cards_on_table)
        player.cards_on_table = []
        player.state = 'trick_before_play'
        player.trickend()

    def gameend(self,data):
        #print('receive game end')
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'trick_before_play':
            return

        player.scores = copy.deepcopy(data['scores'])
        player.scores_num = data['scores_num']
        player.gameend()

        player.state = 'end'

        #print('send new game')
        self.sendmsg('new_game',{'user':data['user']})

        #time.sleep(1)
        #self.cancel_player(player.name)

    def newgamereply(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        player = self.find_player(data['user'])
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return

        if not player.state == 'end':
            return

        player.state = 'wait'
        self.sendmsg('ready_for_start',{'user':player.name})

    def error(self,data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        if 'user' in data:
            player = self.find_player(data['user'])
            if not player:
                self.sendmsg('error', {'detail': "no such player"})
                return

            log('%s:%s'%(data['user'],data['detail']),l = 1)

        else:
            log(data['detail'],l = 1)

    def cancel_player(self,name):
        player = self.find_player(name)
        if not player:
            self.sendmsg('error', {'detail': "no such player"})
            return
        print('bonne journee1')
        print(player.state)
        if not player.state == 'before_start':
            return
        print('bonne journee2')
        print(player.state)
        self.sendmsg('logout',{'user':name})

    def addrobot(self, data):
        data = self.strip_data(data)
        if isinstance(data, int):
            return

        rb_name = data['robot']
        room = data['room']
        place = data['place']
        rb = robot_dict[rb_name]

        self.add_member(room,place,rb,master=data['master'])

    def close_family(self):
        if len(self.members) == 0:
            self.sio.disconnect()
        print("disconnect from server")

    def create_room(self,robot):
        name = self.make_a_name(robot)
        self.members.append(robot(0, 0, name,True))
        # 'login': {"user": "name", "user_pwd": "pwd", "room": roomid}
        # TODO:place, robot password
        self.sendmsg('login', {"user": name, "user_pwd": -1})


if __name__=="__main__":
    from ast import literal_eval
    with open("config.py",'r') as f:
        config=literal_eval(f.read())
        log("read log from %s: %s"%(f.name,config))
    log("You are using socketio %s"%(socketio.__version__))
    fm = RobotFamily('http://%s:%d'%(config["ip"],config["port"]))
    try:
        fm.connect()
    except:
        log("",l=3)