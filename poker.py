'''Cards 2.8.2
A Texas Hold'em poker game implementation in Python.
This module provides the core game engine, including card handling, player management,
betting rounds, and pot management.

created 'position' variable.  
'''
__author__='philip'

import random
import pokerhands  # Hand evaluation module
from operator import attrgetter
import time
import pokerstrat  # Player strategy module
import wcjunkins  # Import your custom strategy module

# Card class represents a single playing card
class Card:
    # Card ranks from lowest to highest
    RANKS=['2','3','4','5','6','7','8','9','10','J', 'Q', 'K', 'A']
    # Card suits: hearts, clubs, spades, diamonds
    SUITS=['h', 'c', 's', 'd']

    def __init__(self,rank, suit, faceup=True):
        """Initialize a card with rank, suit, and faceup status"""
        self.rank=rank
        self.suit=suit
        self.values=[]
        self.__value=(Card.RANKS.index(self.rank)+1)  # Numeric value of the card
        self.faceup=faceup  # Whether the card is face up or down

    def __str__(self):
        """String representation of the card"""
        if self.faceup:
            return str(self.rank)+str(self.suit)
        else:
            return 'XX'  # Hidden card representation

    @property
    def value(self):
        """Get the numeric value of the card"""
        v=self.__value
        return v

# Hand class represents a player's hand and player attributes
class Hand:
    serial=0  # Counter for player positions

    def __init__(self, name, table, strategy='Random'):
        """Initialize a player with name, table, and strategy"""
        self.strategy=[]  # List of strategy objects
        self.stratname=strategy  # Name of the strategy
        try:
            strategy_class=getattr(pokerstrat, strategy)  # Try to get strategy from pokerstrat
        except AttributeError:
            try:
                strategy_class=getattr(wcjunkins, strategy)  # Try to get strategy from wcjunkins
            except AttributeError:
                raise ValueError(f"Strategy '{strategy}' not found in pokerstrat or wcjunkins modules")
        strat=strategy_class(self)  # Create strategy instance
        self.strategy.append(strat)
               
        self.cards=[]  # Player's hole cards
        self.total_cards=(self.cards+table.cards)  # All cards (hole + community)
        table.players.append(self)  # Add player to table
        self.name=name
        
        Hand.serial+=1
        self.position=Hand.serial  # Player position at table
        self.small_blind=False  # Small blind status
        self.big_blind=False  # Big blind status
        self.dealer=False  # Dealer status
        self.hand_value=0  # Current hand strength
        self.rep=''  # Hand representation
        self.tie_break=0  # For breaking ties
        self.raw_data=0  # Raw hand data
        self.is_folded=False  # Fold status
        self.stack=1000  # Player's chip stack
        
        self.stake=0  # Current bet amount
        self.in_pot=0  # Total in pot
        self.to_play=0  # Amount to call
        self.all_in=False  # All-in status
        self.first_all_in=False  # First all-in flag
        self.raised=0  # Number of raises
        self.carry_over=0  # Carry over amount for side pots

        # Statistics tracking
        self.history=[]
        self.pots_played=0
        self.win=0
        self.raises=0
        self.calls=0
        self.checks=0

    @property
    def play_analysis(self):
        """Analyze player's play style"""
        pass

    @property
    def get_position(self):
        """Get player's position relative to pot"""
        return self.position%pot.table_size
    
    def __str__(self):
        """String representation of player"""
        rep='\n'+str(self.name)+'\t    stack='+str(self.stack)+'\n'
        
        if self.small_blind:
            rep+=' small blind'
        elif self.big_blind:
            rep+=' big blind'
        elif self.dealer:
            rep+=' dealer'
        
        return rep
   
    def get_value(self):
        """Evaluate the strength of the player's hand"""
        self.total_cards=(self.cards+table.cards)
        rep, hand_value, tie_break, raw_data=pokerhands.evaluate_hand(self.total_cards)
        
        self.rep=str(rep)
        self.hand_value=hand_value
        self.tie_break=tie_break
        self.raw_data=raw_data
        
        return hand_value, rep, tie_break, raw_data

    def print_cards(self):
        """Print the player's cards"""
        rep=''
        if self.is_folded:
            rep='FF'
        else:
            for card in self.cards:
                rep+=str(card)+'  '
        print (rep)
        
    def flip(self):
        """Flip all cards face up/down"""
        for card in self.cards: card.faceup=not card.faceup

    def fold(self, pot):
        """Fold the player's hand"""
        self.is_folded=True
        self.in_pot=0
        self.stake=0
        self.raised=0
        
        print (str(self.name)+' folds')
        pot.folded_players.append(self)
        if self in pot.active_players:
            pot.active_players.remove(self)
                
        if pot.one_remaining:
            pot.stage=5

    def no_play(self, pot):
        """Skip player's turn"""
        next_player(pot)
        self.stake=0
    	
    def check_call(self, pot):
        """Check or call the current bet"""
        if self.to_play==0:
            print (str(self.name)+' checks')
        else:
            if self.to_play>self.stack:
                self.stake=self.stack
            else:
                self.stake=self.to_play
            print (str(self.name)+' calls '+str(self.stake))
            if pot.stage==0 and pot.raised==False:
                pot.limpers+=1
        next_player(pot)
    
    def bet(self, pot, stake):
        """Place a bet or raise"""
        if pot.already_bet:
            print (str(self.name)+' raises '+str(stake-self.to_play))
            self.raised+=1
            pot.limpers=0
            pot.raised=True
        else:
            print (str(self.name)+' bets '+str(stake))
            pot.already_bet=True
      
        self.stake=stake
        pots[-1].to_play+=(self.stake-self.to_play)
        next_player(pot, True)
        
    def ante(self, pot):
        """Post blinds"""
        if self.small_blind:
            self.stack-=BLINDS[0]
            pot.total+=BLINDS[0]
            self.in_pot+=BLINDS[0]
            
        if self.big_blind:
            self.stack-=BLINDS[1]
            pot.total+=BLINDS[1]
            pot.to_play=BLINDS[1]
            self.in_pot+=BLINDS[1]
        
    def bust(self):
        """Handle player busting"""
        print (str(self.name)+' is bust')
        list_index=table.players.index(self)
        for p in table.players[list_index+1:]:
            p.position-=1
        table.players.remove(self)
        
    def clear(self):
        """Clear player's hand and reset status"""
        self.cards=[]
        self.is_folded=False
        self.all_in=False
        self.raised=0

    def add(self, cards):
        """Add cards to player's hand"""
        self.cards.append(cards)

# Deck class represents the deck of cards
class Deck(Hand):
    def __init__(self):
        """Initialize an empty deck"""
        self.cards=[]

    def populate(self):
        """Create a full deck of cards"""
        for rank in Card.RANKS:
            for suit in Card.SUITS:
                card=Card(rank, suit)
                self.cards.append(card)

    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)

    def print_cards(self):
        """Print all cards in deck"""
        rep=''
        for card in self.cards:
            rep+=str(card)+' '
        print (rep)

    def deal_to(self, hand, cards=1, faceup=True):
        """Deal cards to a hand"""
        if len(self.cards)<cards:
            print ('not enough cards to deal')
        elif len(self.cards)==0:
            print ('deck empty')
        else:
            dealt=[]
            if not faceup:
                for card in self.cards:
                    card.faceup=False
            for i in range (0,cards):
                dealt.append(self.cards.pop())
            for card in dealt:
                hand.add(card)

# Table class represents the poker table
class Table(Hand):
    def __init__(self):
        """Initialize a new table"""
        self.cards=[]  # Community cards
        self.players=[]  # Players at table
        self.is_folded=False
        self.button=0  # Dealer button position
        self.hands=0  # Hand counter
        self.blinds_timer=0  # Blind level timer
        
    def print_cards(self):
        """Print community cards"""
        rep='Community cards_______________\n'
        if self.is_folded:
            rep='FF'
        else:
            for card in self.cards:
                card.faceup=True
                rep+=str(card)+' '
        print (rep)

    def print_players(self):
        """Print all players at table"""
        for player in self.players:
            print (player)
            
    def clear(self):
        """Clear table cards"""
        self.cards=[]

# Pot class manages the betting pot
class Pot(object):
    stage_dict={0:'pre-flop bet', 1:'dealing the flop', 2:'dealing the turn', 3:'dealing the river'}
    deal_sequence=[0,3,1,1]  # Number of cards to deal each stage
    pot_number=0
    
    def __init__(self, table, name):
        """Initialize a new pot"""
        self.players=[]  # All players in pot
        self.folded_players=[]  # Folded players
        self.active_players=[]  # Active players
        self.limpers=0  # Number of limpers
        self.name=name
        self.blinds=BLINDS
                    
        self.total=0  # Total pot size
        
        self.button=table.button
        self.to_play=0  # Amount to call
        self.stage=0  # Current betting stage
        self.turn=0  # Current turn
        self.no_raise=0  # Number of no raises
        self.already_bet=False  # Bet made this round
        self.raised=False  # Raise made this round

    @property
    def is_frozen(self):
        """Check if pot is frozen (one player remaining)"""
        if len(self.active_players)<=1:
            self.active_players=[]
            return True
        else:
            return False

    @property
    def yet_to_play(self):
        """Get number of players yet to act"""
        ytp=self.table_size-(self.turn+1)
        if ytp<1: ytp=1
        return ytp

    @property
    def one_remaining(self):
        """Check if only one player remains"""
        if len(self.folded_players)==(self.table_size-1):
            return True
        else:
            return False
        
    @property
    def table_size(self):
        """Get number of players at table"""
        return len(self.players)
        
    def __str__(self):
        """String representation of pot"""
        rep='Pot= '+str(self.total)+'.  to play:'+str(self.to_play)
        return str(rep)
            
    def set_blinds(self):
        """Set blinds for the hand"""
        dealer=(self.button)%self.table_size
        small_blind=(self.button+1)%self.table_size
        big_blind=(self.button+2)%self.table_size

        self.players[dealer].dealer=True
        self.players[small_blind].small_blind=True
        self.players[big_blind].big_blind=True

    @property
    def who_plays(self):
        """Get next player to act"""
        next_up=0
        if self.stage==0:
            next_up=(self.button+3)%self.table_size
            return next_up
        else:
            next_up=(self.button+1)%self.table_size
            return next_up

# Side_pot class for handling side pots
class Side_pot(Pot):
    serial=0
    
    def __init__(self, parent):
        """Initialize a side pot"""
        Pot.__init__(self, parent, Pot)
        self.button=parent.button
        Side_pot.serial+=1
        self.name='side pot '+str(Side_pot.serial)
        self.players=[]

# Debug function to print game state
def debug(pot):
    """Print detailed game state for debugging"""
    print('debug______________________')
    for player in pot.players:
        print (str(player.name)+' Stack='+str(player.stack)+' Stake='+str(player.stake)+' Player in pot='+str(player.in_pot)+'  Pot total='+str(pot.total)+'  all_in='+str(player.all_in)+'first all in'+str(player.first_all_in))
        print ('is folded'+str(player.is_folded))
        print ('raw data='+str(player.raw_data))
        print ('position='+str(player.position))
    
    for pot in pots:
        print (str(pot.name)+' total '+ str(pot.total))
        print ('yet to play:'+str(pot.yet_to_play))
        print ('active players')
        for player in pot.active_players:
            print (str(player.name))
        print ('table size '+str(pot.table_size))
        print ('limpers='+str(pot.limpers))
        print ('no raise '+str(pot.no_raise))
        print ('frozen='+str(pot.is_frozen))
        print ('one remaining='+str(pot.one_remaining))
        print ('Pot to play:  '+str(pot.to_play))
    print ('turn'+str(pot.turn)+'  no_raise'+str(pot.no_raise))
    print ('______________________________')

# Move to next player
def next_player(pot, is_raise=False):
    """Advance to next player"""
    pot.turn+=1
    if is_raise:
        pot.no_raise=1
    else:
        pot.no_raise+=1
    return

# Prepare for next hand
def next_hand(table, deck):
    """Reset table for next hand"""
    table.clear()
    deck.clear()
    Side_pot.serial=0

    for hand in table.players:
        hand.clear()
        hand.small_blind=False
        hand.big_blind=False
        hand.dealer=False
        hand.first_all_in=False

    table.button+=1

# Handle antes and initial dealing
def ante_up(pot):
    """Post blinds and deal initial cards"""
    for player in pot.players:
        player.ante(pot)
        print (player)
        deck.deal_to(player, 2)
        if player.stratname=='Human':
            player.flip()
        player.print_cards()
        pot.already_bet=True

    print (pot)
    print ('\n\n\n')

# Handle betting round
def betting_round(pot, table):
    """Process a complete betting round"""
    global pots
    is_side_pot=False
    create_side_pot=False
    side_potters=[]
    
    while pot.no_raise<(pot.table_size):
        next_up=(int(pot.who_plays)+(pot.turn))%pot.table_size
        player=pot.players[next_up]
        player.to_play=(pots[-1].to_play-player.in_pot)
        if player.to_play<0:
            player.to_play=0

        if pots[-1].is_frozen==False:
            if player in pots[-1].active_players:
                print (str(player.name)+' to play'+ str(player.to_play)+'\n')
                for strategy in player.strategy:
                    strategy.decide_play(player, pots[-1])
            else:
                player.no_play(pot)
        else:
            player.no_play(pot)

        pots[-1].total+=player.stake
        player.in_pot+=player.stake
        player.stack-=player.stake
         
        if player.stack==0 and player.first_all_in==False:
            print (str(player.name)+' is all in ')
            is_side_pot=True
            player.all_in=True
            player.first_all_in=True

    if pots[-1].one_remaining:
        is_side_pot=False
            
    # Handle side pots
    if is_side_pot:
        for player in pots[-1].players:
            if player.is_folded==False:
                side_potters.append(player)
            
        side_potters.sort(key=attrgetter('in_pot'), reverse=True)
        big_bet=side_potters[0].in_pot

        next_pot_players=[]
        
        print ('side pot')
        print ('high bet'+str(big_bet))
        low_bet=side_potters[-1].in_pot
        print ('low bet'+str(low_bet))
        
        for player in side_potters:
            refund=(player.in_pot-low_bet)
            if len(next_pot_players)>1:
                create_side_pot=True

            player.in_pot-=refund
            pot.total-=refund
            player.stack+=refund
            player.carry_over=refund

            print ('player in side pot - '+str(player.name))
            
            if player.carry_over>0:
                next_pot_players.append(player)
            else:
                if player in pots[-1].active_players:
                    pots[-1].active_players.remove(player)
      
            print (str(player.name))
            print ('refund...'+str(refund))

        if create_side_pot:
            sidepot=Side_pot(pot)
            
            for player in next_pot_players:
                sidepot.players.append(player)
                sidepot.total+=player.carry_over
                player.in_pot+=player.carry_over
                player.stack-=player.carry_over
                
                if player.stack>0:
                    player.first_all_in=False
                    player.all_in=False
                    pots[-1].active_players.append(player)
                
            pots.append(sidepot)

    # Reset pot for next round
    for pot in pots:
        print (str(pot.name))
        pot.to_play=0
        print ('pot size= '+str(pot.total))
        
        for player in pot.players:
            player.in_pot=0
            player.stake=0
            player.raised=0

    pots[0].no_raise=0
    pots[0].to_play=0
    pots[0].turn=0
    pots[0].stage+=1
    pots[0].already_bet=False
    pots[0].limpers=0

# Handle showdown
def showdown(pot):
    """Determine winner and distribute pot"""
    scoring=[]
    
    if pot.one_remaining:
        for player in pot.players:
            if player.is_folded==False:
                print (str(player.name)+' wins'+str(pot.total))
                player.stack+=pot.total
    else:
        for player in pot.players:
            if player.is_folded==False:
                player.get_value()
                scoring.append(player)
                 
        scoring.sort(key=attrgetter('hand_value', 'tie_break'), reverse=True)
        split_pot=[]
        print ('\n\n\n')
        for player in scoring:
            if player.stratname!='Human':
                player.flip()
            player.print_cards()
            print (player.name+' has '+str(player.rep))
                
        # Check for split pot
        split_stake=0
        split=False
        
        for player in scoring[1:]:
            if player.hand_value==scoring[0].hand_value and player.tie_break==scoring[0].tie_break:
                split=True
                split_pot.append(scoring[0])
                split_pot.append(player)

        if split:
            print ('split pot')
            split_stake=int((pot.total/(len(split_pot))))
            for player in split_pot:
                print (str(player.name)+' wins '+str(split_stake))
                player.stack+=split_stake
        else:
            scoring[0].stack+=pot.total
            print (str(scoring[0].name)+' wins '+str(pot.total))

# Main game setup and loop
BLINDS=[10,20]  # Initial blind levels

table=Table()  # Create table

# Create players with different strategies
player1=Hand('Philip', table, 'SklanskySys2')
player2=Hand('Igor', table, 'SklanskySys2')
player3=Hand('Carol', table, 'SklanskySys2')
player4=Hand('Johnboy', table, 'SklanskySys2')
player5=Hand('Rob', table, 'SklanskySys2')
player6=Hand('Alex', table, 'SklanskySys2')
player7=Hand('Wynona', table, 'SklanskySys2')
player8=Hand('Timur', table, 'SklanskySys2')
player9=Hand('wcjunkins', table, 'wcjunkins')

deck=Deck()  # Create deck

status='play'  # Game status

# Main game loop
while status=='play':
    # Shuffle deck
    deck.populate()
    deck.shuffle()

    # Create pot for this hand
    pots=[]
    pot=Pot(table, 'main')
    
    for player in table.players:
        pot.players.append(player)
        pot.active_players.append(player)
            
    pots.append(pot)
    
    # Set blinds and deal initial cards
    pot.set_blinds()
    print ('Hand#'+str(table.hands))
    print ('Blinds: '+str(BLINDS))
    ante_up(pot)

    # Play through all betting rounds
    while pot.stage<4:
        deck.deal_to(table, Pot.deal_sequence[pot.stage], True)
        print (str(Pot.stage_dict[pot.stage]))
        table.print_cards()        	
        betting_round(pots[-1], table)

    # Showdown if multiple players remain
    if len(table.players)>1:
        for pot in pots:
            showdown(pot)
            
    # Update game state
    table.hands+=1
    table.blinds_timer=table.hands%6
    if table.blinds_timer==5:
        BLINDS[:] = [x*2 for x in BLINDS]  # Increase blinds
        
    # Check for busted players
    for player in table.players[:]:
        print (player.name, player.stack, BLINDS[1])
        if player.stack<=BLINDS[1]:
            player.bust()
            
    # Check for winner
    if len(table.players)==1:
        status='winner'
    
    print ('\n\n\n')
    next_hand(table, deck)
    
# Announce winner
for player in table.players:
    print (str(player.name)+' wins the game')




    



    






   



