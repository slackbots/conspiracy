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
        self.playing = sorted(self.player_names.keys())
        self.eliminated = []
        shuffle(players)
        for i in range(len(players)):
            players[i - 1].link_kappa(players[i])

    def player(self, ident):  # ident can be an id or a name or a Player object; in any case a Player reference will be returned
        if type(ident) is Player:
            return ident
        elif ident in self.players:
            return self.players[ident]
        else:
            return self.player_names[ident]  # let this throw KeyError if necessary

    def _eliminate(self, player):
        self.playing.remove(player.name)
        self.eliminated.add(player.name)
        Player.eliminate(player)


class ConspiracyGame(ConspiracyData):
    def __init__(self, players):
        ConspiracyData.__init__(self, players)
        self.swapreq = set()

    def cap(self, capping, capped):
        capping = self.player(capping)
        capped = self.player(capped)
        if capping is capped.kappa():  # if the person capping X is the person who can cap X
            self.inform_kappa_update(capped.target())
            self.inform_capped(capping, capped)
            self._eliminate(capped)
        else:
            self.inform_kappa_update(capping.target())
            self.inform_failed(capping, capped)
            self._eliminate(capping)

    def resign(self, player):
        player = self.player(player)
        self.inform_resigned(player)
        self._eliminate(player)

    def kswap(self, player, target, direct=False):
        player = self.player(player)  # hmm this might be possible using advanced decorators
        target = self.player(target)
        if (target.id, player.id) in self.swapreq:
            self.swapreq.remove((target.id, player.id))
            self.inform_kswap(player, target)
            self.inform_kswap(target, player, response=True)
        elif direct:
            self.inform_kswap(player, target)
        else:
            self.swapreq.add((player.id, target.id))
            self.inform_kswap_proposal(player, target)
