
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Utils import log
import random
from Robot import Robot

class MrRandom(Robot):
    """ONLY for 4 players"""
    def __init__(self,room=0,place=0,name="default",create_room = False):
        super(MrRandom,self).__init__(room,place,name,create_room)
        self.place = place
        self.cards_list = [] #cards in hand
        self.history = [] #list of (int,str,str,str,str)
        self.cards_on_table = [] #[int,str,...]
        self.score_cards = [[],[],[],[]]

        #useless infos
        self.initial_cards = [] #cards initial
        self.room = room
        self.name = name
        self.players_information = [None, None, None, None]

    def decide_suit(self):
        if len(self.cards_on_table)==1:
            suit="A"
        else:
            suit=self.cards_on_table[1][0]
        return suit

    def gen_cards_dict(self):
        cards_dict={"S":[],"H":[],"D":[],"C":[]}
        for i in self.cards_list:
            cards_dict[i[0]].append(i)
        return cards_dict

    def pick_a_card(self):
        assert (self.cards_on_table[0]+len(self.cards_on_table)-1)%4==self.place,"self.place and self.cards_on_table contrdict"
        suit=self.decide_suit()
        cards_dict=self.gen_cards_dict()
        if cards_dict.get(suit)==None or len(cards_dict[suit])==0:
            i=random.randint(0,len(self.cards_list)-1)
            choice=self.cards_list[i]
        else:
            i=random.randint(0,len(cards_dict[suit])-1)
            choice=cards_dict[suit][i]
        return choice

    @staticmethod
    def family_name():
        return 'Miss.random'

class Human(MrRandom):
    def pick_a_card(self,suit=None):
        suit=self.decide_suit()
        log("%s, %s, %s, %s"%(self.name,suit,self.cards_on_table,self.cards_list))
        while True:
            choice=input("your turn: ")
            if choice in self.cards_list:
                break
            else:
                log("%s is not your cards. "%(choice),end="")
        return choice

    @staticmethod
    def family_name():
        return 'Human'

if __name__=="__main__":
    log("",l=2)
