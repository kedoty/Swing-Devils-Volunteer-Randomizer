"""
Script to modify the Swing Devils volunteer sheet.
"""
import calendar
import datetime as dt
import copy as cp
import pandas as pd
import random as rd
import time

YEAR = 2022
MONTH = 10

# which week to skip and why
# SKIP_WEEK = {
#     3: "Thanksgiving",
#     }
SKIP_WEEK = {
    # 0: "",
    # 1: "",
    # 2: "",
    # 3: "",
    # 4: "",
    }

# Kyle is gone weeks 3 and 5, Geoff is gone week 2
# GONE = {
#    "Kyle": [2,4],
#    "Geoff": [1],
#    }
GONE = {
    "Christy": [0,2],
    "Edina": [3],
    "Kyle": [1,2,3],
    "Jessica": [1,2,3],
    }

# Geoff has volunteered to the second week
# volunteered = [
#    {},
#    {"DJ": "Geoff"},
#    {},
#    {},
#    {},
#    {},
#    ]
VOLUNTEERED = [
    # first week
    {
        "Teaching (intermediate)": "Michael",
        "DJ": "Jessica",
        "Closing": "Kyle",
    },
    # second week
    {
        # "First Door Shift": "Colby",
        "Teaching (intermediate)": "Michael",
        "DJ": "Geoff",
        "Closing": "Colby",
    },
    # third week
    {
        # "First Door Shift": "Colby",
        "Teaching (intermediate)": "Michael",
        "DJ": "Geoff",
        "Closing": "Colby",
    },
    # fourth week
    {
        "Teaching (intermediate)": "Michael",
        "Closing": "Colby",
    },
    # possible fifth week
    {
    },
    # facebook
    {},
    ]

VOLUNTEER_OPTIONS = pd.read_csv(
    "swing_devils_vol.csv",
    header=0,
    index_col=0,
    keep_default_na=False)


class NoneAvailableError(RuntimeError):
    """Error when there is no one available at a position."""


# pylint: disable=too-many-instance-attributes
class VolunteerPositions:
    """Class that holds and finds the volunteers for each week."""

    # pylint: disable=too-many-arguments
    def __init__(self, year, month, skip_week,
                 gone, volunteered, volunteer_options):
        """
        Initialize the data.
        """
        first_of_month = dt.datetime(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]
        self.thursdays = [
            first_of_month + dt.timedelta(n) for n in range(num_days)
            if (first_of_month + dt.timedelta(n)).weekday() == 3
            ]
        self.num_thursdays = len(self.thursdays)
        self.skip_week = skip_week
        self.gone = cp.deepcopy(gone)

        # the list of weeks of what everyone is doing
        self.week_list = cp.deepcopy(volunteered)
        # dictionary containing dictionaries per person of what they can do
        self.vol_dict = {}
        # dictionary containing the number of time a person did something
        self.vol_num = {}
        # the duties to fill
        self.duties = []
        # dictionary containing a list of who can do each item
        self.duty_dict = {}
        # dictionary containing the max number of weeks a person can volunteer per month
        self.max_weeks_per_month = {}

        for duty_name in volunteer_options.columns:
            if duty_name != "Max weeks per month":
                self.duties.append(duty_name)

        for name, row in volunteer_options.iterrows():
            self.vol_dict[name] = []
            self.vol_num[name] = 0
            for duty_name, entry in row.iteritems():
                if duty_name == "Max weeks per month":
                    self.max_weeks_per_month[name] = entry
                elif entry != "":
                    self.vol_dict[name].append(duty_name)

        for week_vol in volunteered:
            for name in week_vol.values():
                self.vol_num[name] += 1



    def update_duty_dict(self, week_num):
        """
        """
        self.reset_duty_dict()
        self.remove_volunteers(week_num)
        self.remove_gone(week_num)
        self.remove_max_volunteered()

    def reset_duty_dict(self):
        """
        """
        # Reset duty_dict
        self.duty_dict = {}
        for duty_name in self.duties:
            self.duty_dict[duty_name] = []
            for name, duty_list in self.vol_dict.items():
                if duty_name in duty_list:
                    self.duty_dict[duty_name].append(name)

    def remove_volunteers(self, week_num):
        """
        """
        for available_list in self.duty_dict.values():
            for volunteer in self.week_list[week_num].values():
                try:
                    available_list.remove(volunteer)
                except ValueError:
                    pass


    def remove_gone(self, week_num):
        """
        """
        for available_list in self.duty_dict.values():
            for volunteer, gone_weeks in self.gone.items():
                if week_num in gone_weeks:
                    try:
                        available_list.remove(volunteer)
                    except ValueError:
                        pass

    def remove_max_volunteered(self):
        """
        """
        for available_list in self.duty_dict.values():
            for volunteer, max_weeks in self.max_weeks_per_month.items():
                if self.vol_num[volunteer] >= max_weeks:
                    try:
                        available_list.remove(volunteer)
                    except ValueError:
                        pass

    def remove_name_from_duties(self, name):
        """
        """
        for available_list in self.duty_dict.values():
            try:
                available_list.remove(name)
            except ValueError:
                pass

    def assign_name(self, position, week_num):
        """
        Randomly finds a name for the given position.
        """
        # Only add if someone hasn't volunteered
        if position not in self.week_list[week_num]:
            if not self.duty_dict[position]:
                raise NoneAvailableError(f"No one is available for {position} at week {week_num}, {self.week_list}")

            name = rd.choice(self.duty_dict[position])
            self.week_list[week_num][position] = name

            self.vol_num[name] += 1
            self.remove_name_from_duties(name)


    def find_people(self):
        """
        Find people for each option for each week of the month.
        """
        positions_to_add = [
            # "Teaching (intermediate)",
            "First Door Shift",
            "Teaching (follow)",
            "DJ",
            "Closing",
            "Teaching (lead)",
            ]

        for week_num in range(self.num_thursdays):
            if week_num not in self.skip_week:
                self.update_duty_dict(week_num)
                for position in positions_to_add:
                    self.assign_name(position, week_num)

        # add Facebook person
        self.reset_duty_dict()
        self.assign_name("Facebook Events", self.num_thursdays)

    # pylint: disable=too-many-branches
    def add_to_spreadsheet(self):
        """
        Add dates and people to the spreadsheet
        """
        volunteer_spreadsheet = pd.read_csv(
            "swing_devils.csv",
            header=None,
            keep_default_na=False)

        # find second friday
        if self.thursdays[0].day == 7:
            friday = 8
        else:
            friday = self.thursdays[1].day + 1
        volunteer_spreadsheet[8][0] = f"{MONTH}/{friday}/{YEAR}"

        # go through all the weeks (except the extras)
        # the "week" after contains the facebook job
        for week_num, week in enumerate(self.week_list[:self.num_thursdays]):
            # find row and col of where to add the date and people
            if week_num == 0:
                col = 1
                row = 0
            elif week_num == 1:
                col = 4
                row = 0
            elif week_num == 2:
                col = 1
                row = 18
            elif week_num == 3:
                col = 4
                row = 18
            elif week_num == 4:
                col = 1
                row = 36
            else:
                raise RuntimeError("too many weeks???")

            # add the date
            volunteer_spreadsheet[col][row] = f"{self.thursdays[week_num]:%m/%d/%Y}"

            # check to see if this week should be skipped
            if week_num in self.skip_week:
                if self.skip_week[week_num]:
                    volunteer_spreadsheet[col][row + 14] = self.skip_week[week_num]
                continue

            # find the offset to add the specific pos
            for position, name in week.items():
                if position == "First Door Shift":
                    row_add = 2
                elif position == "Teaching (lead)":
                    row_add = 5
                elif position == "Teaching (follow)":
                    row_add = 6
                elif position == "Teaching (intermediate)":
                    row_add = 7
                elif position == "DJ":
                    row_add = 10
                elif position == "Closing":
                    row_add = 13
                else:
                    raise RuntimeError("Bad Position")

                # add the person
                volunteer_spreadsheet[col][row + row_add] = name

        # add the facebook position
        volunteer_spreadsheet[8][20] = self.week_list[
            self.num_thursdays]["Facebook Events"]

        # output the schedule as a csv file
        out_name = f"swing_devils_out_{YEAR}_{MONTH:02}.csv"
        volunteer_spreadsheet.to_csv(out_name, index=False, header=False)


def main():
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
                volunteer_options=VOLUNTEER_OPTIONS)
            vol_pos.find_people()
            vol_pos.add_to_spreadsheet()
            break
        except NoneAvailableError as err:
            print(err.args[0], "\n")
            time.sleep(.25)


if __name__ == "__main__":
    main()
