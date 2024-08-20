"""
Package Configurations
python                    3.11.3
simpy                     4.0.1
"""

import pandas as pd
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np
# If you also want to get the image bytes as a variable, you can use BytesIO
from io import BytesIO
import random
import seaborn as sns

simmode = ''

# Define a fixed color map for the jobs
COLOR_MAP = {
    'J-0': '#3498db',  # light blue
    'J-1': '#2ecc71',  # light green
    'J-2': '#e74c3c',  # light red
    'J-3': '#f1c40f',  # yellow
    'J-4': '#9b59b6',  # purple
    'J-5': '#34495e',  # dark blue
    'J-6': '#e67e22',  # orange
    'J-7': '#1abc9c',  # turquoise
    'J-8': '#f39c12',  # dark yellow
    'J-9': '#7f8c8d'   # gray
}

def Gantt(cfg, result, num, printmode=True, writemode=False):
    df = result.iloc[0:num].copy()

    # 10 machine, converting 1~10 machine indices to 0~9
    plot_order = {}
    for i in range(10):
        plot_order['M' + str(i)] = i
    df['plot_order'] = df['Machine'].map(plot_order)
    df = df.sort_values(by='plot_order')

    # Ensure the color map uses fixed colors
    df['color'] = df['Job'].apply(lambda j: COLOR_MAP[j.split('_')[0]])

    machine_list = df['Machine'].unique()

    # TODO: 머신 열 순서대로 출력되도록.
    fig, ax = plt.subplots(1, figsize=(16 * 0.8, 9 * 0.8))
    ax.barh(df.Machine, df.Delta, left=df.Start, color=df.color, edgecolor='black')

    ##### LEGENDS #####
    legend_elements = [Patch(facecolor=COLOR_MAP[i], label=i) for i in COLOR_MAP]
    plt.legend(handles=legend_elements)
    plt.ylabel(cfg.ylabel)
    plt.xlabel(cfg.xlabel)
    plt.title(cfg.TITLE)

    ##### TICKS #####
    if printmode:
        plt.show()

    # Save the figure as an image file
    if writemode:
        fig.savefig(cfg.save_path + '/' + cfg.filename + '.png', format='png')

    # Create a BytesIO object
    image_bytes_io = BytesIO()

    # Save the figure to the BytesIO object
    fig.savefig(image_bytes_io, format='png')

    # Get the image bytes
    image_bytes = image_bytes_io.getvalue()

    return image_bytes














# # create a column with the color for each department
#
# def Gantt(cfg, result, num, printmode=True, writemode=False):
#     df = result.iloc[0:num].copy()
#
#     # 10 machine, converting 1~10 machine indices to 0~9
#     plot_order = {}
#     for i in range(10):
#         plot_order['M' + str(i)] = i
#         # plot_order['M' + str(i + 1)] = i
#     df['plot_order'] = df['Machine'].map(plot_order)
#     df = df.sort_values(by='plot_order')
#
#     c_dict = dict()
#     job_list = df['Job'].unique()
#
#     """Generating Color Hex Codes for Plotting"""
#     for i in range(len(job_list)):
#
#         rgb = random.randrange(0, 2 ** 24)
#         # Converting that number from base-10
#         # (decimal) to base-16 (hexadecimal)
#         hex_color = str(hex(rgb))[2:]
#         if len(hex_color) == 5:  # 가끔 Hex Code가 5자리로 변환되는 경우가 있음
#             hex_color = '#0' + hex_color
#         else:
#             hex_color = '#' + hex_color
#         # Quay 데이터에서는 J-0부터가 아니라 J-1부터 시작하고 있음
#         # c_dict['J-' + str(i+1)] = hex_color
#         # abz5 Data
#         c_dict['J-' + str(i)] = hex_color
#         # c_dict['J' + str(i+1)] = hex_color
#
#     df['color'] = df['Job'].apply(lambda j: c_dict[j.split('_')[0]])
#
#     machine_list = df['Machine'].unique()
#
#
#     # TODO: 머신 열 순서대로 출력되도록.
#     fig, ax = plt.subplots(1, figsize=(16 * 0.8, 9 * 0.8))
#     ax.barh(df.Machine, df.Delta, left=df.Start, color=df.color, edgecolor='black')
#     ##### LEGENDS #####
#
#     legend_elements = [Patch(facecolor=c_dict[i], label=i) for i in c_dict]
#     plt.legend(handles=legend_elements)
#     plt.ylabel(cfg.ylabel)
#     plt.xlabel(cfg.xlabel)
#     # plt.title(TITLE, size=24)
#     plt.title(cfg.TITLE)
#
#     ##### TICKS #####
#     if printmode:
#         plt.show()
#
#     # Save the figure as an image file
#     if writemode:
#         fig.savefig(cfg.save_path + '/' + cfg.filename + '.png', format='png')
#
#     # Create a BytesIO object
#     image_bytes_io = BytesIO()
#
#     # Save the figure to the BytesIO object
#     fig.savefig(image_bytes_io, format='png')  # This is different from saving file as .png
#
#     # Get the image bytes
#     image_bytes = image_bytes_io.getvalue()
#
#     return image_bytes
