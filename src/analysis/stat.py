"""
Helper classes and functions for displaying remediation stats.
"""

# Standard lib
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

# 3rd party
import pandas as pd
from tqdm import tqdm
from gryft.scanning.types import CVE

# Local
from .fetch import global_latest_scan, image_first_scan, images_first_scan


@dataclass(frozen=True)
class Remediation:
    """
    Represents a represents a remediation.

    cve (CVE): The CVE match.
    first_seen_at (datetime): When the match was first observed.
    remediated_at (datetime): When the match was remediated.
    """
    cve: CVE
    first_seen_at: datetime
    remediated_at: datetime


class RemediationTable:
    """
    Represents remediation data. Basically wraps a `pd.DataFrame`
    with some quality of life methods for calculating remediation stats.
    """
    def __init__(self, df: pd.DataFrame):
        """
        df (pd.DataFrame): A `pd.DataFrame` of the remediation data. May include a mixture of
                           registries and repositories.
        """
        self._df = df
    
    def latest_remediation(self) -> datetime:
        return self._df["remediated_at"].max()

    def resolve_edge_cases(self, first_seen_at: bool=True,
                           remediated_at: bool=True):
        df = self._df.copy()

        if remediated_at:
            df.loc[df["remediated_at"].isna(), "remediated_at"] = global_latest_scan()

        if first_seen_at:
            seen = images_first_scan()
            for i, row in tqdm(df.iterrows(), total=df.shape[0],
                            desc="Resolving edge-cases", ):
                if pd.notna(row["first_seen_at"]):
                    continue

                key = (row["registry"], row["repository"])
                if key not in seen.keys():
                    image = {k: row[k] for k in ["registry", "repository", "tag"]}
                    seen[key] = image_first_scan(image)
                
                df.at[i, "first_seen_at"] = seen[key]
        
        # Calculate remedation time columns
        
        df["rtime"] = pd.to_datetime(df["remediated_at"]) - pd.to_datetime(df["first_seen_at"])
        df["rtime"] = df["rtime"].dt.total_seconds() / 3600
        
        return RemediationTable(df)

    @classmethod
    def empty(cls):
        """
        Creates an empty table.

        Returns:
            An empty `RemediationTable`
        """
        return cls(pd.DataFrame(columns=["registry",
                "repository", "tag", "labels", "first_seen_at",
                "remediated_at", "id", "severity", "fix_state",
                "component.name", "component.version", "component.type_",
                "rtime"]))
    
    @classmethod
    def from_remediations(cls, image: Dict, remediations: List[Remediation]):
        """
        Creates a `RemediationTable` from a `List` of `Remediation` objects. All remediations
        must be from the same image.

        Args:
            image (Dict): The image the remediation are based on. Must contain the fields 
                        `registry`, `repository`, `tag`, and `labels`.
            remediations (List[Remediation]): A `List` of the image's remediations.

        Returns:
            A new `RemediationTable`
        """

        # If no remediations are provided, create an empty table.
        if len(remediations) == 0:
            return RemediationTable.empty()
        
        # Map the remdiations to pd.DataFrame rows
        df = pd.DataFrame(map(asdict, remediations))

        # Set type of datetime columns
        df["first_seen_at"] = pd.to_datetime(df["first_seen_at"])
        df["remediated_at"] = pd.to_datetime(df["remediated_at"])

        # Add the image data columns
        for col in ["registry", "repository", "tag"]:
            df[col] = image[col]
        df["labels"] = "".join(image["labels"])

        # Expand CVE column
        expanded_df = pd.json_normalize(df["cve"])
        df = pd.concat([df.drop(columns=["cve"]), expanded_df], axis=1)

        # Calculate remedation time columns
        df["rtime"] = (df["remediated_at"] - df["first_seen_at"])
        df["rtime"] = df["rtime"].dt.total_seconds() / 3600

        return cls(df)

    def filter(self, label: str=None, registry: str=None, repository:str=None,
               purge: bool=False):
        """
        Filters a table by `label`, `registry`, and `repository`. This operation is not
        in-place. A new `RemediationTable` object is returned.

        Args:
            label (str, optional): The label to filter by.
            registry (str, optional): The registry to filter by.
            repository (str, optional): The repository to filter by.
            purge (bool, optional): If True, purges items according to the provided filters (filters \"out\" instead of \"for\").

        Returns:
            The filtered `RemediationTable`
        """
        filtered_df = self._df.copy(deep=True)
        if purge:
            if label is not None:
                filtered_df = filtered_df[~filtered_df["labels"].str.contains(label)]
            if registry is not None:
                filtered_df = filtered_df[filtered_df["registry"] != registry]
            if repository is not None:
                filtered_df = filtered_df[filtered_df["repository"] != repository]
        else:
            if label is not None:
                filtered_df = filtered_df[filtered_df["labels"].str.contains(label)]
            if registry is not None:
                filtered_df = filtered_df[filtered_df["registry"] == registry]
            if repository is not None:
                filtered_df = filtered_df[filtered_df["repository"] == repository]
        return RemediationTable(filtered_df)

    def preexisting(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the preexisting CVE matches.
        A preexisting match is one that is discovered on the first scan
        and has no certain `first_seen_at` value.

        Returns:
            A `pd.DataFrame` of the preexisting CVE matches.
        """
        return self._df[self._df["first_seen_at"].isna()]

    def discovered(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the discovered CVE matches.
        A discovered match is one that is discovered during the experiment
        and therefore has a certain `first_seen_at` value.

        Returns:
            A `pd.DataFrame` of the discovered CVE matches.
        """
        return self._df[self._df["first_seen_at"].notna()]

    def remediated(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the remediated CVE matches.
        A remediated match is one that is observed at some point
        (including the first scan) and disappears at a later point.
        The `remediated_at` value of these matches is defined.

        Returns:
            A `pd.DataFrame` of the remediated CVE matches.
        """
        return self._df[self._df["remediated_at"].notna()]
    
    def true_remediated(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the true_remediated CVE matches.
        A true_remediated match is one that is observed at some point
        (NOT including the first scan) and disappears at a later point.
        The `first_seen_at` and `remediated_at` values of these matches are defined.

        Returns:
            A `pd.DataFrame` of the true_remediated CVE matches.
        """
        return self._df[self._df["first_seen_at"].notna() & self._df["remediated_at"].notna()]
    
    def residual(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the residual CVE matches.
        A residual match is one that is observed at the last scan.
        The `remediated_at` value of these matches is NOT defined.

        Returns:
            A `pd.DataFrame` of the residual CVE matches.
        """
        return self._df[self._df["remediated_at"].isna()]
    
    def perpetual(self) -> pd.DataFrame:
        """
        Returns a `pd.DataFrame` of the perpetual CVE matches.
        A perpetual match is one that is observed at the first AND last scan.
        NEITHER the `first_seen_at` nor `remediated_at` values of these matches
        are defined.

        Returns:
            A `pd.DataFrame` of the perpetual CVE matches.
        """
        return self._df[self._df["first_seen_at"].isna() & self._df["remediated_at"].isna()]
    
    def _group_rtime(self, groups: List[str]) -> pd.DataFrame:
        """
        A helper method that computes the mean and std remediation
        time (rtime) of the provided groups.
        """
        df = self.remediated().copy()
        mean_df = df.groupby(groups)["rtime"] \
                .mean() \
                .reset_index()
        
        std_df = df.groupby(groups)["rtime"] \
                .std() \
                .reset_index() \
        
        return mean_df.merge(std_df, how="inner",
                             on=["registry", "repository", "tag"],
                             suffixes=["_mean", "_std"])

    def cve_stats(self) -> Dict:
        """
        Tabulates the CVE match stats across the table. Reports preexisting,
        discovered, remediated, true_remediated, residual, and perpetual CVE
        matches. For each match type, the count and percent is reported.

        The count is the number of CVE matches of the given type. For example,
        there are 51 preexisting CVEs.

        The percent is the count divided by the total matches observed, including preexisting.

        For example, percent remediated = [ count remediated / (count preexisting + count discovered) ] or
        12% of the CVE matches were remediated.

        Count columns are prepended with n_. Percent columns are prepended with p_.

        Returns:
            A `pd.DataFrame` of the CVE match statistics.
        """
        categories = ["preexisting", "discovered",
                      "remediated", "true_remediated", "residual", "perpetual"]
        
        # Count
        stats = {f"n_{cat}": getattr(self, cat)().shape[0] for cat in categories}
        
        # Percent
        total = stats["n_preexisting"] + stats["n_discovered"]
        for cat in categories:
            stats[f"p_{cat}"] = stats[f"n_{cat}"] / total
        
        return stats
    
    def image_summary(self, true_rtime: bool=False) -> pd.DataFrame:
        """
        Calculates CVE match stats by image across the table. Basically
        groups the table by image and calls `cve_stats()`.

        Returns:
            A `pd.DataFrame` of the CVE match stats by image.
        """
        groups = ["registry", "repository", "tag"]
        df = self._group_rtime(groups)

        for i, row in df.iterrows():
            registry, repository = row["registry"], row["repository"]
            image_tab = self.filter(registry=registry, repository=repository)
            stats = image_tab.cve_stats()
            for key, value in stats.items():
                df.loc[i, key] = value
        
        return df


def concat(tables: List[RemediationTable]) -> RemediationTable:
    """
    A helper function for concatenating tables.

    Args:
        table (List[RemediationTable]): The `List` of tables to concat.

    Returns:
        A `RemediationTable` formed from concatenating the input tables.
    """
    dfs = [tab._df for tab in tables]
    merged_df = pd.concat(dfs, axis=0, ignore_index=True)
    return RemediationTable(merged_df)
