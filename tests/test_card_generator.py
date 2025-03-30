#!/usr/bin/env python3

import math
import os
import sys
import tempfile
import unittest
import uuid

from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import card_generator


class TestCardGenerator(unittest.TestCase):
    """Test the card generator functions."""

    def setUp(self):
        """Set up test case with sample images."""
        # Create a temporary directory for test output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_output_dir = self.temp_dir.name

        # Create test images for symbols
        self.test_images = {}
        for i in range(10):
            # Create a simple colored image with a unique color
            color = (25 * (i % 10), 25 * (i // 3), 255 - 25 * i, 255)
            img = Image.new('RGBA', (50, 50), color=color)
            self.test_images[i] = img

        # Create some test cards (lists of symbol indices)
        self.test_cards = [
            [0, 1, 2, 3],  # Card with 4 symbols
            [0, 4, 5, 6],  # Card with 4 symbols, sharing 1 with first card
            [1, 4, 7, 8],  # Card with 4 symbols, sharing 1 with each previous card
        ]

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_generate_circular_layout(self):
        """Test generating a circular layout."""
        # Test with various numbers of symbols
        for n_symbols in range(3, 10):
            layout = card_generator.generate_circular_layout(n_symbols)

            # We should have the right number of positions
            self.assertEqual(len(layout), n_symbols)

            # Each position should be a tuple of (x, y, scale)
            for pos in layout:
                self.assertEqual(len(pos), 3)
                x, y, scale = pos

                # Coordinates should be in [0, 1] range
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, 1)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(y, 1)

                # Scale should be positive
                self.assertGreater(scale, 0)

        # Test predefined layouts for common symbol counts
        common_counts = [3, 4, 5, 6, 7, 8]
        for count in common_counts:
            layout = card_generator.generate_circular_layout(count)
            self.assertEqual(len(layout), count)

            # Make sure positions are well-distributed
            center_positions = [pos for pos in layout if (0.4 <= pos[0] <= 0.6 and 0.4 <= pos[1] <= 0.6)]
            if count > 2:  # For counts > 2, expect at most one symbol at center
                self.assertLessEqual(len(center_positions), 1)

    def test_generate_grid_layout(self):
        """Test generating a grid layout."""
        # Test with various numbers of symbols
        for n_symbols in range(3, 10):
            layout = card_generator.generate_grid_layout(n_symbols)

            # We should have the right number of positions
            self.assertEqual(len(layout), n_symbols)

            # Each position should be a tuple of (x, y, scale)
            for pos in layout:
                self.assertEqual(len(pos), 3)
                x, y, scale = pos

                # Coordinates should be in [0, 1] range
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, 1)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(y, 1)

                # Scale should be positive
                self.assertGreater(scale, 0)

        # Test specific grid properties
        for n_symbols in [4, 9, 16]:  # Perfect squares
            layout = card_generator.generate_grid_layout(n_symbols)

            # Check that layout has expected number of rows and columns
            rows = len(set(round(pos[1] * 100) for pos in layout))  # Round to avoid floating point issues
            cols = len(set(round(pos[0] * 100) for pos in layout))

            grid_size = int(math.sqrt(n_symbols))
            self.assertLessEqual(rows, grid_size)
            self.assertLessEqual(cols, grid_size)

    def test_create_circular_card(self):
        """Test creating a circular card."""
        # Create a circular card with the first test card
        card_img = card_generator.create_circular_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400)
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with custom colors
        card_img = card_generator.create_circular_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            background_color=(200, 200, 200),
            border_color=(100, 100, 100)
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with custom border width
        card_img = card_generator.create_circular_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            border_width=20
        )
        self.assertEqual(card_img.size, (400, 400))

        # Test with grid layout
        card_img = card_generator.create_circular_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            layout='grid'
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test error handling with missing symbol
        bad_symbols = self.test_cards[0].copy()
        bad_symbols.append(99)  # Add a symbol that doesn't exist
        card_img = card_generator.create_circular_card(
            bad_symbols,
            self.test_images,
            size=(400, 400)
        )

        # Should still create a card
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with non-square dimensions
        card_img = card_generator.create_circular_card(
            self.test_cards[0],
            self.test_images,
            size=(600, 400)
        )
        self.assertEqual(card_img.size, (600, 400))

    def test_create_square_card(self):
        """Test creating a square card."""
        # Create a square card with the first test card
        card_img = card_generator.create_square_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400)
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with custom colors
        card_img = card_generator.create_square_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            background_color=(200, 200, 200),
            border_color=(100, 100, 100)
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with custom border width
        card_img = card_generator.create_square_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            border_width=20
        )
        self.assertEqual(card_img.size, (400, 400))

        # Test with grid layout
        card_img = card_generator.create_square_card(
            self.test_cards[0],
            self.test_images,
            size=(400, 400),
            layout='grid'
        )

        # Check that the card has the right size and mode
        self.assertEqual(card_img.size, (400, 400))
        self.assertEqual(card_img.mode, 'RGBA')

        # Test with non-square dimensions
        card_img = card_generator.create_square_card(
            self.test_cards[0],
            self.test_images,
            size=(600, 400)
        )
        self.assertEqual(card_img.size, (600, 400))

        # Test error handling with missing symbol
        bad_symbols = self.test_cards[0].copy()
        bad_symbols.append(99)  # Add a symbol that doesn't exist
        card_img = card_generator.create_square_card(
            bad_symbols,
            self.test_images,
            size=(400, 400)
        )
        self.assertEqual(card_img.size, (400, 400))

    def test_create_cards_pdf(self):
        """Test creating a PDF with multiple cards."""
        # Create a unique job ID for this test
        job_id = f"test-{uuid.uuid4()}"

        # Create a PDF with the test cards
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=1
        )

        # Check that the PDF file exists
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith(".pdf"))

        # Check the PDF path format
        self.assertIn(job_id, pdf_path)

        # Test with different card shapes and page layouts
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            card_shape='square',
            card_size='A5',
            layout='grid',
            cards_per_page=2
        )

        # Check that the PDF file exists
        self.assertTrue(os.path.exists(pdf_path))

        # Test with 4 cards per page
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=4
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test with 9 cards per page
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=9
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test invalid cards_per_page (should default to 1)
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=7  # Not a valid option
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test with invalid card size (should default to A4)
        pdf_path = card_generator.create_cards_pdf(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            card_size='INVALID'
        )
        self.assertTrue(os.path.exists(pdf_path))

    def test_generate_cards(self):
        """Test generating Dobble cards with PDF and PNG exports."""
        # Create a unique job ID for this test
        job_id = f"test-{uuid.uuid4()}"

        # Generate cards with both PDF and PNG exports
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            export_png=True
        )

        # Check that the PDF file exists
        self.assertTrue(os.path.exists(pdf_path))

        # Check that we have the right number of PNG files
        self.assertEqual(len(png_paths), len(self.test_cards))

        # Check that all PNG files exist
        for png_path in png_paths:
            self.assertTrue(os.path.exists(png_path))
            self.assertTrue(png_path.endswith(".png"))
            self.assertIn(job_id, png_path)

        # Test with square cards and no PNG export
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            card_shape='square',
            export_png=False
        )

        # Check that the PDF file exists
        self.assertTrue(os.path.exists(pdf_path))

        # Check that no PNG files were generated
        self.assertEqual(len(png_paths), 0)

        # Test with different card size
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            card_size='A5'
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test with grid layout
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            layout='grid'
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test with custom cards_per_page
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            self.test_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=4
        )
        self.assertTrue(os.path.exists(pdf_path))

        # Test with larger number of cards
        many_cards = []
        for i in range(10):
            many_cards.append([i] + [j for j in range(10, 14)])

        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            many_cards,
            self.test_images,
            self.test_output_dir,
            cards_per_page=9
        )
        self.assertTrue(os.path.exists(pdf_path))
        self.assertEqual(len(png_paths), 0)  # No PNGs by default

        # Test with PNG export for many cards
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            many_cards,
            self.test_images,
            self.test_output_dir,
            export_png=True
        )
        self.assertEqual(len(png_paths), len(many_cards))


if __name__ == '__main__':
    unittest.main()