#!/usr/bin/env python3

import math
import logging
import random
from typing import List, Tuple, Set, Dict

# Set up logging
logger = logging.getLogger('dobble_generator')


def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def next_prime(n: int) -> int:
    """Find the next prime number greater than or equal to n."""
    if n <= 2:
        return 2
    # Start with next odd number
    prime = n + 1 if n % 2 == 0 else n
    while not is_prime(prime):
        prime += 2
    return prime


def calculate_dobble_parameters(n_symbols: int) -> Tuple[int, int, int]:
    """
    Calculate parameters for Dobble cards based on finite projective plane.

    Args:
        n_symbols: Approximate number of different symbols desired

    Returns:
        Tuple of (order, symbols_per_card, total_cards)
    """
    # For a projective plane of order n:
    # - Each card contains n+1 symbols
    # - Total number of symbols is n²+n+1
    # - Total number of cards is n²+n+1

    # Solve for n: n²+n+1 >= n_symbols
    # This is a quadratic: n² + n + (1-n_symbols) >= 0
    a, b, c = 1, 1, 1 - n_symbols
    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        logger.warning(f"Invalid discriminant: {discriminant}")
        # Fall back to a reasonable approximation
        n = int(math.sqrt(n_symbols - 1))
    else:
        # Calculate the two roots
        root1 = (-b + math.sqrt(discriminant)) / (2 * a)
        root2 = (-b - math.sqrt(discriminant)) / (2 * a)
        # We want the positive root
        n = max(root1, root2)
        # Round up to ensure we have enough symbols
        n = math.ceil(n)

    # Find the next prime power
    if not is_prime(n):
        n = next_prime(n)

    # Calculate parameters
    symbols_per_card = n + 1
    total_symbols = n * n + n + 1
    total_cards = n * n + n + 1

    logger.info(f"For {n_symbols} symbols: order={n}, symbols_per_card={symbols_per_card}, total_cards={total_cards}")
    return n, symbols_per_card, total_cards


def generate_projective_plane(order: int) -> List[Set[int]]:
    """
    Generate a finite projective plane of given order.

    Args:
        order: The order of the projective plane (must be a prime number)

    Returns:
        List of sets, where each set contains the symbols for one card
    """
    if not is_prime(order):
        raise ValueError(f"Order must be a prime number, got {order}")

    n = order
    # Total number of points/lines in the projective plane
    total_points = n * n + n + 1

    # Create the incidence matrix for a projective plane of order n
    # We'll use the construction based on the field GF(n)

    # First, create the set of all points (symbols)
    # Points are represented as (x, y) pairs where x, y are elements of GF(n)
    # Plus n+1 "points at infinity" represented as (i, -1) for i in [0, n-1] and (-1, -1)
    points = []

    # Add the finite points
    for x in range(n):
        for y in range(n):
            points.append((x, y))

    # Add the points at infinity
    for i in range(n):
        points.append((i, -1))
    points.append((-1, -1))

    # Now create the lines (cards)
    lines = []

    # Lines of the form y = mx + b
    for m in range(n):
        for b in range(n):
            line = set()
            for x in range(n):
                y = (m * x + b) % n
                line.add(points.index((x, y)))
            # Add the point at infinity corresponding to this slope
            line.add(points.index((m, -1)))
            lines.append(line)

    # Lines of the form x = c (vertical lines)
    for c in range(n):
        line = set()
        for y in range(n):
            line.add(points.index((c, y)))
        # Add the "vertical" point at infinity
        line.add(points.index((-1, -1)))
        lines.append(line)

    # Line at infinity
    line_at_infinity = set()
    for i in range(n):
        line_at_infinity.add(points.index((i, -1)))
    line_at_infinity.add(points.index((-1, -1)))
    lines.append(line_at_infinity)

    # Verify we have the right number of lines
    assert len(lines) == total_points, f"Expected {total_points} lines, got {len(lines)}"

    # Verify each pair of lines intersects at exactly one point
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            intersection = lines[i].intersection(lines[j])
            assert len(intersection) == 1, f"Lines {i} and {j} intersect at {len(intersection)} points: {intersection}"

    return lines


def generate_dobble_cards(n_symbols: int, shuffle: bool = True) -> Tuple[List[List[int]], int]:
    """
    Generate Dobble cards with the given number of symbols.

    Args:
        n_symbols: Approximate number of different symbols to use
        shuffle: Whether to shuffle the symbols on each card

    Returns:
        Tuple of (list of cards, total symbols)
    """
    # Calculate parameters
    order, symbols_per_card, total_cards = calculate_dobble_parameters(n_symbols)

    # Generate the projective plane
    try:
        cards_as_sets = generate_projective_plane(order)
    except ValueError:
        # If order is not prime, find the closest prime number
        logger.warning(f"Order {order} is not prime, adjusting")
        order = next_prime(order)
        _, symbols_per_card, total_cards = calculate_dobble_parameters(order * order + order + 1)
        cards_as_sets = generate_projective_plane(order)

    # Convert sets to lists for consistent ordering
    cards = [sorted(list(card)) for card in cards_as_sets]

    # Determine the actual number of symbols used
    all_symbols = set()
    for card in cards:
        all_symbols.update(card)
    total_symbols = len(all_symbols)

    # Remap symbols to 0..total_symbols-1 for cleaner indexing
    symbol_map = {old: new for new, old in enumerate(sorted(all_symbols))}
    cards = [[symbol_map[s] for s in card] for card in cards]

    # Shuffle symbols on each card if requested
    if shuffle:
        for card in cards:
            random.shuffle(card)

    # Verify the Dobble property: any two cards share exactly one symbol
    verify_dobble_property(cards)

    logger.info(
        f"Generated {len(cards)} cards with {symbols_per_card} symbols per card, using {total_symbols} total symbols")
    return cards, total_symbols


def verify_dobble_property(cards: List[List[int]]) -> bool:
    """
    Verify that any two cards share exactly one symbol.

    Args:
        cards: List of cards, where each card is a list of symbols

    Returns:
        True if the Dobble property holds, raises AssertionError otherwise
    """
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            card1, card2 = set(cards[i]), set(cards[j])
            intersection = card1.intersection(card2)
            if len(intersection) != 1:
                error_msg = f"Cards {i} and {j} share {len(intersection)} symbols: {intersection}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
    return True


def limit_cards(cards: List[List[int]], max_cards: int) -> List[List[int]]:
    """
    Limit the number of cards while preserving the Dobble property.

    Args:
        cards: List of all generated cards
        max_cards: Maximum number of cards to keep

    Returns:
        Subset of cards that still maintain the Dobble property
    """
    if max_cards >= len(cards):
        return cards

    # Simple approach: just take the first max_cards
    # This preserves the Dobble property since any subset of a valid Dobble deck is still valid
    limited_cards = cards[:max_cards]

    # Verify the property still holds
    verify_dobble_property(limited_cards)

    return limited_cards


def select_symbols(cards: List[List[int]], available_symbols: int) -> Dict[int, int]:
    """
    Create a mapping from card symbols to actual image indices.

    Args:
        cards: List of generated cards
        available_symbols: Number of actual images/icons available

    Returns:
        Dictionary mapping card symbols to image indices
    """
    # Find all unique symbols used in the cards
    all_symbols = set()
    for card in cards:
        all_symbols.update(card)

    if len(all_symbols) > available_symbols:
        raise ValueError(f"Not enough images: need {len(all_symbols)}, have {available_symbols}")

    # Create a mapping from symbols to image indices
    # If shuffle is True, assign images randomly
    symbol_to_image = {symbol: i % available_symbols for i, symbol in enumerate(all_symbols)}

    return symbol_to_image