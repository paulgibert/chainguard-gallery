"""
Useful functions for plotting remediation data.
"""

# Standard lib

# 3rd party
import matplotlib.pyplot as plt
import pandas as pd

# Local
from analysis.stat import RemediationTable


def rtime_hist(table: RemediationTable, color: str=None):
    """
    Plots a histogram of all remediations. The x axis is days, the y
    axis is number of remediations.

    Args:
        table (`RemediationTable`): The table of remediations to plot.
        color (str, optional): The color of the bars.
    """
    if color is None:
        color="#6a72e6"
    fig, ax = plt.subplots()
    data = table.remediated()["rtime"] / 24
    ax.hist(data, color=color)
    ax.set_ylabel("Number of CVEs")
    ax.set_xlabel("Days")
    return fig, ax
