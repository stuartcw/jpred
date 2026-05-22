#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "pillow",
#     "pandas",
# ]
# ///

import click
import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

def get_leaderboard_data(db_path):
    """Get leaderboard data from results table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read from results table
    cursor.execute("""
        SELECT rank, name, points, exact_matches, j1_score, j2_score, j3_score
        FROM results
        ORDER BY rank
    """)

    leaderboard = []
    for row in cursor.fetchall():
        rank, name, points, exact, j1, j2, j3 = row
        leaderboard.append({
            'name': name,
            'points': points,
            'exact': exact,
            'j1': j1,
            'j2': j2,
            'j3': j3
        })

    conn.close()
    return leaderboard

def create_leaderboard_image(leaderboard, output_path, year):
    """Create a PNG image of the leaderboard table."""

    # Table settings
    row_height = 30
    header_height = 60
    col_widths = [60, 400, 80, 80, 60, 60, 60]  # Rank, Name, Points, Exact, J1, J2, J3
    total_width = sum(col_widths)
    total_height = header_height + (len(leaderboard) * row_height)

    # Colors
    bg_color = (255, 255, 255)
    header_color = (41, 128, 185)
    text_color = (0, 0, 0)
    header_text_color = (255, 255, 255)
    alt_row_color = (236, 240, 241)
    border_color = (189, 195, 199)

    # Create image
    img = Image.new('RGB', (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        cell_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        cell_font = ImageFont.load_default()

    # Draw header
    draw.rectangle([0, 0, total_width, header_height], fill=header_color)

    # Draw title
    title = f"JPred {year} - All Entrants"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((total_width - title_width) // 2, 5), title, fill=header_text_color, font=title_font)

    # Draw column headers
    headers = ['Rank', 'Name', 'Points', 'Exact', 'J1', 'J2', 'J3']
    x = 0
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        bbox = draw.textbbox((0, 0), header, font=header_font)
        text_width = bbox[2] - bbox[0]
        text_x = x + (width - text_width) // 2
        draw.text((text_x, 30), header, fill=header_text_color, font=header_font)
        x += width

    # Draw rows
    y = header_height
    for rank, entry in enumerate(leaderboard, 1):
        # Alternate row colors
        if rank % 2 == 0:
            draw.rectangle([0, y, total_width, y + row_height], fill=alt_row_color)

        # Draw cells
        cells = [
            str(rank),
            entry['name'][:50],  # Truncate long names
            str(entry['points']),
            str(entry['exact']),
            str(entry['j1']),
            str(entry['j2']),
            str(entry['j3'])
        ]

        x = 0
        for i, (cell, width) in enumerate(zip(cells, col_widths)):
            bbox = draw.textbbox((0, 0), cell, font=cell_font)
            text_width = bbox[2] - bbox[0]

            # Left align name, center align others
            if i == 1:
                text_x = x + 10
            else:
                text_x = x + (width - text_width) // 2

            draw.text((text_x, y + 8), cell, fill=text_color, font=cell_font)

            # Draw vertical borders
            draw.line([(x + width, header_height), (x + width, total_height)], fill=border_color)
            x += width

        # Draw horizontal border
        draw.line([(0, y + row_height), (total_width, y + row_height)], fill=border_color)
        y += row_height

    # Draw outer border
    draw.rectangle([0, 0, total_width - 1, total_height - 1], outline=border_color, width=2)

    # Save image
    img.save(output_path)
    print(f"Leaderboard image saved to {output_path}")

@click.command()
@click.option('--output', '-o', default='docs/leaderboard.png', help='Output PNG file path')
def main(output):
    """Generate a PNG image of the JPred leaderboard table."""

    # Auto-detect year from tables directory structure
    tables_dir = Path('tables')
    year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]

    if not year_dirs:
        print("Error: No year directory found in tables/")
        exit(1)

    year = year_dirs[0].name
    db_path = f'jpred_{year}.db'

    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found. Run make_all.sh first.")
        exit(1)

    print(f"Generating leaderboard for year {year}...")
    leaderboard = get_leaderboard_data(db_path)

    print(f"Found {len(leaderboard)} entrants")
    create_leaderboard_image(leaderboard, output, year)

if __name__ == '__main__':
    main()
