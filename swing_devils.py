"""
Script to modify the Swing Devils volunteer sheet.
"""
import calendar
import datetime as dt
import copy as cp
import pandas as pd
import random as rd
import time

from typing import Dict, List, Tuple

YEAR = 2023
MONTH = 4

# which week to skip and why
# SKIP_WEEK = {
#     3: "Thanksgiving",
# }
SKIP_WEEK: Dict[int, str] = {
    # 0: "",
    # 1: "",
    # 2: "",
    # 3: "Winter Break",
    # 4: "Winter Break",
}

# Kyle is gone weeks 3 and 5, Geoff is gone week 2
# GONE = {
#     "Kyle": (3,5),
#     "Geoff": (2,),
# }
GONE: Dict[str, Tuple[int, ...]] = {
    "Christy": (1,),
    "Bear": (2,),
    "Geoff": (3, 4),
}

# Geoff has volunteered to the second week
# volunteered = (
#     {},
#     {"DJ": "Geoff"},
#     {},
#     {},
#     {},
#     {},
# )
VOLUNTEERED: Tuple[
    Dict[str, str],
    Dict[str, str],
    Dict[str, str],
    Dict[str, str],
    Dict[str, str],
    Dict[str, str],
] = (
    {
        # first week
        "Teaching (intermediate)": "Maureen and Kenny",
        "DJ": "Geoff",
        "Closing": "Colby",
    },
    {
        # second week
        "Teaching (intermediate)": "Maureen and Kenny",
    },
    {
        # third week
        "Teaching (intermediate)": "Maureen and Kenny",
        "DJ": "Jessica",
        "Closing": "Kyle",
    },
    {
        # fourth week
        "Teaching (intermediate)": "Maureen and Kenny",
    },
    {
        # possible fifth week
    },
    {
        # facebook
    },
)

VOLUNTEER_OPTIONS: pd.DataFrame = pd.read_csv(
    "swing_devils_vol.csv", header=0, index_col=0, keep_default_na=False
)


class NoneAvailableError(RuntimeError):
    """Error when there is no one available at a position."""


# pylint: disable=too-many-instance-attributes
class VolunteerPositions:
    """Class that holds and finds the volunteers for each week."""

    skip_week_key = "skip"
    facebook_key = "Facebook Events"

    row_offset_dict = {
        "First Door Shift": 2,
        "Teaching (lead)": 5,
        "Teaching (follow)": 6,
        "Teaching (intermediate)": 7,
        "DJ": 10,
        "Closing": 13,
        skip_week_key: 15,
        facebook_key: 0,
    }

    duties_to_not_assign = (
        facebook_key,
        # "Teaching (intermediate)",
    )

    col_row_list = (
        (1, 0),
        (4, 0),
        (1, 18),
        (4, 18),
        (1, 36),
        (8, 20),  # Facebook entry
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        year: int,
        month: int,
        skip_week: Dict[int, str],
        gone: Dict[str, Tuple[int, ...]],
        volunteered: Tuple[
            Dict[str, str],
            Dict[str, str],
            Dict[str, str],
            Dict[str, str],
            Dict[str, str],
            Dict[str, str],
        ],
        volunteer_options: pd.DataFrame,
    ):
        """
        Initialize the data.
        """
        # list containing which Thursdays are in the month
        first_of_month = dt.datetime(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]
        THURSDAY_WEEKDAY = 3
        self.thursdays = [
            first_of_month + dt.timedelta(n)
            for n in range(num_days)
            if (first_of_month + dt.timedelta(n)).weekday() == THURSDAY_WEEKDAY
        ]

        # dictionary containing who is gone which weeks
        self.gone = gone

        # the list of which week numbers to schedule
        self.week_num_list = [
            week_num
            for week_num in range(len(self.thursdays))
            if week_num not in skip_week
        ]

        # the list of weeks of what everyone is doing
        self.week_list = cp.deepcopy(volunteered)
        for skip_week_num, skip_reason in skip_week.items():
            self.week_list[skip_week_num][self.skip_week_key] = skip_reason

        # all available duties
        self.duties = [
            duty_name
            for duty_name in self.row_offset_dict.keys()
            if duty_name != self.skip_week_key
        ]

        # the duties to fill
        self.duties_to_assign = [
            duty_name
            for duty_name in self.duties
            if duty_name not in self.duties_to_not_assign
        ]

        # dictionary containing dictionaries per person of what they can do
        self.vol_dict: Dict[str, List[str]] = {}

        # dictionary containing the number of time a person did something
        self.vol_num: Dict[str, int] = {}

        # dictionary containing the max number of weeks a person can volunteer per month
        self.max_weeks_per_month: Dict[str, int] = {}

        for name, row in volunteer_options.iterrows():
            name = str(name)
            self.vol_dict[name] = []
            self.vol_num[name] = 0
            for duty_name, entry in row.iteritems():
                duty_name = str(duty_name)
                if duty_name == "Max weeks per month":
                    self.max_weeks_per_month[name] = int(entry)
                elif str(entry):
                    self.vol_dict[name].append(duty_name)

        for week_vol in volunteered:
            for name in set(week_vol.values()):
                if name:
                    try:
                        self.vol_num[name] += 1
                    except KeyError:
                        pass

        # dictionary containing a list of who can do each item
        self.duty_dict: Dict[str, List[str]] = {}

    def update_duty_dict(self, week_num: int) -> None:
        """Updates the duty dict of who can do what for the week.

        Will remove anyone who has already volunteered this week,
        will be gone this week, or who has volunteered their max amount this month.
        """
        self.reset_duty_dict()
        self.remove_volunteers(week_num)
        self.remove_gone(week_num)
        self.remove_max_volunteered()

    def reset_duty_dict(self) -> None:
        """Fills the duty_dict with everyone who says they can do each role."""
        # Reset duty_dict
        self.duty_dict = {}
        for duty_name in self.duties:
            self.duty_dict[duty_name] = []
            for name, duty_list in self.vol_dict.items():
                if duty_name in duty_list:
                    self.duty_dict[duty_name].append(name)

    def remove_volunteers(self, week_num: int) -> None:
        """Remove everyone who has already volunteered for something the given week."""
        for available_list in self.duty_dict.values():
            for volunteer in self.week_list[week_num].values():
                try:
                    available_list.remove(volunteer)
                except ValueError:
                    pass

    def remove_gone(self, week_num: int) -> None:
        """Remove everyone who says they will be gone in the given week."""
        for available_list in self.duty_dict.values():
            for volunteer, gone_weeks in self.gone.items():
                if (week_num + 1) in gone_weeks:
                    try:
                        available_list.remove(volunteer)
                    except ValueError:
                        pass

    def remove_max_volunteered(self) -> None:
        """Remove everyone who has already volunteered their max times in a month."""
        for available_list in self.duty_dict.values():
            for volunteer, max_weeks in self.max_weeks_per_month.items():
                if self.vol_num[volunteer] >= max_weeks:
                    try:
                        available_list.remove(volunteer)
                    except ValueError:
                        pass

    def remove_name_from_duties(self, name: str) -> None:
        """Removes the given name from all duties in the duty_dict."""
        for available_list in self.duty_dict.values():
            try:
                available_list.remove(name)
            except ValueError:
                pass

    def assign_name(self, position: str, week_num: int) -> None:
        """Randomly finds a name for the given position."""
        # Only add if someone hasn't volunteered
        if position not in self.week_list[week_num]:
            if not self.duty_dict[position]:
                raise NoneAvailableError(
                    f"No one is available for {position} at week {week_num + 1}, {self.week_list}"
                )

            name = rd.choice(self.duty_dict[position])
            self.week_list[week_num][position] = name

            self.vol_num[name] += 1
            self.remove_name_from_duties(name)

    def find_people(self) -> None:
        """Find people for each option for each week of the month."""
        shuffled_week_num = rd.sample(self.week_num_list, k=len(self.week_num_list))
        for week_num in shuffled_week_num:
            self.update_duty_dict(week_num)

            shuffled_duties = rd.sample(
                self.duties_to_assign, k=len(self.duties_to_assign)
            )
            for position in shuffled_duties:
                self.assign_name(position, week_num)

        # add Facebook person
        self.reset_duty_dict()
        self.assign_name(self.facebook_key, -1)

    def add_second_friday(self, volunteer_spreadsheet: pd.DataFrame) -> None:
        """Add the second Friday to the volunteer spreadsheet."""
        if self.thursdays[0].day == 7:
            friday = 8
        else:
            friday = self.thursdays[1].day + 1
        volunteer_spreadsheet[8][0] = f"{MONTH}/{friday}/{YEAR}"

    def add_volunteer_week(
        self, volunteer_spreadsheet: pd.DataFrame, week_num: int, week: Dict[str, str]
    ) -> None:
        """Adds the given week to the spreadsheet."""
        # Early return if not a valid Thursday
        if week_num >= len(self.thursdays):
            return

        # Get the column and row information
        try:
            col, row = self.col_row_list[week_num]
        except IndexError:
            raise RuntimeError("too many weeks???")

        # Add the date
        volunteer_spreadsheet[col][row] = f"{self.thursdays[week_num]:%m/%d/%Y}"

        # Add the information (if not skipped)
        skip_row_offset = self.row_offset_dict[self.skip_week_key]
        try:
            volunteer_spreadsheet[col][row + skip_row_offset] = week[self.skip_week_key]
        except KeyError:
            for position, name in week.items():
                try:
                    row_offset = self.row_offset_dict[position]
                except KeyError:
                    raise RuntimeError("Bad Position")

                volunteer_spreadsheet[col][row + row_offset] = name

    def add_to_spreadsheet(self) -> None:
        """
        Add dates and people to the spreadsheet
        """
        volunteer_spreadsheet = pd.read_csv(
            "swing_devils.csv", header=None, keep_default_na=False
        )

        self.add_second_friday(volunteer_spreadsheet)

        # Go through all the weeks (except the extras)
        # the last "week" contains the facebook job.
        for week_num, week in enumerate(self.week_list[:-1]):
            self.add_volunteer_week(volunteer_spreadsheet, week_num, week)

        # Add the facebook position.
        col, row = self.col_row_list[-1]
        volunteer_spreadsheet[col][row] = self.week_list[-1][self.facebook_key]

        # Output the schedule as a csv file.
        out_name = f"swing_devils_out_{YEAR}_{MONTH:02}.csv"
        volunteer_spreadsheet.to_csv(out_name, index=False, header=False)


def main() -> None:
    """
    Find a possible weekly volunteer list.
    """
    while True:
        try:
            vol_pos = VolunteerPositions(
                year=YEAR,
                month=MONTH,
                skip_week=SKIP_WEEK,
                gone=GONE,
                volunteered=VOLUNTEERED,
                volunteer_options=VOLUNTEER_OPTIONS,
            )
            vol_pos.find_people()
            vol_pos.add_to_spreadsheet()
            break
        except NoneAvailableError as err:
            print(err.args[0], "\n")
            time.sleep(0.25)


if __name__ == "__main__":
    main()
