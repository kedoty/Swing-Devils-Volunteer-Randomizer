# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 20:45:28 2018

@author: kedot
"""


import pandas as pd
import random as rd
import copy as cp
from datetime import datetime, timedelta

###############################
# dictionary of people and the week num they are gone
# list of dictionaries for who volunteered for what each month
# hard coded (need to change each month)
###############################
# Doty is gone weeks 3 and 5, Geoff is gone week 2
#gone = {"Doty": [2,4],
#        "Geoff": [1],
#        }
gone = {"Mariah": [2],
        "Madeline": [0,3],
        "Courtney": [3],
        }

# Geoff has volunteered to DJ and close the first week
# as well as DJ the second week
#volunteered = [{'DJ':'Geoff', 'Closing (tear down)':'Geoff'},
#               {'DJ':'Geoff'},
#               {},
#               {},
#               {},
#               {},
#               ]
volunteered = [{'DJ':'Geoff'},  # first week
               {},              # second week
               {},              # third week
               {},              # fouth week
               {},              # possible fifth week
               {},              # facebook
               ]


###############
#get thrusdays#
###############
year = 2019
month = 11
day = 7
friday = 8
#extra_open = 2 #third thursday needs an extra opener
extra_open = -1
# which week to skip and why
skip_week = {3:'Thanksgiving'}
#monday = 26

thurs = [datetime(year,month,day)]
next_thurs = thurs[-1] + timedelta(days=7)

while next_thurs.month == month:
    thurs.append(next_thurs)
    next_thurs = thurs[-1] + timedelta(days=7)

num_thursdays = len(thurs)

weekly_schedule = pd.read_csv(
    "swing_devils.csv",
    header=None,
    keep_default_na=False)

########
#get volunteer data
########
volunteer = pd.read_csv(
    'swing_devils_vol.csv',
    header=0,
    index_col=0,
    keep_default_na=False)


###############################
# The error class and find people functions
###############################
class CounterOverflowError(RuntimeError):
    def __init__(self, message):
        self.message = message

def find_name(position,
              this_week,
              week_num,
              find_name_input,
              not_allowed):
    """
    randomly finds a name for a position
    """
    (week_list, vol_num, duty_dict, counter) = find_name_input
    name = 'default'
    
    # check if someone already volunteered
    if position in week_list[week_num]:
        name = week_list[week_num][position]
        if counter[0] > 100:
            print(f"Week {week_num}: {name} at {position}")
            raise CounterOverflowError('counter = {counter[0]}')
            
        if vol_num[name] >= duty_dict['Max weeks per month'][name]:
            #print(f"{name} at {position}")
            raise CounterOverflowError('counter = {counter[0]}')
            
        if this_week[name] >= 2:
            print(f"Week {week_num}: {name} at {position}")
            raise CounterOverflowError('counter = {counter[0]}')
        counter[0] += 1
    else:
                #exceed weeks per month
        while (vol_num[name] >= duty_dict['Max weeks per month'][name]
                #exceed times per week
            or this_week[name] >= 2
                #person gone this week
            or name in gone and week_num in gone[name]
                #person not allowed based on previous assignments
            or name in not_allowed):
            
            if counter[0] > 1000:
                print(f"Week {week_num}: {name} at {position}")
                raise CounterOverflowError('counter = {counter[0]}')
            counter[0] += 1
            if position == 'Extra Opener':
                name = rd.choice(duty_dict['Opening'])
            else:
                name = rd.choice(duty_dict[position])
            
        week_list[week_num][position] = name
        
    this_week[name] += 1
    if this_week[name] == 1: #first add for this week
        vol_num[name] += 1
    return name

def find_people():
    """
    find people for each event
    """
    #initialize data
    #dictionary containing dictionaries per person of what they can do
    vol_dict = {}
    #dictionary containing a list of who can do each item
    duty_dict = {}
    #dictionary containing the number of time a person did something
    vol_num = {}
    #list containing name of every person
    name_list = []
    
    for d_name in volunteer.columns:
        duty_dict[d_name] = []
    
    duty_dict['Max weeks per month'] = {}
    
    for name, val in volunteer.iterrows():
        name_list.append(name)
        vol_dict[name] = {}
        vol_num[name] = 0
        for d_name, duty in val.iteritems():
            if d_name[:7] == 'Unnamed':
                continue
            elif d_name == 'Max weeks per month':
                duty_dict[d_name][name] = duty
                continue
            
            if duty == '':
                vol_dict[name][d_name] = False
            else:
                vol_dict[name][d_name] = True
                duty_dict[d_name].append(name)
                
    
    vol_num['default'] = 100
    duty_dict['Max weeks per month']['default'] = 0
    counter = [0]
    week_list = cp.deepcopy(volunteered)
    find_name_input = (week_list, vol_num, duty_dict, counter)
    
    #find the people
    for week_num in range(len(thurs)+1):
        # reset number of times each person has helped this week
        this_week = {}
        for name in name_list:
            this_week [name] = 0
        
        if week_num < len(thurs):
            # add opener
            not_allowed = []
            opener = find_name(
                    'Opening',
                    this_week,
                    week_num,
                    find_name_input,
                    not_allowed)
    
            # add extra opener
            if week_num == extra_open:
                not_allowed = [opener]
                find_name('Extra Opener',
                          this_week,
                          week_num,
                          find_name_input,
                          not_allowed)
            
            # add Teaching (lead)
            lead = find_name('Teaching (lead)',
                             this_week,
                             week_num,
                             find_name_input,
                             not_allowed)
            
            # add Teaching (follow)
            not_allowed = lead
            follow = find_name('Teaching (follow)',
                               this_week,
                               week_num,
                               find_name_input,
                               not_allowed)
            
            # put lead and follow together
            week_list[week_num]['Teaching'] = lead + ' and ' + follow
            
            # add DJ
            not_allowed = [opener]
            DJ = find_name('DJ',
                           this_week,
                           week_num,
                           find_name_input,
                           not_allowed)
            
            # add First Door Shift
            not_allowed = [lead, follow, DJ]
            door = find_name('First Door Shift',
                             this_week,
                             week_num,
                             find_name_input,
                             not_allowed)
        
            # add Closing (tear down)
            not_allowed =[opener, door]
            close = find_name('Closing (tear down)',
                              this_week,
                              week_num,
                              find_name_input,
                              not_allowed)
        
            # add Closing (count till)
            not_allowed = [close, opener, door]
            find_name('Closing (count till)',
                      this_week,
                      week_num,
                      find_name_input,
                      not_allowed)
        else: 
            # add Facebook person
            not_allowed = []
            find_name('Facebook Events',
                      this_week,
                      week_num,
                      find_name_input,
                      not_allowed)
        
    return week_list
    
# Run the find people function
redo = True
while redo:
    try:  
        week_list = find_people()
        redo = False
    except CounterOverflowError as err:
        print('CounterOverflowError:', err.message)
    
    
###############################
# Add dates and people to the sheet
###############################
weekly_schedule[8][0] = f'{month}/{friday}/{year}'
#weekly_schedule[8][19] = f'{month}/{monday}/{year}'

# go through all the weeks (except the extras)
# the "week" after contains the facebook job
for week_num,week in enumerate(week_list[0:num_thursdays]):
    if week == {}:
        break
    # find row and col of where to add the date and people
    if week_num == 0:
        col = 1
        row = 0
    elif week_num == 1:
        col = 4
        row = 0
    elif week_num == 2:
        col = 1
        row = 20
    elif week_num == 3:
        col = 4
        row = 20
    elif week_num == 4:
        col = 1
        row = 40
    else:
        raise RuntimeError("too many weeks???")
        
    # add the date
    weekly_schedule[col][row] = f'{thurs[week_num]:%m/%d/%Y}'
    
    # find the offset to add the specific pos
    for position, name in week.items():
        if position == 'Opening':
            row_add = 2
        elif position == 'Extra Opener':
            row_add = 3
        elif position == 'Teaching':
            row_add = 5
        elif position == 'DJ':
            row_add = 9
        elif position == 'First Door Shift':
            row_add = 12
        elif position == 'Closing (tear down)':
            row_add = 15
        elif position == 'Closing (count till)':
            row_add = 16
        elif (position == 'Teaching (lead)' or
              position == 'Teaching (follow)'):
            continue
        else:
            raise RuntimeError("Bad Position")
    
        # add the person
        weekly_schedule[col][row + row_add] = name

# add the facebook position
weekly_schedule[8][19] = week_list[num_thursdays]['Facebook Events']

# output the schedule as a csv file
out_name = f"swing_devils_out_{year}_{month:02}.csv"
weekly_schedule.to_csv(out_name, index=False, header=False)










