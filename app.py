#!/usr/bin/env python3

import os
import logging
import uuid
import shutil
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

import dobble_math
import card_generator
import image_processor

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/app/logs/app.log'), logging.StreamHandler()]
)
logger = logging.getLogger('dobble_generator')

# App constants
UPLOAD_FOLDER = '/app/uploads'
ICONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'icons')
EXPORTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'exports')
DEFAULT_ICONS_FOLDER = '/app/static/default_icons'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

# Ensure directories exist
os.makedirs(ICONS_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    # Get default icon sets info
    icon_sets = get_default_icon_sets()

    # Get user's uploaded icon sets
    user_icon_sets = get_user_icon_sets()

    # Get recent exports
    recent_exports = get_recent_exports(5)

    return render_template(
        'index.html',
        icon_sets=icon_sets,
        user_icon_sets=user_icon_sets,
        recent_exports=recent_exports
    )


@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@app.route('/preview/<job_id>')
def preview(job_id):
    """Render the preview page for a specific job."""
    job_data_path = os.path.join(EXPORTS_FOLDER, f"{job_id}.json")

    if not os.path.exists(job_data_path):
        return redirect(url_for('index'))

    try:
        with open(job_data_path, 'r') as f:
            job_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading job data: {e}")
        return redirect(url_for('index'))

    return render_template('preview.html', job=job_data)


@app.route('/api/generate', methods=['POST'])
def generate_cards():
    """Generate Dobble cards based on the request parameters."""
    try:
        # Get parameters from the request
        n_symbols = int(request.form.get('n_symbols', 31))  # Default: minimum for 7 symbols per card
        n_cards = int(request.form.get('n_cards', 0))  # 0 means maximum possible
        symbols_per_card = int(request.form.get('symbols_per_card', 0))  # 0 means auto-calculate
        icon_set = request.form.get('icon_set', '')
        card_size = request.form.get('card_size', 'A4')  # A4, A5, etc.
        layout = request.form.get('layout', 'circle')  # circle, grid
        download_format = request.form.get('format', 'pdf')  # pdf, png, both

        # Check if icon set is specified
        if not icon_set:
            return jsonify({'success': False, 'message': 'No icon set specified'}), 400

        # Split icon set type and ID
        icon_set_parts = icon_set.split(':')
        if len(icon_set_parts) != 2:
            return jsonify({'success': False, 'message': 'Invalid icon set format'}), 400

        icon_set_type, icon_set_id = icon_set_parts

        # Get the icon files based on the type
        if icon_set_type == 'default':
            icon_dir = os.path.join(DEFAULT_ICONS_FOLDER, icon_set_id)
        else:  # user
            icon_dir = os.path.join(ICONS_FOLDER, icon_set_id)

        if not os.path.exists(icon_dir):
            return jsonify({'success': False, 'message': 'Icon set not found'}), 404

        # Get all image files from the icon directory
        icon_files = []
        for filename in os.listdir(icon_dir):
            if allowed_file(filename):
                icon_files.append(os.path.join(icon_dir, filename))

        available_symbols = len(icon_files)
        if available_symbols == 0:
            return jsonify({'success': False, 'message': 'No valid icons found in the set'}), 400

        # If symbols_per_card is specified, calculate minimum n_symbols required
        if symbols_per_card > 0:
            # For symbols_per_card = n+1, we need n²+n+1 different symbols
            order = symbols_per_card - 1
            n_symbols = order * order + order + 1

        # Generate Dobble cards
        cards, total_symbols_needed = dobble_math.generate_dobble_cards(n_symbols)

        # Check if we have enough icons
        if total_symbols_needed > available_symbols:
            return jsonify({
                'success': False,
                'message': f'Not enough icons: need {total_symbols_needed}, have {available_symbols}'
            }), 400

        # Limit the number of cards if requested
        if n_cards > 0 and n_cards < len(cards):
            cards = dobble_math.limit_cards(cards, n_cards)

        # Map card symbols to actual icons
        symbol_to_icon = dobble_math.select_symbols(cards, available_symbols)

        # Now map the symbols to actual icon files
        symbol_to_file = {symbol: icon_files[icon_idx] for symbol, icon_idx in symbol_to_icon.items()}

        # Generate a job ID
        job_id = str(uuid.uuid4())

        # Prepare the icon images
        processed_icons = image_processor.process_icons(symbol_to_file)

        # Generate the card layout
        pdf_path, png_paths = card_generator.generate_cards(
            job_id,
            cards,
            processed_icons,
            EXPORTS_FOLDER,
            card_size=card_size,
            layout=layout
        )

        # Save job information for later reference
        job_data = {
            'id': job_id,
            'created_at': datetime.now().isoformat(),
            'n_symbols': n_symbols,
            'n_cards': len(cards),
            'symbols_per_card': len(cards[0]),
            'icon_set': icon_set,
            'card_size': card_size,
            'layout': layout,
            'pdf_path': pdf_path,
            'png_paths': png_paths,
            'download_format': download_format
        }

        with open(os.path.join(EXPORTS_FOLDER, f"{job_id}.json"), 'w') as f:
            json.dump(job_data, f)

        # Return success with job ID
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Generated {len(cards)} cards with {len(cards[0])} symbols per card',
            'preview_url': url_for('preview', job_id=job_id)
        })

    except Exception as e:
        logger.error(f"Error generating cards: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/upload_icons', methods=['POST'])
def upload_icons():
    """Upload a set of icons."""
    try:
        # Check if name is provided
        set_name = request.form.get('set_name', '')
        if not set_name:
            return jsonify({'success': False, 'message': 'Set name is required'}), 400

        # Create a clean set ID from the name
        set_id = secure_filename(set_name).lower()
        if not set_id:
            set_id = str(uuid.uuid4())

        # Create a directory for the icon set
        icon_set_dir = os.path.join(ICONS_FOLDER, set_id)
        os.makedirs(icon_set_dir, exist_ok=True)

        # Check if files were uploaded
        if 'icons' not in request.files:
            return jsonify({'success': False, 'message': 'No files uploaded'}), 400

        files = request.files.getlist('icons')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'message': 'No files selected'}), 400

        # Process each uploaded file
        count = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(icon_set_dir, filename))
                count += 1

        # Save set metadata
        with open(os.path.join(icon_set_dir, 'metadata.json'), 'w') as f:
            json.dump({
                'id': set_id,
                'name': set_name,
                'count': count,
                'created_at': datetime.now().isoformat()
            }, f)

        return jsonify({
            'success': True,
            'message': f'Uploaded {count} icons to set "{set_name}"',
            'set_id': set_id
        })

    except Exception as e:
        logger.error(f"Error uploading icons: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/delete_icon_set', methods=['POST'])
def delete_icon_set():
    """Delete a user's icon set."""
    try:
        # Get the icon set ID
        icon_set = request.form.get('icon_set', '')
        if not icon_set:
            return jsonify({'success': False, 'message': 'No icon set specified'}), 400

        # Split icon set type and ID
        icon_set_parts = icon_set.split(':')
        if len(icon_set_parts) != 2 or icon_set_parts[0] != 'user':
            return jsonify({'success': False, 'message': 'Cannot delete default icon sets'}), 400

        icon_set_id = icon_set_parts[1]
        icon_set_dir = os.path.join(ICONS_FOLDER, icon_set_id)

        # Check if the directory exists
        if not os.path.exists(icon_set_dir):
            return jsonify({'success': False, 'message': 'Icon set not found'}), 404

        # Delete the directory and all its contents
        shutil.rmtree(icon_set_dir)

        return jsonify({
            'success': True,
            'message': f'Deleted icon set "{icon_set_id}"'
        })

    except Exception as e:
        logger.error(f"Error deleting icon set: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/delete_export', methods=['POST'])
def delete_export():
    """Delete an export."""
    try:
        # Get the job ID
        job_id = request.form.get('job_id', '')
        if not job_id:
            return jsonify({'success': False, 'message': 'No job ID specified'}), 400

        # Check if the job exists
        job_data_path = os.path.join(EXPORTS_FOLDER, f"{job_id}.json")
        if not os.path.exists(job_data_path):
            return jsonify({'success': False, 'message': 'Export not found'}), 404

        # Load job data to get associated files
        with open(job_data_path, 'r') as f:
            job_data = json.load(f)

        # Delete PDF file
        pdf_path = job_data.get('pdf_path', '')
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

        # Delete PNG files
        png_paths = job_data.get('png_paths', [])
        for png_path in png_paths:
            if os.path.exists(png_path):
                os.remove(png_path)

        # Delete job data file
        os.remove(job_data_path)

        return jsonify({
            'success': True,
            'message': f'Deleted export "{job_id}"'
        })

    except Exception as e:
        logger.error(f"Error deleting export: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/exports/<filename>')
def serve_export(filename):
    """Serve an exported file."""
    return send_from_directory(EXPORTS_FOLDER, filename)


@app.route('/health')
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


def get_default_icon_sets():
    """Get information about available default icon sets."""
    icon_sets = []

    # Check if default icons directory exists
    if not os.path.exists(DEFAULT_ICONS_FOLDER):
        return icon_sets

    # Iterate through each subdirectory
    for set_id in os.listdir(DEFAULT_ICONS_FOLDER):
        set_dir = os.path.join(DEFAULT_ICONS_FOLDER, set_id)
        if os.path.isdir(set_dir):
            # Count valid icon files
            count = 0
            sample_icon = None
            for filename in os.listdir(set_dir):
                if allowed_file(filename):
                    count += 1
                    if not sample_icon:
                        sample_icon = f"/static/default_icons/{set_id}/{filename}"

            # Load metadata if available
            metadata_path = os.path.join(set_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    set_name = metadata.get('name', set_id)
                except Exception:
                    set_name = set_id.replace('_', ' ').title()
            else:
                set_name = set_id.replace('_', ' ').title()

            icon_sets.append({
                'id': f"default:{set_id}",
                'name': set_name,
                'count': count,
                'sample_icon': sample_icon
            })

    return icon_sets


def get_user_icon_sets():
    """Get information about user-uploaded icon sets."""
    icon_sets = []

    # Check if user icons directory exists
    if not os.path.exists(ICONS_FOLDER):
        return icon_sets

    # Iterate through each subdirectory
    for set_id in os.listdir(ICONS_FOLDER):
        set_dir = os.path.join(ICONS_FOLDER, set_id)
        if os.path.isdir(set_dir):
            # Count valid icon files
            count = 0
            sample_icon = None
            for filename in os.listdir(set_dir):
                if allowed_file(filename):
                    count += 1
                    if not sample_icon:
                        sample_icon = f"/uploads/icons/{set_id}/{filename}"

            # Load metadata if available
            metadata_path = os.path.join(set_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    set_name = metadata.get('name', set_id)
                except Exception:
                    set_name = set_id.replace('_', ' ').title()
            else:
                set_name = set_id.replace('_', ' ').title()

            icon_sets.append({
                'id': f"user:{set_id}",
                'name': set_name,
                'count': count,
                'sample_icon': sample_icon
            })

    return icon_sets


def get_recent_exports(limit=5):
    """Get information about recent exports."""
    exports = []

    # Check if exports directory exists
    if not os.path.exists(EXPORTS_FOLDER):
        return exports

    # Get all JSON files with job data
    json_files = []
    for filename in os.listdir(EXPORTS_FOLDER):
        if filename.endswith('.json'):
            json_path = os.path.join(EXPORTS_FOLDER, filename)
            try:
                with open(json_path, 'r') as f:
                    job_data = json.load(f)
                job_data['created_at_dt'] = datetime.fromisoformat(job_data['created_at'])
                json_files.append(job_data)
            except Exception as e:
                logger.error(f"Error loading job data from {json_path}: {e}")

    # Sort by creation time, newest first
    json_files.sort(key=lambda x: x['created_at_dt'], reverse=True)

    # Get the most recent ones
    for job in json_files[:limit]:
        # Check if PDF file exists
        pdf_exists = os.path.exists(job.get('pdf_path', ''))

        exports.append({
            'id': job['id'],
            'created_at': job['created_at_dt'].strftime('%Y-%m-%d %H:%M'),
            'n_cards': job.get('n_cards', 0),
            'symbols_per_card': job.get('symbols_per_card', 0),
            'pdf_path': os.path.basename(job.get('pdf_path', '')),
            'pdf_exists': pdf_exists,
            'preview_url': url_for('preview', job_id=job['id'])
        })

    return exports


@app.route('/api/icons/<path:filename>')
def serve_icon(filename):
    """Serve a user-uploaded icon."""
    return send_from_directory(UPLOAD_FOLDER, f"icons/{filename}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8920, debug=True)