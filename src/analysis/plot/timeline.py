"""
Useful functions for plotting remediation data.
"""

# Standard lib
from typing import Tuple, List
from datetime import datetime, timedelta

# 3rd party
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
import pandas as pd

# Local
from analysis.stat import RemediationTable
from analysis.fetch import image_first_scan, global_latest_scan


"""
Sorting functions
"""

class _Segment:
    def __init__(self, start: datetime, end: datetime, id_: str, color: str):
        self.start = start
        self.end = end
        self.id_ = id_
        self.color = color
    
    def value(self) -> int:
        return (self.end - self.start).total_seconds()
    
    def intersects(self, other) -> bool:
        if self.start < other.start:
            return self.end >= other.start
        elif other.start < self.start:
            return other.end >= self.start
        else:
            return True


class _Node:
    def __init__(self, segments: List[_Segment]):
        self.segments = segments
    
    def add_segment(self, segment: _Segment):
        self.segments.append(segment)
    
    def value(self) -> int:
        sizes = [seg.value() for seg in self.segments]
        return sum(sizes)
    
    def intersects(self, other) -> bool:
        for seg in self.segments:
            if seg.intersects(other):
                return True
        return False
    
    def max_value(self, all: List[_Segment]) -> int:
        value = self.value()
        for seg in all:
            if (seg not in self.segments) and (not self.intersects(seg)):
                value += seg.value()
        return value


def _sort_segments_i(segments: List[_Segment]) -> List[_Segment]:
    tree = []
    best = _Node([])

    tree.append(best)
    while len(tree) > 0:
        node = tree.pop(0)

        if best is None or node.value() > best.value():
            best = node

        for seg in segments:
            if (seg not in node.segments) and (not node.intersects(seg)):
                new_node = _Node(node.segments.copy())
                new_node.add_segment(seg)

                if new_node.max_value(segments) > best.value():
                    tree.append(new_node)
    return best


def _sort_segments(segments: List[_Segment]) -> List[List[_Segment]]:
    to_sort = segments.copy()
    sorted = []
    
    while len(to_sort) > 0:
        node = _sort_segments_i(to_sort)
        sorted.append(node.segments)
        for seg in node.segments:
            to_sort.remove(seg)
    
    return sorted


"""
Plotting functions
"""
LINE_WIDTH = 2
X_END = global_latest_scan()


legend = {
    "critical": "#303030",
    "high": "#f56464",
    "medium or lower": "#6a72e6"
}


def _get_line_color(row: pd.Series) -> str:
        severity = row["severity"]
        if severity in legend.keys():
            return legend[severity]
        return legend["medium or lower"]


def _get_markers(segment: _Segment, x_start: datetime) -> Tuple[str, str]:
    start_marker, end_marker = "o", "o"
    if segment.start == x_start:
        start_marker = "<"
    if segment.end == X_END:
        end_marker = ">"
    return start_marker, end_marker


def _get_segment(row: pd.Series, x_start: datetime) -> _Segment:
    start = row["first_seen_at"]
    if pd.isnull(start):
        start = x_start
    end = row["remediated_at"]
    if pd.isnull(end):
            end = X_END
    id_ = row["id"]
    color = _get_line_color(row)
    return _Segment(start, end, id_, color)


def _plot_line(seg: _Segment, y: int, ax: Axes):
    ax.plot([seg.start, seg.end], [y, y], color=seg.color, linewidth=LINE_WIDTH)


def _plot_markers(seg: _Segment, y: int, x_start: datetime, ax: Axes):
    start_marker, end_marker = _get_markers(seg, x_start)
    ax.plot(seg.start, y, start_marker, mfc="white", mec=seg.color, ms=LINE_WIDTH*2, mew=1)
    ax.plot(seg.end, y, end_marker, mfc=seg.color, mec=seg.color, ms=LINE_WIDTH*2, mew=1)
         

def _plot_ids(seg: _Segment, y: int, ax: Axes):
    id_ = str(seg.id_)
    ax.text(seg.start + ((seg.end - seg.start) / 2), y+0.25, id_, fontsize=6, ha="center")


def _plot_layer(segments: List[_Segment], y: int,
                x_start: datetime, ax: Axes, 
                include_cve_ids: bool=None) -> int:
    for seg in segments:
        _plot_line(seg, y, ax)
        _plot_markers(seg, y, x_start, ax)
           
        if include_cve_ids:
            _plot_ids(seg, y, ax)
    return y + 1


def rtime_timeline(table: RemediationTable, figsize: Tuple[int, int]=None, include_cve_ids: bool=True):
    """
    Plots a timeline of all remediations per image. The x axis is time, the y axis is
    image. This plot assumes the table represents a single registry.

    Args:
        table (RemediationTable): The table of remediations to plot.
        figsize (Tuple[int, int], optional): The figure size akin to matplotlib's `figsize` param.
        include_cve_ids (bool, optional): If `True`, CVE ids will be displayed on the plot.
    """
    
    if figsize is None:
        figsize = (7, 18)

    fig, ax = plt.subplots(figsize=figsize)
    
    hlines = []
    yticks = []
    ytick_labels = []

    y = 0
    for repo in table._df["repository"].unique():
        repo_df = table._df[table._df["repository"] == repo]
        start_y = y

        image = {
            "registry": table._df["registry"].iloc[0],
            "repository": repo,
            "tag": "latest" # TODO: Remove hard-coded value
        }
        x_start = image_first_scan(image)

        segments = [_get_segment(row, x_start) for _, row in repo_df.iterrows()]

        for layer in _sort_segments(segments):
            y = _plot_layer(layer, y, x_start,
                            ax, include_cve_ids=include_cve_ids)
        
        y += 0.5
        hlines.append(y)
        yticks.append((y + start_y) / 2 - 0.25)
        ytick_labels.append(repo)
        y += 0.5
    
    for y in hlines:
        ax.axhline(y, color="#303030", linestyle="--", dashes=(4, 8), linewidth=0.4)
    
    
    ax.set_yticks(yticks)
    ax.set_yticklabels(ytick_labels, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    legend_handles = [Line2D([0], [0], color=color, marker="o", linestyle="", label=label)
                for label, color in legend.items()]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=10)

    return fig, ax
