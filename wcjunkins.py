import random
import pokerstrat
from collections import Counter

# My strategy for the poker AI-player (probably not good lol)
class wcjunkins(pokerstrat.Strategy):

    # Initialize the strategy
    def __init__(self, player):
        super().__init__(player)
        self.name = "wcjunkins"
        self.hand_strength = 0  # Will store current hand strength (0-1)
        self.position = 0  # Will store position at table (0 = early, 1 = middle, 2 = late)
        self.stack_size = 1000  # Will store current stack size
        self.pot_size = 0  # Will store current pot size
        self.opponents = []  # Will store opponent information
        self.current_stage = 'preflop'  # Will track current game stage
        self.aggression_factor = 0.6  # Will control betting aggression (0-1)
        self.bluff_frequency = 0.7  # Increased bluff frequency (0-1)               These two seemed to be good values against the Sklansky bots.
        
        # Position-based strategy parameters
        self.position_aggression = [0.3, 0.5, 0.7]  # Early, middle, late position aggression
        self.position_hand_ranges = {
            0: 0.3,  # Early position - tighter range
            1: 0.5,  # Middle position - moderate range
            2: 0.7   # Late position - wider range
        }
        
        # Preflop hand rankings
        self.preflop_rankings = {
            'AA': 1.0, 'KK': 0.95, 'QQ': 0.9, 'JJ': 0.85, 'TT': 0.8,
            'AKs': 0.85, 'AQs': 0.8, 'AJs': 0.75, 'ATs': 0.7,
            'KQs': 0.75, 'KJs': 0.7, 'KTs': 0.65,
            'QJs': 0.7, 'QTs': 0.65,
            'JTs': 0.65,
            '99': 0.75, '88': 0.7, '77': 0.65, '66': 0.6, '55': 0.55,
            'AKo': 0.7, 'AQo': 0.65, 'AJo': 0.6, 'ATo': 0.55,
            'KQo': 0.6, 'KJo': 0.55, 'KTo': 0.5,
            'QJo': 0.55, 'QTo': 0.5,
            'JTo': 0.5,
            '44': 0.5, '33': 0.45, '22': 0.4
        }
        
        self.blind_steal_range = {
            0: ['AA', 'KK', 'QQ', 'AKs', 'AKo'],  # Early position
            1: ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs'],  # Middle position
            2: ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AKo', 'AQs', 'AJs', 'KQs']  # Late position
        }
        
        self.push_fold_ranges = {
            '10bb': ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AKo', 'AQs', 'AJs', 'KQs', 'ATs', 'KJs'],
            '15bb': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', 'AKs', 'AKo', 'AQs', 'AJs', 'KQs', 'ATs', 'KJs', 'QJs'],
            '20bb': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', 'AKs', 'AKo', 'AQs', 'AJs', 'KQs', 'ATs', 'KJs', 'QJs', 'JTs']
        }
        
        # Bluffing opportunities
        self.bluff_opportunities = {
            'preflop': 0.1,  # Rarely bluff preflop
            'flop': 0.25,    # Moderate bluffing on flop
            'turn': 0.35,    # More bluffing on turn
            'river': 0.4     # Most bluffing on river
        }
    
    def calculate_pot_odds(self, pot, to_call):
        """Calculate pot odds for calling"""
        if to_call == 0:
            return 1.0  # Free to call
        return pot.total / to_call if to_call > 0 else 0

    def calculate_implied_odds(self, hand, pot):
        """Calculate implied odds based on hand potential"""
        outs = self._calculate_outs(hand, pot)
        if outs == 0:
            return 0.0
        # Approximate equity: (outs * 2) + 1 for turn, (outs * 2) for river
        if len(hand.total_cards) - len(hand.cards) == 3:  # Flop
            equity = (outs * 2) + 1
        elif len(hand.total_cards) - len(hand.cards) == 4:  # Turn
            equity = outs * 2
        else:
            equity = 0
        return min(equity / 100, 1.0)  # Convert to 0-1 range

    def _calculate_outs(self, hand, pot):
        """Calculate number of outs for drawing hands"""
        all_cards = hand.total_cards
        if len(all_cards) < 5:
            return 0
        
        # Check for flush draws
        suits = [card.suit for card in all_cards]
        suit_counts = Counter(suits)
        flush_suit = None
        for suit, count in suit_counts.items():
            if count >= 3:  # At least 3 cards of same suit
                flush_suit = suit
                break
        
        if flush_suit:
            # Count remaining cards of the same suit
            return 13 - suit_counts[flush_suit]
        
        # Check for straight draws
        # Convert ranks to numeric values
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                   '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        ranks = sorted([rank_map[card.rank] for card in all_cards])
        unique_ranks = sorted(set(ranks))
        
        if len(unique_ranks) >= 4:
            # Check for open-ended straight draw
            for i in range(len(unique_ranks) - 3):
                if unique_ranks[i+3] - unique_ranks[i] == 3:
                    return 8  # 8 outs for open-ended straight draw
                elif unique_ranks[i+3] - unique_ranks[i] == 4:
                    return 4  # 4 outs for gutshot straight draw
        
        return 0

    def adjust_hand_strength(self, hand_strength, pot):
        """Adjust hand strength based on table dynamics"""
        # Get number of players still to act
        players_to_act = len([p for p in pot.players if p.to_play < pot.to_play])
        
        # Get average stack size
        avg_stack = sum(p.stack for p in pot.players) / len(pot.players)
        
        # Adjust for number of players
        if players_to_act > 3:
            hand_strength *= 0.8  # Reduce strength with many players to act
        elif players_to_act == 1:
            hand_strength *= 1.2  # Increase strength heads-up
        
        # Adjust for stack sizes
        if self.stack_size < avg_stack * 0.5:  # Short stacked
            hand_strength *= 1.3  # Increase strength when short-stacked
        elif self.stack_size > avg_stack * 1.5:  # Deep stacked
            hand_strength *= 0.9  # Reduce strength when deep-stacked
        
        # Adjust for position
        if self.position == 2:  # Late position
            hand_strength *= 1.2  # More aggressive in late position
        elif self.position == 0:  # Early position
            hand_strength *= 0.9  # More conservative in early position
        
        return min(hand_strength, 1.0)

    # Decide the action to take
    def decide_play(self, player, pot):
        # Update stack size and position
        self.stack_size = player.stack
        
        # Calculate position based on player's index in the table
        total_players = len(pot.players)
        player_index = pot.players.index(player)
        
        # Calculate position based on player count
        if total_players <= 6:
            # For 6 or fewer players, use 3 positions
            if player_index <= 1:  # First two positions
                self.position = 0  # Early position
            elif player_index <= 3:  # Middle two positions
                self.position = 1  # Middle position
            else:
                self.position = 2  # Late position
        else:
            # For more than 6 players, use 3 positions with more players in EP
            if player_index <= 2:  # First three positions
                self.position = 0  # Early position
            elif player_index <= 4:  # Middle two positions
                self.position = 1  # Middle position
            else:
                self.position = 2  # Late position
        
        # Get the current bet amount needed to call
        to_call = pot.to_play - player.to_play
        
        # Calculate pot odds and implied odds
        pot_odds = self.calculate_pot_odds(pot, to_call)
        implied_odds = self.calculate_implied_odds(player, pot)
        total_odds = pot_odds + implied_odds
        
        # Adjust hand strength based on table dynamics
        adjusted_strength = self.adjust_hand_strength(self.hand_strength, pot)
        
        # Determine if this is a good bluffing spot
        is_bluff_spot = False
        if self.position == 2:  # Late position
            if total_players <= 3:  # Few players
                is_bluff_spot = True
            elif pot.to_play == pot.blinds[1]:  # Facing just the big blind
                is_bluff_spot = True
            elif pot.raised == False:  # No raises yet
                is_bluff_spot = True
        
        # Check for push/fold situations
        bb = pot.blinds[1]  # Big blind amount
        stack_in_bb = self.stack_size / bb
        
        # Balanced push/fold ranges
        if stack_in_bb <= 15:  # Short stacked
            hand_str = ''.join(sorted([card.rank for card in player.cards], reverse=True))
            if player.cards[0].suit == player.cards[1].suit:
                hand_str += 's'
            else:
                hand_str += 'o'
            
            # Use appropriate range based on stack size
            range_key = '10bb' if stack_in_bb <= 10 else '15bb'
            if hand_str in self.push_fold_ranges[range_key]:
                return player.bet(pot, player.stack)
            elif to_call > self.stack_size * 0.25:  # Balanced folding threshold
                return player.fold(pot)
            else:
                return player.check_call(pot)
        
        # If we don't have enough chips to make the minimum bet
        if to_call > player.stack:
            # Balanced all-in decisions
            if adjusted_strength > 0.75 or total_odds > 1.8:
                return player.bet(pot, player.stack)
            elif adjusted_strength > 0.55 and self.position == 2 and total_odds > 1.3:
                return player.bet(pot, player.stack)
            else:
                return player.fold(pot)
        
        # Get position-based aggression factor
        aggression = self.position_aggression[self.position]
        
        # Consider bluffing in good spots
        if is_bluff_spot and random.random() < self.bluff_frequency:
            # Calculate bluff bet size
            bluff_bet = pot.to_play * 1.5  # Standard bluff size
            if bluff_bet <= player.stack:
                return player.bet(pot, bluff_bet)
        
        # Balanced blind stealing
        if pot.to_play == pot.blinds[1] and self.position == 2:  # Facing just the big blind
            hand_str = ''.join(sorted([card.rank for card in player.cards], reverse=True))
            if player.cards[0].suit == player.cards[1].suit:
                hand_str += 's'
            else:
                hand_str += 'o'
            
            if hand_str in self.blind_steal_range[self.position]:
                return player.bet(pot, pot.blinds[1] * 2.2)  # Balanced raise size
        
        # Adjust action weights based on hand strength, position, and pot odds
        if self.position == 0:  # Early position
            if adjusted_strength > 0.85 or total_odds > 2.2:
                action_weights = [0.1, 0.3, 0.6]
            elif adjusted_strength > 0.65 or total_odds > 1.8:
                action_weights = [0.2, 0.4, 0.4]
            elif adjusted_strength > 0.45 or total_odds > 1.4:
                action_weights = [0.3, 0.5, 0.2]
            else:
                action_weights = [0.65, 0.25, 0.1]
        elif self.position == 1:  # Middle position
            if adjusted_strength > 0.85 or total_odds > 2.2:
                action_weights = [0.05, 0.25, 0.7]
            elif adjusted_strength > 0.65 or total_odds > 1.8:
                action_weights = [0.15, 0.35, 0.5]
            elif adjusted_strength > 0.45 or total_odds > 1.4:
                action_weights = [0.25, 0.45, 0.3]
            else:
                action_weights = [0.55, 0.35, 0.1]
        else:  # Late position
            if adjusted_strength > 0.85 or total_odds > 2.2:
                action_weights = [0.0, 0.2, 0.8]
            elif adjusted_strength > 0.65 or total_odds > 1.8:
                action_weights = [0.1, 0.3, 0.6]
            elif adjusted_strength > 0.45 or total_odds > 1.4:
                action_weights = [0.2, 0.4, 0.4]
            else:
                action_weights = [0.45, 0.35, 0.2]
        
        # Choose action based on weighted probabilities
        r = random.random()
        if r < action_weights[0]:
            return player.fold(pot)
        elif r < action_weights[0] + action_weights[1]:
            return player.check_call(pot)
        else:
            # Calculate bet amount based on hand strength, position, and pot odds
            min_bet = max(pot.to_play - player.to_play, 0)
            
            # Find the maximum possible bet considering other players' stacks
            max_opponent_stack = max([p.stack for p in pot.players if p != player], default=0)
            max_bet = min(player.stack, max_opponent_stack, pot.to_play * 2.5)  # Balanced max bet multiplier
            
            if min_bet > max_bet:
                min_bet = max_bet
            
            # Adjust bet size based on multiple factors
            bet_range = max_bet - min_bet
            strength_multiplier = adjusted_strength * (0.9 + aggression)  # Balanced strength impact
            odds_multiplier = min(total_odds, 1.8)  # Balanced odds impact
            
            # Calculate the bet amount
            bet_amount = min_bet + int(bet_range * strength_multiplier * odds_multiplier)
            
            # Ensure bet_amount is within valid bounds
            bet_amount = max(min_bet, min(bet_amount, max_bet))
            
            # If we're raising against an all-in player, just call
            if any(p.stack == 0 for p in pot.players if p != player):
                return player.check_call(pot)
            
            return player.bet(pot, bet_amount)

    def preflop(self, hand, table):
        self.current_stage = 'preflop'
        self.stack_size = hand.stack
        self.pot_size = table.pot
        self.position = self.calculate_position(hand, table)
        self.hand_strength = self.evaluate_preflop_hand(hand)
        
        # Position-based preflop strategy
        if self.position == 0:  # Early position
            if self.hand_strength < 0.6:  # Only play strong hands
                return 'fold'
            elif self.hand_strength < 0.8:
                return 'call'
            else:
                return 'raise'
        elif self.position == 1:  # Middle position
            if self.hand_strength < 0.4:
                return 'fold'
            elif self.hand_strength < 0.7:
                return 'call'
            else:
                return 'raise'
        else:  # Late position
            if self.hand_strength < 0.3:
                return 'fold'
            elif self.hand_strength < 0.6:
                return 'call'
            else:
                return 'raise'

    def flop(self, hand, table):
        self.current_stage = 'flop'
        self.hand_strength = self.evaluate_hand(hand, table)
        self.pot_size = table.pot
        
        # Position-based postflop strategy
        if self.position == 0:  # Early position
            if self.hand_strength < 0.5:
                return 'fold'
            elif self.hand_strength < 0.7:
                return 'call'
            else:
                return 'raise'
        elif self.position == 1:  # Middle position
            if self.hand_strength < 0.4:
                return 'fold'
            elif self.hand_strength < 0.6:
                return 'call'
            else:
                return 'raise'
        else:  # Late position
            if self.hand_strength < 0.3:
                return 'fold'
            elif self.hand_strength < 0.5:
                return 'call'
            else:
                return 'raise'

    def turn(self, hand, table):
        self.current_stage = 'turn'
        self.hand_strength = self.evaluate_hand(hand, table)
        self.pot_size = table.pot
        
        # Similar to flop but slightly tighter ranges
        if self.position == 0:
            if self.hand_strength < 0.6:
                return 'fold'
            elif self.hand_strength < 0.8:
                return 'call'
            else:
                return 'raise'
        elif self.position == 1:
            if self.hand_strength < 0.5:
                return 'fold'
            elif self.hand_strength < 0.7:
                return 'call'
            else:
                return 'raise'
        else:
            if self.hand_strength < 0.4:
                return 'fold'
            elif self.hand_strength < 0.6:
                return 'call'
            else:
                return 'raise'

    def river(self, hand, table):
        self.current_stage = 'river'
        self.hand_strength = self.evaluate_hand(hand, table)
        self.pot_size = table.pot
        
        # Tightest ranges on river
        if self.position == 0:
            if self.hand_strength < 0.7:
                return 'fold'
            elif self.hand_strength < 0.9:
                return 'call'
            else:
                return 'raise'
        elif self.position == 1:
            if self.hand_strength < 0.6:
                return 'fold'
            elif self.hand_strength < 0.8:
                return 'call'
            else:
                return 'raise'
        else:
            if self.hand_strength < 0.5:
                return 'fold'
            elif self.hand_strength < 0.7:
                return 'call'
            else:
                return 'raise'

    def calculate_position(self, hand, table):
        """Calculate position at the table (0=EP, 1=MP, 2=LP)"""
        # Get the total number of players
        total_players = len(table.players)
        
        # Get the current player's index
        player_index = table.players.index(hand)
        
        # Calculate position based on player count
        if total_players <= 6:
            # For 6 or fewer players, use 3 positions
            if player_index <= 1:  # First two positions
                return 0  # Early position
            elif player_index <= 3:  # Middle two positions
                return 1  # Middle position
            else:
                return 2  # Late position
        else:
            # For more than 6 players, use 3 positions with more players in EP
            if player_index <= 2:  # First three positions
                return 0  # Early position
            elif player_index <= 4:  # Middle two positions
                return 1  # Middle position
            else:
                return 2  # Late position

    def evaluate_preflop_hand(self, hand):
        """Evaluate preflop hand strength (0-1) based on standard poker hand rankings"""
        # Get the two cards
        card1, card2 = hand.cards
        
        # Create hand notation (e.g., 'AKs' for Ace-King suited)
        hand_str = self._create_preflop_notation(card1, card2)
        
        # Look up the hand strength in our rankings
        if hand_str in self.preflop_rankings:
            return self.preflop_rankings[hand_str]
        
        # For hands not in our rankings, calculate a basic strength
        return self._calculate_basic_preflop_strength(card1, card2)

    def _create_preflop_notation(self, card1, card2):
        """Create standard poker notation for preflop hands"""
        # Get ranks and suits
        rank1, suit1 = card1.rank, card1.suit
        rank2, suit2 = card2.rank, card2.suit
        
        # Convert ranks to standard notation
        rank_map = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        rank1_str = rank_map.get(rank1, str(rank1))
        rank2_str = rank_map.get(rank2, str(rank2))
        
        # Determine if suited
        suited = 's' if suit1 == suit2 else 'o'
        
        # Create hand notation (higher rank first)
        if rank1 > rank2:
            return f"{rank1_str}{rank2_str}{suited}"
        else:
            return f"{rank2_str}{rank1_str}{suited}"

    def _calculate_basic_preflop_strength(self, card1, card2):
        """Calculate basic preflop hand strength for unranked hands"""
        strength = 0.0
        
        # High card bonus
        high_card = max(card1.rank, card2.rank)
        if high_card >= 12:  # Q or higher
            strength += 0.2
        elif high_card >= 10:  # T or J
            strength += 0.1
            
        # Pair bonus
        if card1.rank == card2.rank:
            strength += 0.3
            
        # Suited bonus
        if card1.suit == card2.suit:
            strength += 0.1
            
        # Connected bonus (e.g., 67, 89)
        if abs(card1.rank - card2.rank) == 1:
            strength += 0.1
            
        return min(strength, 0.9)  # Cap at 0.9 for non-premium hands

    def evaluate_hand(self, hand, table):
        """Evaluate current hand strength including community cards (0-1)"""
        # Combine hole cards and community cards
        all_cards = hand.cards + table.community_cards
        
        # If we don't have enough cards yet, return preflop evaluation
        if len(all_cards) < 5:
            return self.evaluate_preflop_hand(hand)
            
        # Evaluate the best possible hand
        hand_rank = self._evaluate_hand_rank(all_cards)
        
        # Convert hand rank to strength (0-1)
        return self._hand_rank_to_strength(hand_rank)

    def _evaluate_hand_rank(self, cards):
        """Evaluate the rank of a poker hand (higher is better)"""
        # Count ranks and suits
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # Check for flush
        flush = any(count >= 5 for count in suit_counts.values())
        
        # Check for straight
        unique_ranks = sorted(set(ranks))
        straight = False
        if len(unique_ranks) >= 5:
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i+4] - unique_ranks[i] == 4:
                    straight = True
                    break
        
        # Check for pairs, trips, quads
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        trips = [rank for rank, count in rank_counts.items() if count == 3]
        quads = [rank for rank, count in rank_counts.items() if count == 4]
        
        # Determine hand rank
        if flush and straight:
            return 8  # Straight flush
        elif quads:
            return 7  # Four of a kind
        elif trips and pairs:
            return 6  # Full house
        elif flush:
            return 5  # Flush
        elif straight:
            return 4  # Straight
        elif trips:
            return 3  # Three of a kind
        elif len(pairs) >= 2:
            return 2  # Two pair
        elif pairs:
            return 1  # One pair
        else:
            return 0  # High card

    def _hand_rank_to_strength(self, hand_rank):
        """Convert hand rank to strength (0-1)"""
        # Map hand ranks to strength values
        strength_map = {
            0: 0.1,  # High card
            1: 0.3,  # One pair
            2: 0.5,  # Two pair
            3: 0.6,  # Three of a kind
            4: 0.7,  # Straight
            5: 0.8,  # Flush
            6: 0.85, # Full house
            7: 0.9,  # Four of a kind
            8: 1.0   # Straight flush
        }
        return strength_map.get(hand_rank, 0.0)
