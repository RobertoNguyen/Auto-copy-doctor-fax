# Auto-copy doctor's fax #'s by search

import os
import json
import sys
import re
import pyperclip
import logging

logging.basicConfig(level=logging.DEBUG)
#logging.disable(logging.DEBUG)


def main():
    arg = input('"[Last]" or "[Last], [First]" to search. "Help" to display commands: ').lower()

    # regex to check for lastN with/without firstN
    nameSearch = re.compile(r'''
                            ([a-zA-Z]+)     # Checks first name
                            (,\s | ,)?      # Checks for comma
                            ([a-zA-Z]+)?    # Checks for last name
                           ''', re.VERBOSE | re.IGNORECASE)
    try:
        lastN = nameSearch.search(arg).group(1)    # lastN
        firstN = nameSearch.search(arg).group(3)    # firstN, letter
    except AttributeError:
        print('Invalid command, try again\n')
        main()
    
    # regex to check for <list>, <edit> or <add>
    commandSearch = re.compile(r'''
                               (edit)
                               \s*([a-zA-Z]+)?
                              ''', re.VERBOSE)
    
    try:
        arg1 = nameSearch.search(arg).group(1)        #
        arg2 = commandSearch.search(arg).group(2)     #
    except (AttributeError, UnboundLocalError):
        pass

    if arg == 'help':
        print('\n---------COMMAND----------------------------------DESCRIPTION------------------')
        print('1. LIST                                  lists ALL entries')
        print('2. ADD  <LASTNAME, FIRSTNAME, FAX#>      to add entry LASTN/FIRSTN/FAX#')
        print('3. EDIT <LAST NAME/PARTS OF LAST NAME>   to edit entry LASTN/FIRSTN/FAX#\n\n')
        main()
    elif arg1 == 'list':
        list_data()
        main()
    #elif arg == 'add':
        # TODO
    #elif arg == 'edit':
        # TODO
    elif lastN != None:             # <lastN>
        lookup(lastN, firstN)       # <lastN, firstN>
    else:
        print('Invalid command, try again')
        main()


def lookup(lastN, firstN=None):
    #logging.disable(logging.DEBUG)

    result_counter, search_counter = 0, 0
    temp_dict = {}      # used for user number input selection for 2+ search results
    search_results = {}    

    # Iterate through each listed index of the data (doctors key). Filters last names             
    for letter in sorted_data:                   # gets entire alphabet lettered dictionary: {"a": vals}
        if lastN[0] in letter:                  # gets list of key entries for letter: [{LIST}, {OF}, {VALUES}]
            for doctor in letter[lastN[0]]:     # single entry. {'last': name, 'first': name, 'fax': ##########}
                if lastN in doctor["last"]:
                    result_counter += 1
                    temp_dict[result_counter] = doctor      # {#: doctor entry}

    # <lastN> <firstN>. Filters first names after last names are filtered
    if firstN:  # None = False, if parameter filled, True otherwise
        for i in range(1, result_counter+1):
            if firstN in temp_dict[i]["first"]:
                search_counter += 1
                search_results[search_counter] = temp_dict[i]
        if search_counter == 0:     # No search results
            display_results(search_counter, '%s, %s' % (lastN, firstN))
        else:
            display_results(search_counter, search_results)

    # <lastN>
    if result_counter == 0:         # No search results
        display_results(result_counter, lastN)
    else:
        display_results(result_counter, temp_dict)


# Takes arguments from lookup function and displays to user based on # of results
def display_results(result_counter, temp_dict):

    if result_counter == 0:
        print('No results found for: %s \n' % temp_dict)
    elif result_counter == 1:
        result = '{:>5}, {:>5} {:>13}'.format(temp_dict[1]["last"], temp_dict[1]["first"], temp_dict[1]["fax"])
        pyperclip.copy(temp_dict[1]["fax"])
        print('Copied fax number for: %s \n' % result)
    elif result_counter > 1:
        print('LAST'.center(12, '-'), 'FIRST'.center(11, '-'), 'FAX'.center(12, '-'))
        
        for i in range(1, result_counter+1):
            result = '{} {:>10} {:>10} {:>13}'.format(i, temp_dict[i]["last"], temp_dict[i]["first"], temp_dict[i]["fax"])
            print(result)
        print('Found %d results\n' % result_counter)

        while True:
            try:
                num_input = int(input('Enter a number between {}-{} to copy fax number (0 for main menu): '
                                      .format('1', result_counter)))
                if result_counter >= num_input and num_input >= 1:
                    result = '{:>5}, {:>5} {:>13}'\
                        .format(temp_dict[num_input]["last"], temp_dict[num_input]["first"], temp_dict[num_input]["fax"])
                    pyperclip.copy(temp_dict[num_input]["fax"])
                    print('Copied fax number for: %s \n' % result)
                    main()
                elif num_input == 0:
                    print()
                    main()
            except (ValueError, KeyError):
                pass
    main()


# Lists all doctors
def list_data():

    temp_dict = {}
    result_counter = 0      # resets counter if already been used before in other functions

    print('LAST'.center(12, '-'), 'FIRST'.center(11, '-'), 'FAX'.center(12, '-'))

    for letters in range(len(sorted_data)):
        for dr in sorted_data[letters].values():
            for index in range(len(dr)):
                result_counter += 1
                temp_dict[result_counter] = dr[index]
                if result_counter < 10:
                    entry = '{:>2} {:>10} {:>10} {:>13}'\
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"])
                else:
                    entry = '{} {:>10} {:>10} {:>13}'\
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"])
                print(entry)
            print()


# Sorts data file first before using any of the other functions
def sort_alphabet(dictionary):
    less, pivot_list, more = [], [], []

    if len(dictionary) <= 1:
        return dictionary
    else:
        try:
            # need to determine a pivot point in the middle. floors the index if contains remainder
            index = int(len(dictionary) / 2)
            for key1 in dictionary[index]:
                pivot = key1  # pivot = single alphabet letter
            for i in range(len(dictionary)):
                for key in dictionary[i]:
                    if key < pivot:
                        less.append(dictionary[i])
                    elif key > pivot:
                        more.append(dictionary[i])
                    else:
                        pivot_list.append(dictionary[i])
            less = sort_alphabet(less)
            more = sort_alphabet(more)
            return less + pivot_list + more
        except (AttributeError, TypeError):
            pass


def sort_drs(dictionary, first_name=False):
    less, pivot_list, more = [], [], []
    if len(dictionary) <= 1:
        return dictionary
    else:
        try:
            for index in range(len(dictionary)):  # data = [index]. index = 0,1,2,3.
                if first_name:
                    namepiv = dictionary[0]["first"]
                    name = dictionary[index]["first"]
                else:
                    namepiv = dictionary[0]["last"]
                    name = dictionary[index]["last"]  # data[index] = entire list of dr entries per letter
                #logging.debug("Comparing: %s, %s" % (namepiv, name))

                # Sets total length index compared to be the shorter name of the two
                if len(namepiv) < len(name):
                    length = len(namepiv)
                elif len(namepiv) > len(name):
                    length = len(name)
                else:
                    length = len(namepiv)

                # Does the comparing of two letters at the same index
                for i in range(length):
                    if namepiv[i] > name[i]:
                        less.append(dictionary[index])
                        break
                    elif namepiv[i] < name[i]:
                        more.append(dictionary[index])
                        break
                    elif namepiv == name:
                        pivot_list.append(dictionary[index])
                        pivot_list = sort_drs(pivot_list, True)
                        break
                    else:
                        #logging.debug("Comparing: %s, %s" % (namepiv[i], name[i]))
                        pass
                less = sort_drs(less)
                more = sort_drs(more)
            #logging.debug("final %s + %s + %s" % (less, pivot_list, more))
            return less + pivot_list + more
        except (AttributeError, TypeError):
            pass


if __name__ == "__main__":
    # gets current working directory then splits it into a list for data extraction
    listPath = os.getcwd().split(os.path.sep)
    # this is the new path we'll save the data file under. C:\Users\USERNAME\Desktop
    newPath = r'C:\Users\%s\Desktop' % str(listPath[2])
    os.chdir(newPath)

    if os.path.exists('./faxnum.txt') or os.path.exists('./sortedfaxnum.txt'):
        pass
    else:
        q = open("sortedfaxnum.txt", "w")
        q.close()
        f = open("faxnum.txt", "w")
        f.close()
    with open('faxnum.txt') as f:
        data = json.load(f)
        sorted_data = data["doctors"]
    sorted_data = sort_alphabet(sorted_data)
    for length in range(len(sorted_data)):
        unsorted_drs = sort_alphabet(sorted_data[length])  # "a": [{'last':},..]
        for keys, values in unsorted_drs.items():
            sorted_drs = sort_drs(values)
            sorted_data[length][keys] = sorted_drs

    with open('sortedfaxnum.txt', "w") as q:
        q.write('{"doctors":\n')
        json.dump(sorted_data, q, indent=4)
        q.write('}')

    main()