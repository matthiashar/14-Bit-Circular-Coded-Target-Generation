#!/usr/bin/env python3

'''
Generate printable PDF of circular coded photogrammetry targets described by
(expired) patent DE19733466A1.

Matthew Petroff <https://mpetroff.net>, 2018
Matthias Hardner, 2024

This script is released into the public domain using the CC0 1.0 Public
Domain Dedication: https://creativecommons.org/publicdomain/zero/1.0/
'''

import subprocess   # Used to run external commands
import os.path      # Used to manipulate file paths
import sys
import numpy as np  # Used for mathematical operations
import find_codes   # Custom module for generating binary codes

INKSCAPE_EXECUTABLE = 'C://Program Files//Inkscape//bin//inkscape'
BITS = 14
CODES = find_codes.generate_codes(BITS)   # Codes for targets


class SvgPage:
    def __init__(self, width = 210, height = 298, unit = 'mm', margin = 5, background_margin = 5, background_color = '#fff'):
        self.__width = width
        self.__height = height
        self.__unit = unit
        self.__margin = margin
        self.__background_margin = background_margin
        self.__background_color = background_color

        # Create svg page
        self.__svg = '<svg xmlns="http://www.w3.org/2000/svg" width="{w}{u}" ' \
                     'height="{h}{u}" version="1.1" viewBox="0 0 {w} {h}">\n'.format(
            w=self.__width, h=self.__height, u=self.__unit)

        # Create background rect
        self.__svg += '<rect x="{}" y="{}" width="{}" height="{}" fill="{}"/>'.format(
            self.__background_margin, self.__background_margin,
            self.__width - background_margin * 2, self.__height - self.__background_margin * 2, self.__background_color)

    def get_width(self):
        return self.__width

    def get_height(self):
        return self.__height

    def get_margin(self):
        return self.__margin

    def add_circle(self, x, y, radius, color = "#000000"):
        self.__svg += '<circle fill="{}" cx="{}" cy="{}" r="{}"/>\n'.format(color, x, y, radius)

    def add_target(self, x, y, radius, code, code_num, first_segment, color = "#000000"):
        # Define a white circle at the center of the target
        self.add_circle(x, y, radius, color)
        #out = '<circle fill="{}" cx="{}" cy="{}" r="{}"/>\n'.format(MARKER_COLOR, x_center,  y_center, dot_radius)

        # Define the lines forming the outer shape of the target
        self.__svg += '<g stroke="{}" stroke-width="{}" fill="none">\n'.format(color, radius)
        for i in range(BITS):
            if (1 << (BITS - 1 - i)) & code:
                x_start = np.cos(np.deg2rad(360 / BITS * i)) * radius * 2.5
                y_start = np.sin(np.deg2rad(360 / BITS * i)) * radius * 2.5
                x_end = np.cos(np.deg2rad(360 / BITS * (i + 1))) \
                        * radius * 2.5 - x_start
                y_end = np.sin(np.deg2rad(360 / BITS * (i + 1))) \
                        * radius * 2.5 - y_start
                x_start += x
                y_start += y
                # Define a line segment in the SVG path element
                # The path element is used to define a shape as a series of lines, curves and arcs
                # https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
                self.__svg += '<path d="m{} {}a{} {} 0 0 1 {} {}"' \
                              ' {}/>\n'.format(x_start, y_start, radius * 2.5, \
                                               radius * 2.5, x_end, y_end, \
                                               'id="first"' if first_segment else '')
                first_segment = False
        self.__svg += '</g>\n'
        self.__svg += '<text x="{}" y="{}" font-size="{}" alignment-base="bottom" ' \
                      'font-family="Source Sans Pro, sans-serif" fill="{}">{}' \
                      '</text>'.format(x - radius * 3, y + radius * 3, radius / 2, color, code_num + 1)

    def savePDF(self, filename, path):
        # Write SVG file
        svg_temp = self.__svg + '</svg>'
        svg_filename = os.path.join(path, 'sheet.svg')
        with open(svg_filename, 'w') as out_file:
            out_file.write(svg_temp)

        # Use Inkscape to convert SVG to PDF
        result_1 = subprocess.run([INKSCAPE_EXECUTABLE, '-g', '--without-gui', '--select=first',
                        '--actions', 'EditSelectSameObjectType',
                        '--actions', 'StrokeToPath',
                        '--actions', 'SelectionUnion',
                        '--actions', 'FileSave',
                        '--actions', 'FileQuit', svg_filename])

        result_2 = subprocess.run(
            [INKSCAPE_EXECUTABLE, '--export-filename=' + filename, svg_filename])

def create_sheet_grid(diameter, code_index, rows, cols, filename, path):
    # Create sheet
    svg_page = SvgPage(margin=10)

    width = svg_page.get_width()
    height = svg_page.get_height()
    margin = svg_page.get_margin()

    target_size = diameter * 3
    x_spacing = (width - margin * 2 - target_size) / (cols - 1)
    y_spacing = (height - margin * 2 - target_size) / (rows - 1)

    # Add coded markers
    for i in range(rows):
        for j in range(cols):
            num = code_index + i * cols + j
            if num < len(CODES):
                svg_page.add_target(margin + target_size / 2 + j * x_spacing,
                                    margin + target_size / 2 + i * y_spacing,
                                    diameter / 2, CODES[num], num, True)

    # save pdf
    svg_page.savePDF(filename, path)

def create_sheet_a(diameter, code_index, filename, path):
    # Create sheet
    svg_page = SvgPage()

    width = svg_page.get_width()
    height = svg_page.get_height()
    margin = svg_page.get_margin()

    target_size = diameter * 3
    x_spacing = (width - margin * 2 - target_size)
    y_spacing = (height - margin * 2 - target_size) / 3

    # Add coded markers
    svg_page.add_target(width/4 , height/4, diameter / 2, CODES[code_index], code_index, True)

    svg_page.add_target(width/4*3, height/4*3, diameter / 2, CODES[code_index+1], code_index+1, False)

    # Add uncoded markers in the corners
    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 0 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 1 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 2 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 3 * y_spacing,
                        diameter / 2)

    # save pdf
    svg_page.savePDF(filename, path)

def create_sheet_b(diameter, code_index, filename, path):
    # Create sheet
    svg_page = SvgPage()

    width = svg_page.get_width()
    height = svg_page.get_height()
    margin = svg_page.get_margin()

    target_size = diameter * 3
    x_spacing = (width - margin * 2 - target_size)
    y_spacing = (height - margin * 2 - target_size) / 3

    # Change location of coded marker depending on code id
    col = 1
    row = 2
    coded_x = width / 4
    coded_y = height / 4
    if code_index % 2 == 0:
        col = 0
        row = 0
        coded_x *= 3
        coded_y *= 3

    # Add coded marker
    svg_page.add_target(coded_x, coded_y , diameter / 2, CODES[code_index], code_index, True)

    svg_page.add_circle(margin + target_size / 2 + col * x_spacing,
                        margin + target_size / 2 + row * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + col * x_spacing,
                        margin + target_size / 2 + (row + 1) * y_spacing,
                        diameter / 2)

    # Add uncoded markers in the corners
    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 0 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 1 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 2 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 3 * y_spacing,
                        diameter / 2)


    # save pdf
    svg_page.savePDF(filename, path)

def create_sheet_c(diameter, code_index, filename, path):
    # Create sheet
    svg_page = SvgPage()

    width = svg_page.get_width()
    height = svg_page.get_height()
    margin = svg_page.get_margin()

    target_size = diameter * 3
    x_spacing = (width - margin * 2 - target_size)
    y_spacing = (height - margin * 2 - target_size) / 2

    # Add coded markers
    svg_page.add_target(width/2 , height/2, diameter / 2, CODES[code_index], code_index, True)

    # Add uncoded markers in the corners
    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 0 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 0 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 0 * x_spacing,
                        margin + target_size / 2 + 2 * y_spacing,
                        diameter / 2)

    svg_page.add_circle(margin + target_size / 2 + 1 * x_spacing,
                        margin + target_size / 2 + 2 * y_spacing,
                        diameter / 2)

    # save pdf
    svg_page.savePDF(filename, path)


def main(argv):
    # Create sheets of targets in temporary directory
    dir = argv[1]

    # Create a grid of coded markers
    for n in range(0, 8*2, 8):
        pdf_filename = os.path.join(dir, str(n) + '_grid.pdf')
        create_sheet_grid(20, n, 4, 2, pdf_filename, dir)

    # Create a sheet with two coded markers
    pdf_filename = os.path.join(dir, str(16) + '_a.pdf')
    create_sheet_a(25, 16, pdf_filename ,dir )

    # Create a sheet with one coded markers
    pdf_filename = os.path.join(dir, str(18) + '_b.pdf')
    create_sheet_b(25, 18, pdf_filename, dir)

    # Create a sheet with on coded marker in the center
    pdf_filename = os.path.join(dir, str(19) + '_c.pdf')
    create_sheet_c(25, 19, pdf_filename, dir)

if __name__ == "__main__":
    main(sys.argv)
