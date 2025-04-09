import poker
from wcjunkins import wcjunkins
import random

def create_test_hand(cards_str):
    """Create a hand from a string representation like 'Ah Kd'"""
    cards = []
    for card_str in cards_str.split():
        rank = card_str[0]
        suit = card_str[1].lower()
        cards.append(poker.Card(rank, suit))
    return cards

def create_test_table(community_cards_str):
    """Create community cards from a string representation like 'Ah Kd Qc'"""
    if not community_cards_str:
        return []
    return create_test_hand(community_cards_str)

def run_test_case(name, hole_cards, community_cards, pot_size, to_play, position, expected_action):
    """Run a single test case and print the results"""
    print(f"\n=== Test Case: {name} ===")
    
    # Create table and pot
    table = poker.Table()
    pot = poker.Pot(table, "TestPot")
    pot.total = pot_size
    pot.to_play = to_play
    
    # Create player
    player = poker.Hand("TestPlayer", table, "wcjunkins")
    player.cards = create_test_hand(hole_cards)
    player.position = position
    player.stack = 1000  # Starting stack
    
    # Set community cards
    table.cards = create_test_table(community_cards)
    
    # Get AI decision
    strategy = wcjunkins(player)
    action = strategy.decide_play(player, pot)
    
    # Print test details
    print(f"Hole Cards: {hole_cards}")
    print(f"Community Cards: {community_cards}")
    print(f"Position: {position}")
    print(f"Pot Size: {pot_size}")
    print(f"To Play: {to_play}")
    print(f"Expected Action: {expected_action}")
    print(f"Actual Action: {action}")
    
    # Evaluate result
    if action == expected_action:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
    
    return action == expected_action

def main():
    """Run all test cases"""
    tests = [
        # Test Case 1: Strong pre-flop hand in late position
        {
            "name": "Strong Pre-flop Hand in Late Position",
            "hole_cards": "Ah Kh",
            "community_cards": "",
            "pot_size": 30,
            "to_play": 0,
            "position": 8,
            "expected_action": "check_call"  # Should check with strong hand when no bet to call
        },
        
        # Test Case 2: Weak pre-flop hand in early position
        {
            "name": "Weak Pre-flop Hand in Early Position",
            "hole_cards": "7h 2d",
            "community_cards": "",
            "pot_size": 30,
            "to_play": 0,
            "position": 2,
            "expected_action": "fold"  # Should fold weak hand in early position
        },
        
        # Test Case 3: Strong post-flop hand with pot odds
        {
            "name": "Strong Post-flop Hand with Pot Odds",
            "hole_cards": "Ah Kh",
            "community_cards": "Qh Jh Th",
            "pot_size": 100,
            "to_play": 20,
            "position": 5,
            "expected_action": "check_call"  # Should call with strong hand and good pot odds
        },
        
        # Test Case 4: Very strong hand with betting opportunity
        {
            "name": "Very Strong Hand with Betting Opportunity",
            "hole_cards": "Ah Kh",
            "community_cards": "Qh Jh Th",
            "pot_size": 100,
            "to_play": 0,
            "position": 6,
            "expected_action": "bet"  # Should bet with very strong hand
        },
        
        # Test Case 5: Marginal hand with poor pot odds
        {
            "name": "Marginal Hand with Poor Pot Odds",
            "hole_cards": "Ah Kd",
            "community_cards": "Qh Jh Th",
            "pot_size": 100,
            "to_play": 80,
            "position": 4,
            "expected_action": "fold"  # Should fold with marginal hand and poor pot odds
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if run_test_case(**test):
            passed += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {passed}/{total} tests")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

if __name__ == "__main__":
    main() 