from weakref import ref
from random import shuffle


class Player:
    def __init__(self, name, id):
        self.name = name  # str
        self.id = id  # any hashable object
        self.target = None  # no target or kappa indicates not currently playing
        self.kappa = None   # (temporary during initialization... or eliminated)

    def link_kappa(self, kappa):
        self.kappa = ref(kappa)
        kappa.target = ref(self)

    def eliminate(self):
        self.target().link_kappa(self.kappa())
        self.target = None
        self.kappa = None


class ConspiracyData:
    def __init__(self, players):
        players = [player if type(player) is Player else Player(*player) for player in players]  # haha best names ever
        self.players = {player.id: player for player in players}
        self.player_names = {player.name: player for player in players}
        self.playing = sorted(player_names.keys())
        self.eliminated = []
        shuffle(players)
        for i in range(len(players)):
            players[i - 1].link_kappa(players[i])
    
    def player(self, ident):  # ident can be an id or a name or a Player object; in any case a Player reference will be returned
        if type(ident) is Player:
            return ident
        elif ident in self.players: 
            return players[ident] 
        else:
            return player_names[ident]  # let this throw KeyError if necessary
    
    def _eliminate(self, player):
        self.playing.remove(player.name)
        self.eliminated.add(player.name)
        Player.eliminate(player)
    

class ConspiracyGame(ConspiracyData):
    def __init__(self, players, output):
        ConspiracyData.__init__(self, players)
        self.swapreq = set()
        self.output = output
        output.game_start(len(players))
        for player in players.values():
            output.kappa(player)
    
    def cap(self, capping, capped):
        capping = self.player(capping)
        capped = self.player(capped)
        if capping is capped.kappa():  # if the person capping X is the person who can cap X
            self.output.capped(capped)
            self.output.kappa_update(capped.target())
            self._eliminate(capped)
        else:
            self.output.failed(capping, capped)
            self.output.kappa_update(capping.target())
            self._eliminate(capping)
    
    def resign(self, player):
        player = self.player(player)
        self.output.resigned(player)
        self._eliminate(player)
    
    def kswap(self, player, target, direct = False):
        player = self.player(player)  # hmm this might be possible using advanced decorators
        target = self.player(target)
        if (target.id, player.id) in self.swapreq:
            self.swapreq.remove((target.id, player.id))
            self.output.kswap(player, target)
            self.output.kswap(target, player, response=True)
        elif direct:
            self.output.kswap(player, target)
        else:
            self.swapreq.add((player.id, target.id))
            self.output.kswap_proposal(player, target)

class basic_output:  # this entire class can be passed as an output object to ConspiracyGame
    def game_start(num):
        print("The game started with {} players!".format(num))
    
    def kappa(player):
        print("Player {p} can be capped by {k}.".format(p=player.name, k=player.kappa().name))
    
    def kappa_update(player):
        print("Player {p} can now be capped by {k}.".format(p=player.name, k=player.kappa().name))
    
    def capped(capped):
        print("Player {p} was capped by {k}!".format(p=capped.name, k=capped.kappa().name))
    
    def failed(capping, capped):
        print("Player {k} tried to cap {p} but failed!".format(k=capping.name, p=capped.name))
    
    def resigned(player):
        print("Player {p} has resigned.".format(p=player.name))
    
    def kswap(player, target, response=False):
        print(("In response, player" if response else "Player") + " {p} has told player {t} that {k} can cap them.".format(p=player.name, t=target.name, k=player.kappa().name))
    
    def kswap_proposal(player, target):
        print("Player {p} has proposed a kswap with {t}.".format(p=player.name, t=target.name))
    
    def game_end(ranks):
        print("The game has ended! The rankings are as follows:")
        for i, name in enumerate(ranks):
            print("{place:>3}: {name}".format(place=i, name=name))
