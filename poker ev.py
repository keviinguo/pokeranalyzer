import random
from collections import Counter
from itertools import combinations
import matplotlib.pyplot as plt


RANK_ORDER = "23456789TJQKA"
SUITS = "hdcs"


def create_deck():
    """Creates a standard 52-card deck."""
    return [rank + suit for rank in RANK_ORDER for suit in SUITS]


def card_value(rank):
    """Turns card rank into a number."""
    return RANK_ORDER.index(rank) + 2


def parse_cards(card_string):
    """Converts input like 'Ah Kh' into a list of cards."""
    if not card_string.strip():
        return []

    cards = card_string.strip().split()
    parsed = []

    for card in cards:
        if len(card) != 2:
            raise ValueError(f"Invalid card format: {card}")
        rank = card[0].upper()
        suit = card[1].lower()

        if rank not in RANK_ORDER or suit not in SUITS:
            raise ValueError(f"Invalid card: {card}")

        parsed.append(rank + suit)

    return parsed


def is_straight(values):
    """Checks if a hand has a straight."""
    values = sorted(set(values))

    if len(values) < 5:
        return False, None

    for i in range(len(values) - 4):
        window = values[i:i + 5]
        if window == list(range(window[0], window[0] + 5)):
            return True, window[-1]

    if {14, 2, 3, 4, 5}.issubset(values):
        return True, 5

    return False, None


def evaluate_5card_hand(cards):
    """Evaluates a 5-card poker hand."""
    ranks = [card[0] for card in cards]
    suits = [card[1] for card in cards]
    values = sorted([card_value(r) for r in ranks], reverse=True)

    rank_counts = Counter(values)
    counts = sorted(rank_counts.values(), reverse=True)
    counts_sorted = sorted(rank_counts.items(), key=lambda x: (-x[1], -x[0]))

    flush = len(set(suits)) == 1
    straight, straight_high = is_straight(values)

    if flush and straight:
        return (8, straight_high)

    if counts == [4, 1]:
        four = counts_sorted[0][0]
        kicker = counts_sorted[1][0]
        return (7, four, kicker)

    if counts == [3, 2]:
        triple = counts_sorted[0][0]
        pair = counts_sorted[1][0]
        return (6, triple, pair)

    if flush:
        return (5, *sorted(values, reverse=True))

    if straight:
        return (4, straight_high)

    if counts == [3, 1, 1]:
        triple = counts_sorted[0][0]
        kickers = sorted([v for v, c in rank_counts.items() if c == 1], reverse=True)
        return (3, triple, *kickers)

    if counts == [2, 2, 1]:
        pairs = sorted([v for v, c in rank_counts.items() if c == 2], reverse=True)
        kicker = [v for v, c in rank_counts.items() if c == 1][0]
        return (2, pairs[0], pairs[1], kicker)

    if counts == [2, 1, 1, 1]:
        pair = [v for v, c in rank_counts.items() if c == 2][0]
        kickers = sorted([v for v, c in rank_counts.items() if c == 1], reverse=True)
        return (1, pair, *kickers)

    return (0, *sorted(values, reverse=True))


def evaluate_best_hand(cards):
    """Finds the best 5-card hand out of 7 cards."""
    best = None
    for combo in combinations(cards, 5):
        score = evaluate_5card_hand(combo)
        if best is None or score > best:
            best = score
    return best


def monte_carlo_equity(hero_cards, board_cards, num_sims=10000):
    """Estimates win, tie, and loss probabilities against one random opponent."""
    wins = 0
    ties = 0
    losses = 0

    known_cards = set(hero_cards + board_cards)

    for _ in range(num_sims):
        deck = create_deck()
        remaining_deck = [card for card in deck if card not in known_cards]
        random.shuffle(remaining_deck)

        opp_cards = remaining_deck[:2]
        cards_needed = 5 - len(board_cards)
        sim_board = board_cards + remaining_deck[2:2 + cards_needed]

        hero_score = evaluate_best_hand(hero_cards + sim_board)
        opp_score = evaluate_best_hand(opp_cards + sim_board)

        if hero_score > opp_score:
            wins += 1
        elif hero_score == opp_score:
            ties += 1
        else:
            losses += 1

    total = wins + ties + losses
    return wins / total, ties / total, losses / total


def calculate_ev(pot_size, call_amount, win_prob, tie_prob=0.0):
    """
    Calculates EV of calling.

    pot_size = current pot after opponent bet, before your call
    call_amount = amount you must call
    """
    money_won_if_win = pot_size + call_amount
    ev = (win_prob * money_won_if_win) - ((1 - win_prob - tie_prob) * call_amount)
    return ev


def break_even_percentage(pot_size, call_amount):
    """Calculates break-even win percentage."""
    return call_amount / (pot_size + call_amount)


def plot_ev_vs_win_probability(pot_size, call_amount, actual_win_prob, actual_ev):
    """Plots EV against win probability."""
    win_probs = [i / 100 for i in range(101)]
    ev_values = [calculate_ev(pot_size, call_amount, wp) for wp in win_probs]

    plt.figure(figsize=(8, 5))
    plt.plot(win_probs, ev_values, label="EV of Call")
    plt.axhline(0, linestyle="--", label="Break-even EV")
    plt.axvline(actual_win_prob, linestyle="--", label="Your Win Probability")
    plt.scatter([actual_win_prob], [actual_ev], s=80, label="Your Scenario")

    plt.xlabel("Win Probability")
    plt.ylabel("Expected Value ($)")
    plt.title("EV vs Win Probability")
    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    print("Enter cards like: Ah Kh")

    try:
        hero_cards = parse_cards(input("Enter your 2 cards: "))
        if len(hero_cards) != 2:
            raise ValueError("You must enter exactly 2 cards.")

        board_input = input("Enter board cards shown so far (0 to 5 cards): ")
        board_cards = parse_cards(board_input)

        if len(board_cards) > 5:
            raise ValueError("Board cannot have more than 5 cards.")

        all_known = hero_cards + board_cards
        if len(all_known) != len(set(all_known)):
            raise ValueError("Duplicate cards detected.")

        pot_size = float(input("Enter current pot size AFTER opponent bet, BEFORE your call: "))
        call_amount = float(input("Enter amount you must call: "))
        num_sims = int(input("Enter number of simulations (ex: 10000): "))

        win_prob, tie_prob, loss_prob = monte_carlo_equity(hero_cards, board_cards, num_sims)
        ev = calculate_ev(pot_size, call_amount, win_prob, tie_prob)
        break_even = break_even_percentage(pot_size, call_amount)

        print(f"Win probability: {win_prob:.2%}")
        print(f"Tie probability: {tie_prob:.2%}")
        print(f"Loss probability: {loss_prob:.2%}")
        print(f"Break-even win rate: {break_even:.2%}")
        print(f"Expected value of call: ${ev:.2f}")

        if ev > 0:
            print("Recommendation: CALL")
        else:
            print("Recommendation: FOLD")

        plot_ev_vs_win_probability(pot_size, call_amount, win_prob, ev)

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()