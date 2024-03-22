# Standard lib
import smtplib
from email.message import EmailMessage

# Local
from monitor import ProgressReport


def report2str(report: ProgressReport) -> str:
    return f"""
        Scan Report
        ===========
        Start: {report.scan_duration.isoformat()}
        Duration: {report.scan_duration} minute(s)
        Total Scans: {report.total_scans} / {report.total_images}

        Repeated Scans:
        {report.repeated_scans}

        Missing Scans:
        {report.missing_scans}

        Unprompted Scans:
        {report.unprompted_scans}
    """


def email_report(report: ProgressReport, to_addr: str):
    pass