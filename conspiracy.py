from weakref import ref
from random import shuffle

class Player:
    def __init__(self, name, id):
        self.name = name  # str
        self.id = id      # any hashable object
    
    def link_kappa(self, kappa):
        self.kappa = ref(kappa)
        kappa.target = ref(self)
    
    def eliminate(self):
        self.target().link_kappa(self.kappa())

class ConspiracyData:
    def __init__(self, players):
        self.players = {player.id: player for player in players}
        self.player_names = {player.name: player for player in players}
        self.eliminated = []
        players = list(players)  # not copy() cuz players could be immutable
        players.shuffle()
        for i in range(len(players))
            players[i-1].link_kappa(players[i])
