#!/usr/bin/env python3

import unittest
import sys
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app


class TestApp(unittest.TestCase):
    """Test the Flask application functionality."""

    def setUp(self):
        """Set up test case."""
        # Configure the app for testing
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

        # Create temporary directories for test data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

        # Create a temporary icons directory
        self.icons_dir = os.path.join(self.test_dir, 'icons')
        os.makedirs(self.icons_dir, exist_ok=True)

        # Create a temporary exports directory
        self.exports_dir = os.path.join(self.test_dir, 'exports')
        os.makedirs(self.exports_dir, exist_ok=True)

        # Patch the app paths to use our test directories
        self.original_icons_folder = app.ICONS_FOLDER
        self.original_exports_folder = app.EXPORTS_FOLDER
        app.ICONS_FOLDER = self.icons_dir
        app.EXPORTS_FOLDER = self.exports_dir

        # Create some test icons
        self.create_test_icons()

    def tearDown(self):
        """Clean up after test case."""
        # Restore original app paths
        app.ICONS_FOLDER = self.original_icons_folder
        app.EXPORTS_FOLDER = self.original_exports_folder

        # Clean up temporary directory
        self.temp_dir.cleanup()

    def create_test_icons(self):
        """Create test icons for testing."""
        # Create a test icon set directory
        self.test_set_dir = os.path.join(self.icons_dir, 'test_set')
        os.makedirs(self.test_set_dir, exist_ok=True)

        # Create some test icons
        for i in range(10):
            # Create a simple colored image with a unique color
            color = (25 * (i % 10), 25 * (i // 3), 255 - 25 * i, 255)
            img = Image.new('RGBA', (50, 50), color=color)
            img.save(os.path.join(self.test_set_dir, f'icon_{i}.png'))

        # Create metadata file
        metadata = {
            'id': 'test_set',
            'name': 'Test Icon Set',
            'count': 10,
            'created_at': '2023-01-01T00:00:00'
        }

        with open(os.path.join(self.test_set_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

    def create_test_export(self):
        """Create a test export for testing."""
        # Create a test export JSON file
        job_id = 'test_job'
        job_data = {
            'id': job_id,
            'created_at': '2023-01-01T00:00:00',
            'n_symbols': 7,
            'n_cards': 7,
            'symbols_per_card': 3,
            'icon_set': 'user:test_set',
            'card_size': 'A4',
            'layout': 'circle',
            'pdf_path': os.path.join(self.exports_dir, f'{job_id}.pdf'),
            'png_paths': [
                os.path.join(self.exports_dir, f'{job_id}_card_0.png'),
                os.path.join(self.exports_dir, f'{job_id}_card_1.png'),
                os.path.join(self.exports_dir, f'{job_id}_card_2.png')
            ],
            'download_format': 'pdf'
        }

        with open(os.path.join(self.exports_dir, f'{job_id}.json'), 'w') as f:
            json.dump(job_data, f)

        # Create a dummy PDF file
        with open(job_data['pdf_path'], 'wb') as f:
            f.write(b'dummy pdf data')

        # Create dummy PNG files
        for png_path in job_data['png_paths']:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(png_path)

        return job_id, job_data

    def test_index_route(self):
        """Test the index route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dobble Card Generator', response.data)

    def test_settings_route(self):
        """Test the settings route."""
        response = self.app.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Settings', response.data)

    def test_preview_route(self):
        """Test the preview route."""
        # Create a test export
        job_id, _ = self.create_test_export()

        # Test the preview route
        response = self.app.get(f'/preview/{job_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Card Preview', response.data)

        # Test with non-existent job ID
        response = self.app.get('/preview/nonexistent')
        self.assertEqual(response.status_code, 302)  # Should redirect

    @patch('app.dobble_math.generate_dobble_cards')
    @patch('app.image_processor.process_icons')
    @patch('app.card_generator.generate_cards')
    def test_generate_cards_api(self, mock_generate_cards, mock_process_icons, mock_generate_dobble_cards):
        """Test the /api/generate endpoint."""
        # Set up mocks
        mock_generate_dobble_cards.return_value = ([[0, 1, 2], [0, 3, 4], [1, 3, 5]], 7)
        mock_process_icons.return_value = {i: MagicMock() for i in range(7)}
        mock_generate_cards.return_value = ('test.pdf', ['test_card_0.png', 'test_card_1.png', 'test_card_2.png'])

        # Test with valid parameters
        response = self.app.post('/api/generate', data={
            'icon_set': 'user:test_set',
            'symbols_per_card': '3',
            'n_cards': '0',
            'card_size': 'A4',
            'layout': 'circle',
            'format': 'pdf'
        })

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('job_id', data)
        self.assertIn('preview_url', data)

        # Test with missing icon set
        response = self.app.post('/api/generate', data={
            'symbols_per_card': '3',
            'n_cards': '0',
            'card_size': 'A4',
            'layout': 'circle',
            'format': 'pdf'
        })

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_upload_icons_api(self):
        """Test the /api/upload_icons endpoint."""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # Test with valid parameters
        response = self.app.post('/api/upload_icons', data={
            'set_name': 'Test Upload',
            'icons': (img_buffer, 'icon.png')
        }, content_type='multipart/form-data')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('set_id', data)

        # Verify the icon set was created
        set_id = data['set_id']
        set_dir = os.path.join(self.icons_dir, set_id)
        self.assertTrue(os.path.exists(set_dir))
        self.assertTrue(os.path.exists(os.path.join(set_dir, 'metadata.json')))

        # Test with missing set name
        response = self.app.post('/api/upload_icons', data={
            'icons': (img_buffer, 'icon.png')
        }, content_type='multipart/form-data')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_delete_icon_set_api(self):
        """Test the /api/delete_icon_set endpoint."""
        # Test with valid parameters
        response = self.app.post('/api/delete_icon_set', data={
            'icon_set': 'user:test_set'
        })

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify the icon set was deleted
        self.assertFalse(os.path.exists(self.test_set_dir))

        # Test with invalid icon set
        response = self.app.post('/api/delete_icon_set', data={
            'icon_set': 'default:test_set'
        })

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_delete_export_api(self):
        """Test the /api/delete_export endpoint."""
        # Create a test export
        job_id, job_data = self.create_test_export()

        # Test with valid parameters
        response = self.app.post('/api/delete_export', data={
            'job_id': job_id
        })

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify the export was deleted
        self.assertFalse(os.path.exists(os.path.join(self.exports_dir, f'{job_id}.json')))
        self.assertFalse(os.path.exists(job_data['pdf_path']))
        for png_path in job_data['png_paths']:
            self.assertFalse(os.path.exists(png_path))

        # Test with invalid job ID
        response = self.app.post('/api/delete_export', data={
            'job_id': 'nonexistent'
        })

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')


if __name__ == '__main__':
    unittest.main()