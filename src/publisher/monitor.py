"""
Let N be the number of minutes to monitor
We will probe every n minutes

Init a table with the name of every image.
Keep a timestamp

Fetch all scans after timestamp
update table counts every minute

At the end of 30 mins, report:


Total scans to total images: 1204/1206
Redudant Scans:
image1: 2
image2: 4
image3: 5

Missing scans for:
image6
image10

Unprompted scans:
imageX
"""


# Standard lib
from typing import List, Dict
from datetime import datetime, timedelta
import time

# 3rd party
from pymongo import Cursor


def fetch_images() -> Cursor:
    pass

def fetch_scans_after(after: datetime) -> Cursor:
    pass

def init_table(images: Cursor) -> Dict[str, int]:
    pass

@dataclass
class ProgressReport:
    timestamp: datetime
    total_scans: int
    total_images: int
    repeat_scans: Dict[str, int]
    missing_scans: List[str]
    unprompted_scans: List[str]
    scan_duration: int
    scan_start_time: datetime

def update_table(curr_time: datetime, table: Dict[str, int]) -> ProgressReport:
    pass


class ProgressMonitor:
    def __init__(self, images: List[str]=None):
        self._images = images
        if self._images is None:
            self._images = fetch_images()
        self._table = init_table(self._images)
    
    def start(self, monitor_window: int=20,
              monitor_interval: int=1) -> ProgressReport:
        curr_time = datetime.now(datetime.UTC)
        end_time = curr_time + timedelta(minutes=monitor_window)
        
        while curr_time < end_time:
            report = update_table(curr_time, self._table)
            time.sleep(60 * monitor_interval)
            curr_time = datetime.now(datetime.UTC)
        
        return report