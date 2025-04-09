import poker
from pokerstrat import Strategy

class wcjunkins(Strategy):
    def __init__(self, player):
        super().__init__(player)
        self.name = "wcjunkins"
        # Strategy parameters
        self.position_weights = {
            'early': 0.7,    # More conservative in early position
            'middle': 0.85,  # Balanced in middle position
            'late': 1.0      # More aggressive in late position
        }
        self.hand_strength_thresholds = {
            'pre_flop': {
                'fold': 0.3,
                'call': 0.5,
                'raise': 0.7
            },
            'flop': {
                'fold': 0.4,
                'call': 0.6,
                'raise': 0.75
            },
            'turn': {
                'fold': 0.45,
                'call': 0.65,
                'raise': 0.8
            },
            'river': {
                'fold': 0.5,
                'call': 0.7,
                'raise': 0.85
            }
        }
        
    @property
    def play_style(self):
        return "Adaptive Position-Based Strategy with Dynamic Hand Strength Evaluation"
        
    def evaluate_hand_strength(self, player, pot):
        """Evaluate hand strength using poker.py's hand evaluator"""
        hand_value, rep, tie_break, raw_data = player.get_value()
        
        # Get raw values for pre-flop analysis
        raw_values, flush_score, straight, gappers = raw_data
        
        # Pre-flop evaluation
        if len(pot.table.cards) == 0:
            # Convert hand value to 0-1 scale for pre-flop
            if 'pair' in rep:
                return 0.7 + (max(raw_values) / 13.0) * 0.3
            elif flush_score == 2:  # Suited cards
                return 0.5 + (sum(raw_values) / 26.0) * 0.3
            else:
                return 0.3 + (sum(raw_values) / 26.0) * 0.4
                
        # Post-flop evaluation
        # Convert 7-digit hand value to 0-1 scale
        # First digit represents hand rank (1-9)
        # Remaining digits for tie breaks
        hand_strength = float(str(hand_value)[0]) / 9.0
        
        # Adjust based on tie break strength
        tie_break_factor = float(str(tie_break)) / 10000000.0  # Normalize tie break
        
        return hand_strength + (tie_break_factor * 0.1)  # Give 10% weight to tie break
        
    def calculate_pot_odds(self, player, pot):
        """Calculate pot odds and implied odds"""
        if pot.to_play == 0:
            return 0.0
            
        call_amount = pot.to_play - player.in_pot
        if call_amount <= 0:
            return 0.0
            
        # Basic pot odds
        pot_odds = call_amount / (pot.total + call_amount)
        
        # Adjust for implied odds based on remaining stack sizes
        remaining_players = len([p for p in pot.players if not p.is_folded])
        avg_stack = sum(p.stack for p in pot.players if not p.is_folded) / remaining_players
        
        # Better implied odds with deeper stacks
        implied_odds_factor = min(1.0, avg_stack / (pot.total * 2))
        
        return pot_odds * (1 - implied_odds_factor * 0.3)  # Reduce required equity by up to 30% based on implied odds
        
    def get_position_factor(self, player, pot):
        """Calculate position advantage"""
        num_players = len(pot.players)
        active_players = len([p for p in pot.players if not p.is_folded])
        position = player.position
        
        # Early position
        if position <= num_players // 3:
            return self.position_weights['early']
        # Middle position    
        elif position <= (2 * num_players) // 3:
            return self.position_weights['middle']
        # Late position
        else:
            # Increase aggression if fewer players
            late_bonus = 1.0 + (1 - active_players/num_players) * 0.2
            return self.position_weights['late'] * late_bonus
            
    def get_stage_thresholds(self, pot):
        """Get thresholds for current stage"""
        if len(pot.table.cards) == 0:
            return self.hand_strength_thresholds['pre_flop']
        elif len(pot.table.cards) == 3:
            return self.hand_strength_thresholds['flop']
        elif len(pot.table.cards) == 4:
            return self.hand_strength_thresholds['turn']
        else:
            return self.hand_strength_thresholds['river']
            
    def calculate_bet_size(self, player, pot, hand_strength):
        """Calculate optimal bet size based on hand strength and pot size"""
        # Base bet on pot size
        pot_based_bet = pot.total * 0.75
        
        # Adjust based on hand strength
        if hand_strength > 0.9:
            bet_multiplier = 1.5  # Very strong hand - bet bigger
        elif hand_strength > 0.8:
            bet_multiplier = 1.2
        elif hand_strength > 0.7:
            bet_multiplier = 1.0
        else:
            bet_multiplier = 0.8  # Weaker hand - bet smaller
            
        # Consider stack sizes
        max_bet = min(player.stack, max(p.stack for p in pot.players if not p.is_folded))
        target_bet = min(max_bet, pot_based_bet * bet_multiplier)
        
        # Round to a more natural betting amount
        return int(target_bet)
        
    def decide_play(self, player, pot):
        """Main decision making method"""
        # Get current hand strength
        hand_strength = self.evaluate_hand_strength(player, pot)
        
        # Get position factor
        position_factor = self.get_position_factor(player, pot)
        
        # Calculate pot odds
        pot_odds = self.calculate_pot_odds(player, pot)
        
        # Get thresholds for current stage
        thresholds = self.get_stage_thresholds(pot)
        
        # Adjust thresholds based on position
        adjusted_fold = thresholds['fold'] / position_factor
        adjusted_call = thresholds['call'] / position_factor
        adjusted_raise = thresholds['raise'] / position_factor
        
        # Decision making
        if hand_strength < adjusted_fold:
            # Hand too weak, fold
            return player.fold(pot)
            
        if pot.to_play == 0:
            # No bet to call
            if hand_strength > adjusted_raise:
                # Strong hand - bet
                bet_amount = self.calculate_bet_size(player, pot, hand_strength)
                return player.bet(pot, bet_amount)
            else:
                # Marginal hand - check
                return player.check_call(pot)
                
        # There is a bet to call
        if hand_strength > adjusted_raise and hand_strength > pot_odds * 1.5:
            # Strong hand and good pot odds - raise
            bet_amount = self.calculate_bet_size(player, pot, hand_strength)
            return player.bet(pot, bet_amount)
        elif hand_strength > adjusted_call and hand_strength > pot_odds:
            # Decent hand and acceptable pot odds - call
            return player.check_call(pot)
        else:
            # Weak hand or bad pot odds - fold
            return player.fold(pot)
