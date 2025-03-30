#!/usr/bin/env python3

import unittest
import sys
import os
import math
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dobble_math


class TestDobbleMath(unittest.TestCase):
    """Test the mathematical functions for Dobble card generation."""

    def test_is_prime(self):
        """Test the is_prime function."""
        # Test some known primes
        self.assertTrue(dobble_math.is_prime(2))
        self.assertTrue(dobble_math.is_prime(3))
        self.assertTrue(dobble_math.is_prime(5))
        self.assertTrue(dobble_math.is_prime(7))
        self.assertTrue(dobble_math.is_prime(11))
        self.assertTrue(dobble_math.is_prime(13))
        self.assertTrue(dobble_math.is_prime(17))
        self.assertTrue(dobble_math.is_prime(19))
        self.assertTrue(dobble_math.is_prime(23))
        self.assertTrue(dobble_math.is_prime(29))
        self.assertTrue(dobble_math.is_prime(31))

        # Test some known non-primes
        self.assertFalse(dobble_math.is_prime(1))
        self.assertFalse(dobble_math.is_prime(4))
        self.assertFalse(dobble_math.is_prime(6))
        self.assertFalse(dobble_math.is_prime(8))
        self.assertFalse(dobble_math.is_prime(9))
        self.assertFalse(dobble_math.is_prime(10))
        self.assertFalse(dobble_math.is_prime(12))
        self.assertFalse(dobble_math.is_prime(14))
        self.assertFalse(dobble_math.is_prime(15))
        self.assertFalse(dobble_math.is_prime(16))
        self.assertFalse(dobble_math.is_prime(18))
        self.assertFalse(dobble_math.is_prime(20))
        self.assertFalse(dobble_math.is_prime(21))

        # Test edge cases
        self.assertFalse(dobble_math.is_prime(0))
        self.assertFalse(dobble_math.is_prime(-1))
        self.assertFalse(dobble_math.is_prime(-2))

    def test_next_prime(self):
        """Test the next_prime function."""
        # Test some known cases
        self.assertEqual(dobble_math.next_prime(1), 2)
        self.assertEqual(dobble_math.next_prime(2), 2)
        self.assertEqual(dobble_math.next_prime(3), 3)
        self.assertEqual(dobble_math.next_prime(4), 5)
        self.assertEqual(dobble_math.next_prime(6), 7)
        self.assertEqual(dobble_math.next_prime(8), 11)
        self.assertEqual(dobble_math.next_prime(10), 11)
        self.assertEqual(dobble_math.next_prime(12), 13)
        self.assertEqual(dobble_math.next_prime(14), 17)
        self.assertEqual(dobble_math.next_prime(16), 17)
        self.assertEqual(dobble_math.next_prime(18), 19)
        self.assertEqual(dobble_math.next_prime(20), 23)

        # Test some larger numbers
        self.assertEqual(dobble_math.next_prime(100), 101)
        self.assertEqual(dobble_math.next_prime(101), 101)
        self.assertEqual(dobble_math.next_prime(102), 103)

        # Test edge cases
        self.assertEqual(dobble_math.next_prime(0), 2)
        self.assertEqual(dobble_math.next_prime(-5), 2)

    def test_calculate_dobble_parameters(self):
        """Test the calculate_dobble_parameters function."""
        # Test various numbers of symbols
        # For 7 symbols, order should be 2, with 3 symbols per card
        order, symbols_per_card, total_cards = dobble_math.calculate_dobble_parameters(7)
        self.assertEqual(order, 2)
        self.assertEqual(symbols_per_card, 3)
        self.assertEqual(total_cards, 7)

        # For 13 symbols, order should be 3, with 4 symbols per card
        order, symbols_per_card, total_cards = dobble_math.calculate_dobble_parameters(13)
        self.assertEqual(order, 3)
        self.assertEqual(symbols_per_card, 4)
        self.assertEqual(total_cards, 13)

        # For 21 symbols, order should be 4, with 5 symbols per card
        order, symbols_per_card, total_cards = dobble_math.calculate_dobble_parameters(21)
        self.assertEqual(order, 5)  # 5 is the next prime after 4
        self.assertEqual(symbols_per_card, 6)
        self.assertEqual(total_cards, 31)

        # For standard Dobble (57 symbols), order should be 7, with 8 symbols per card
        order, symbols_per_card, total_cards = dobble_math.calculate_dobble_parameters(57)
        self.assertEqual(order, 7)
        self.assertEqual(symbols_per_card, 8)
        self.assertEqual(total_cards, 57)

    def test_generate_projective_plane(self):
        """Test the generate_projective_plane function."""
        # Test a small projective plane of order 2
        cards = dobble_math.generate_projective_plane(2)

        # Expected number of cards and symbols per card
        self.assertEqual(len(cards), 7)  # n²+n+1 = 2²+2+1 = 7
        self.assertEqual(len(cards[0]), 3)  # n+1 = 2+1 = 3

        # Test that each pair of cards shares exactly one symbol
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                intersection = cards[i].intersection(cards[j])
                self.assertEqual(len(intersection), 1,
                                 f"Cards {i} and {j} share {len(intersection)} symbols: {intersection}")

        # Test a larger projective plane of order 3
        cards = dobble_math.generate_projective_plane(3)

        # Expected number of cards and symbols per card
        self.assertEqual(len(cards), 13)  # n²+n+1 = 3²+3+1 = 13
        self.assertEqual(len(cards[0]), 4)  # n+1 = 3+1 = 4

        # Test that each pair of cards shares exactly one symbol
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                intersection = cards[i].intersection(cards[j])
                self.assertEqual(len(intersection), 1,
                                 f"Cards {i} and {j} share {len(intersection)} symbols: {intersection}")

        # Test that the function raises an error for non-prime orders
        with self.assertRaises(ValueError):
            dobble_math.generate_projective_plane(4)

        with self.assertRaises(ValueError):
            dobble_math.generate_projective_plane(6)

    def test_generate_dobble_cards(self):
        """Test the generate_dobble_cards function."""
        # Test with a small number of symbols (7)
        cards, total_symbols = dobble_math.generate_dobble_cards(7)

        # Check the number of cards and symbols
        self.assertEqual(total_symbols, 7)
        self.assertEqual(len(cards), 7)
        self.assertEqual(len(cards[0]), 3)

        # Test with more symbols (31)
        cards, total_symbols = dobble_math.generate_dobble_cards(31)

        # Check the number of cards and symbols
        self.assertGreaterEqual(total_symbols, 31)
        self.assertGreaterEqual(len(cards[0]), 6)  # n+1 where n>=5

        # Test with standard Dobble parameters (57 symbols)
        cards, total_symbols = dobble_math.generate_dobble_cards(57)

        # Check the number of cards and symbols
        self.assertGreaterEqual(total_symbols, 57)
        self.assertEqual(len(cards[0]), 8)  # n+1 where n=7

        # Verify the Dobble property for a subset of cards
        test_cards = cards[:20]  # Test with first 20 cards to keep test fast
        for i in range(len(test_cards)):
            for j in range(i + 1, len(test_cards)):
                # Convert to sets for intersection
                card1, card2 = set(test_cards[i]), set(test_cards[j])
                intersection = card1.intersection(card2)
                self.assertEqual(len(intersection), 1,
                                 f"Cards {i} and {j} share {len(intersection)} symbols: {intersection}")

    def test_limit_cards(self):
        """Test the limit_cards function."""
        # Generate full set of cards
        cards, _ = dobble_math.generate_dobble_cards(31)
        original_count = len(cards)

        # Limit to 10 cards
        limited_cards = dobble_math.limit_cards(cards, 10)
        self.assertEqual(len(limited_cards), 10)

        # Verify that the Dobble property still holds
        for i in range(len(limited_cards)):
            for j in range(i + 1, len(limited_cards)):
                card1, card2 = set(limited_cards[i]), set(limited_cards[j])
                intersection = card1.intersection(card2)
                self.assertEqual(len(intersection), 1,
                                 f"Cards {i} and {j} share {len(intersection)} symbols: {intersection}")

        # Test with a limit larger than the number of cards
        limited_cards = dobble_math.limit_cards(cards, original_count + 10)
        self.assertEqual(len(limited_cards), original_count)

    def test_select_symbols(self):
        """Test the select_symbols function."""
        # Generate a set of cards
        cards, _ = dobble_math.generate_dobble_cards(13)

        # Get all unique symbols used in the cards
        all_symbols = set()
        for card in cards:
            all_symbols.update(card)

        # Test with enough images
        symbol_to_image = dobble_math.select_symbols(cards, len(all_symbols))
        self.assertEqual(len(symbol_to_image), len(all_symbols))

        # Test with exact number of images
        symbol_to_image = dobble_math.select_symbols(cards, len(all_symbols))
        self.assertEqual(len(symbol_to_image), len(all_symbols))

        # Test with insufficient images
        with self.assertRaises(ValueError):
            dobble_math.select_symbols(cards, len(all_symbols) - 1)

    def test_verify_dobble_property(self):
        """Test the verify_dobble_property function."""
        # Generate a valid set of Dobble cards
        cards, _ = dobble_math.generate_dobble_cards(13)

        # This should not raise an exception
        self.assertTrue(dobble_math.verify_dobble_property(cards))

        # Create an invalid set of cards (duplicate a card)
        invalid_cards = cards.copy()
        invalid_cards.append(invalid_cards[0])

        # This should raise an AssertionError
        with self.assertRaises(AssertionError):
            dobble_math.verify_dobble_property(invalid_cards)

        # Create another invalid set where two cards share more than one symbol
        invalid_cards = cards.copy()
        # Modify the last card to share multiple symbols with the first card
        invalid_cards[-1] = invalid_cards[0][:2] + invalid_cards[-1][2:]

        # This should raise an AssertionError
        with self.assertRaises(AssertionError):
            dobble_math.verify_dobble_property(invalid_cards)


if __name__ == '__main__':
    unittest.main()