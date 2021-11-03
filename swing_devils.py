"""
Script to modify the Swing Devils volunteer sheet.
"""
import calendar
import datetime
import copy as cp
import pandas as pd
import random as rd

YEAR = 2021
MONTH = 11

# EXTRA_OPEN = 2 # third thursday needs an extra opener
EXTRA_OPEN = -1 # No extra open needed

# which week to skip and why
# SKIP_WEEK = {
#     3: "Thanksgiving",
#     }
SKIP_WEEK = {
    3: "Thanksgiving",
    }

# Kyle is gone weeks 3 and 5, Geoff is gone week 2
# GONE = {
#    "Kyle": [2,4],
#    "Geoff": [1],
#    }
GONE = {
    "Courtney": [1],
    "Geoff": [1],
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
    {},
    # second week
    {},
    # third week
    {},
    # fouth week
    {},
    # possible fifth week
    {},
    # facebook
    {},
    ]

VOLUNTEER_OPTIONS = pd.read_csv(
    "swing_devils_vol.csv",
    header=0,
    index_col=0,
    keep_default_na=False)


class CounterOverflowError(RuntimeError):
    """Error when there have been too many itterations."""


# pylint: disable=too-many-instance-attributes
class VolunteerPositions:
    """Class that holds and finds the volunteers for each week."""

    # pylint: disable=too-many-arguments
    def __init__(self, year, month, skip_week,
                 gone, volunteered, volunteer_options):
        """
        Initialize the data.
        """
        first_of_month = datetime.datetime(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]
        self.thursdays = [
            first_of_month + datetime.timedelta(n) for n in range(num_days)
            if (first_of_month + datetime.timedelta(n)).weekday() == 3
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
        # list containing name of every person
        self.name_list = []
        # the number of times anyone is chosen for any job
        self.counter = 0
        # the week number
        self.week_num = 0

        # dictionary containing a list of who can do each item
        self.duty_dict = {}
        for d_name in volunteer_options.columns:
            self.duty_dict[d_name] = []
        self.duty_dict["Max weeks per month"] = {}

        for name, val in volunteer_options.iterrows():
            self.name_list.append(name)
            self.vol_dict[name] = {}
            self.vol_num[name] = 0
            for d_name, duty in val.iteritems():
                if d_name[:7] == "Unnamed":
                    continue

                if d_name == "Max weeks per month":
                    self.duty_dict[d_name][name] = duty
                    continue

                if duty == "":
                    self.vol_dict[name][d_name] = False
                else:
                    self.vol_dict[name][d_name] = True
                    self.duty_dict[d_name].append(name)

    def find_name(self, position):
        """
        Randomly finds a name for the given position.
        """
        name = "default"

        # check if someone already volunteered
        if position in self.week_list[self.week_num]:
            name = self.week_list[self.week_num][position]
            if self.counter > 100:
                print(f"Week {self.week_num}: {name} at {position}")
                raise CounterOverflowError(f"counter = {self.counter}")

            if self.vol_num[name] >= self.duty_dict["Max weeks per month"][name]:
                print(f"Week {self.week_num}: {name} at {position}")
                raise CounterOverflowError(f"counter = {self.counter}")
            self.counter += 1

        else:
            while (name == "default"
                   # exceed weeks per month
                   or (self.vol_num[name] >=
                       self.duty_dict["Max weeks per month"][name])
                   # person gone this week
                   or (name in self.gone and self.week_num in self.gone[name])):

                if self.counter > 1000:
                    print(f"Week {self.week_num}: {name} at {position}")
                    raise CounterOverflowError(f"counter = {self.counter}")
                self.counter += 1
                if position == "Extra Opener":
                    name = rd.choice(self.duty_dict["Opening"])
                else:
                    name = rd.choice(self.duty_dict[position])

            self.week_list[self.week_num][position] = name

        self.vol_num[name] += 1
        if name not in self.gone:
            self.gone[name] = []
        self.gone[name].append(self.week_num)
        return name

    def find_people(self, extra_open):
        """
        Find people for each option for each week of the month.
        """
        positions_to_add = [
            "Closing",
            "DJ",
            "Teaching (lead)",
            "Teaching (follow)",
            "Opening and First Door Shift",
            ]

        for week_num in range(self.num_thursdays + 1):
            if week_num in self.skip_week:
                continue
            self.week_num = week_num
            if week_num < self.num_thursdays:
                for position in positions_to_add:
                    self.find_name(position)
                # put lead and follow together
                self.week_list[week_num]["Teaching"] = (
                    f"{self.week_list[week_num]['Teaching (lead)']} and "
                    f"{self.week_list[week_num]['Teaching (follow)']}")
                # check if need to add extra opener
                if week_num == extra_open:
                    self.find_name("Extra Opener")
            else:
                # add Facebook person
                self.find_name("Facebook Events")

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
                row = 17
            elif week_num == 3:
                col = 4
                row = 17
            elif week_num == 4:
                col = 1
                row = 34
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
                if position == "Opening and First Door Shift":
                    row_add = 2
                elif position == "Extra Opener":
                    row_add = 3
                elif position == "Teaching":
                    row_add = 5
                elif position == "DJ":
                    row_add = 9
                elif position == "Closing":
                    row_add = 12
                elif position in ("Teaching (lead)", "Teaching (follow)"):
                    continue
                else:
                    raise RuntimeError("Bad Position")

                # add the person
                volunteer_spreadsheet[col][row + row_add] = name

        # add the facebook position
        volunteer_spreadsheet[8][18] = self.week_list[
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
            vol_pos.find_people(extra_open=EXTRA_OPEN)
            vol_pos.add_to_spreadsheet()
            break
        except CounterOverflowError as err:
            print(repr(err))


if __name__ == "__main__":
    main()
