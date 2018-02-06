# Auto-copy doctor's fax #'s by search

import os
import json
import sys
import re
import pyperclip
import logging
import getpass

logging.basicConfig(level=logging.DEBUG)
#logging.disable(logging.DEBUG)


def main():
    arg = input('\n"LAST" or "LAST FIRST" to search. "Help" to display commands: ').lower()

    # regex to check for <commands> <arg(s)> or <last> +/- <first> name searches
    command_regex = re.compile(r'''
                                (\s*[a-zA-Z]+)          # group(1)  <commands>          or      <lastN>
                                ((\s*) (,)? (\s*))?     
                                ([a-zA-Z]+)?            # group(6)  <lastN>             or      <firstN>
                                ((\s*) (,)? (\s*))?
                                ([a-zA-Z]+)?            # group(11) <firstN> or None      
                                ((\s*) (,)? (\s*))?

                                ( \( )?
                                (\d{3})?                # group(17) <###>
                                ( \) )?
                                (\s | - | \.)?
                                (\d{3})?                # group(20) <###>
                                (\s | - | \.)?
                                (\d{4})?                # group(22) <####>
                               ''', re.VERBOSE | re.IGNORECASE)

    phone_regex = re.compile(r'''
                              ( \( )?
                              (\d{3})?                # group(2) <###>
                              ( \) )?
                              (\s | - | \. | \\ | //)?
                              (\d{3})?                # group(5)
                              (\s | - | \. | \\ | //)?
                              (\d{4})?                # group(7)
                             ''', re.VERBOSE)

    try:
        command = command_regex.match(arg).group(1).strip(' ')  # <command> <firstN> <lastN2> <fax>
        lastN = command_regex.search(arg).group(1)              # <lastN> <firstN>
        firstN = command_regex.search(arg).group(6)
        lastN2 = command_regex.search(arg).group(11)
        areacode = command_regex.search(arg).group(17)
        phone1 = command_regex.search(arg).group(20)
        phone2 = command_regex.search(arg).group(22)

        fax = None

        if areacode and phone1 and phone2:
            fax = areacode + phone1 + phone2

        # if re.search(command, 'add, edit, del, list'):
        if command == 'help':
            print('\n---------COMMAND----------------------------------DESCRIPTION------------------')
            print('1. LIST                                  lists ALL entries')
            print('2. ADD  <LASTNAME, FIRSTNAME, FAX#>      to add entry LASTN/FIRSTN/FAX#')
            print('3. EDIT <LAST NAME/PARTS OF LAST NAME>   to edit entry LASTN/FIRSTN/FAX#\n\n')
            main()
        elif command == 'add':
            # TODO FIX SO CANT ADD 2: LCHC NONE <fax> or etc.
            # TODO FIX SORTING ISSUE WITH '' or ' '

            if firstN and fax:
                if lastN2 == None:
                    lastN2 = ''
                else:
                    lastN2 = lastN2.lower()

                firstN = firstN.lower()

                add_entry(firstN, lastN2, fax)
            else:  # if not lastN and not firstN and not fax:

                print("\nIf first or last name has 2 parts, make it into 1. e.g. Del Rio = Delrio")
                last = input("Enter last name:").lower().strip(' ')
                first = input("Enter first name:").strip(' ')
                fax = input("Enter fax number [Must have 10 digits]:")

                if first == None or first == '':
                    pass
                else:
                    first = first.lower()

                areacode = phone_regex.search(fax).group(2)
                phone1 = phone_regex.search(fax).group(5)
                phone2 = phone_regex.search(fax).group(7)

                if areacode and phone1 and phone2:
                    fax = areacode + phone1 + phone2
                else:
                    fax = input("Try again [Must have 10 digits]:")

                while len(fax) == 10:
                    add_entry(last, first, fax)

        elif command == 'edit':
            print("True: %s. Use <command> to map to functions" % command)

        elif command == 'del':
            print("True: %s. Use <command> to map to functions" % command)

        elif command == 'list':
            list_data()

        elif lastN != None:
            print("Performing lookup")
            lookup(lastN, firstN)
        main()
    except (AttributeError, IndexError, TypeError):
        print('Invalid command, try again\n')
        main()


def lookup(lastN, firstN=None, add=False):
    #logging.disable(logging.DEBUG)

    result_counter, search_counter = 0, 0
    temp_dict = {}      # used for user number input selection for 2+ search results
    search_results = {}    

    # Iterate through each listed index of the data (doctors key). Filters last names             
    for letter in sorted_data:                  # gets entire alphabet lettered dictionary: {"a": vals}
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
        if add:
            print(search_results)
            return search_results
        else:
            if search_counter == 0:     # No search results
                display_results(search_counter, '%s, %s' % (lastN, firstN))
            else:
                display_results(search_counter, search_results)

    if add and not firstN:
        return temp_dict
    elif add:
        return search_results

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
        result = '{:>5}, {:>5} {:>13}'.format(temp_dict[1]["last"], temp_dict[1]["first"], temp_dict[1]["fax"]).upper()
        pyperclip.copy(temp_dict[1]["fax"])
        print('Found %s result' % result_counter)
        print('Copied fax number for: %s \n' % result)
    elif result_counter > 1:
        print('LAST'.center(12, '-'), 'FIRST'.center(11, '-'), 'FAX'.center(12, '-'))
        
        for i in range(1, result_counter+1):
            result = '{} {:>10} {:>10} {:>13}'.format(i, temp_dict[i]["last"], temp_dict[i]["first"], temp_dict[i]["fax"]).upper()
            print(result)
        print('Found %d results\n' % result_counter)

        while True:
            try:
                num_input = int(input('Enter a number between {}-{} to copy fax number (0 for main menu): '
                                      .format('1', result_counter)))
                if result_counter >= num_input and num_input >= 1:
                    result = '{:>5}, {:>5} {:>13}'\
                        .format(temp_dict[num_input]["last"], temp_dict[num_input]["first"], temp_dict[num_input]["fax"]).upper()
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
    global sorted_data
    sorted_data = sort_alphabet(sorted_data)

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
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"]).upper()
                else:
                    entry = '{} {:>10} {:>10} {:>13}'\
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"]).upper()
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


def add_entry(last=None, first=None, fax=None):

    def add_person():
        lists.append(entry_dict)
        print("Added person: %s, %s %s" % (last.upper(), first, fax))

    entry_dict, letter_dict = {}, {}
    entry_list = []
    seenLetter = False

    if first == None or first == '':
        first = ''
    else:
        first.upper()

    #TODO FIX REGEX ISSUE-----------------
    if len(fax) == 10:
        fax = '1' + fax

    entry_dict["last"] = last
    entry_dict["first"] = first
    entry_dict["fax"] = fax

    newletter = str(last[0])
    entry_list.append(entry_dict)
    letter_dict[newletter] = entry_list

    result_list = lookup(last, first, True)

    try:
        for index in range(len(sorted_data)):
            for letters, lists in sorted_data[index].items():
                if newletter == letters:  # last[0] == letters
                    seenLetter = True

                    for keys, listed in result_list.items():  # uses lookup function to check if last, first exists
                        if last == listed["last"] and first == listed["first"] and fax == listed["fax"]:
                            print(fax)
                            print(listed["fax"])
                            print("Person already exists: %s, %s %s" % (last, first, fax))
                            break
                        elif last == listed["last"] and first == listed["first"] and fax != listed[
                            "fax"] and keys == len(result_list):
                            decision = int(input(
                                "A different fax # exists for the same person. Enter a number: \n0. Main menu "
                                "\n1. Add new person \n2. Replace with new fax # \n3. Edit entry \n4. Delete entry"))

                            if decision == 0:
                                main()
                            elif decision == 1:
                                print("2 adding")
                                add_person()
                                print(lists)
                                save(sorted_data)
                                main()
                            elif decision == 2:
                                newfax = input('Enter a new fax number:')
                                # fax = newfax
                            break

                    if not result_list:
                        print("1 adding")
                        add_person()
                        save(sorted_data)
                        break
                    elif result_list:
                        for val in result_list.values():
                            if (last != val["last"] or last == val["last"]) and first != val["first"]:
                                print("3 adding")
                                add_person()
                                save(sorted_data)
                                break

                elif not seenLetter and index == len(sorted_data) - 1:  # last[0] does not exist & reached end of index
                    sorted_data.append(letter_dict)
                    if first != None: first = first.upper()
                    print("Added person: %s, %s %s" % (last.upper(), first, fax))
                    save(sorted_data)
                    break
        main()
    except TypeError:
        pass


# Saves all data to this file
def save(newdata):

    for length in range(len(newdata)):
        unsorted_drs = sort_alphabet(newdata[length])  # "a": [{'last':},..]
        for keys, values in unsorted_drs.items():
            sorted_drs = sort_drs(values)
            newdata[length][keys] = sorted_drs

    with open('faxnum.txt', "w") as q:
        q.write('{"doctors":\n')
        json.dump(newdata, q, indent=4)
        q.write('}')


if __name__ == "__main__":

    if sys.platform == 'darwin':        # If Mac OS 'Darwin'
        pass
    elif sys.platform == 'win32':       # If Windows
        # gets current working directory then splits it into a list for data extraction
        # this is the new path we'll save the data file under. C:\Users\USERNAME\Desktop
        listPath = os.getcwd().split(os.path.sep)
        if str(listPath[0]) != 'C':
            #os.chdir(r'C:\Users\Robert\Desktop')
            os.chdir(r'C:\Users\%s\Desktop' % getpass.getuser())
        else:
            #newPath = r'C:\Users\%s\Desktop' % str(listPath[2])
            newPath = r'C:\Users\%s\Desktop' % getpass.getuser()
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

    with open('faxnum123.txt', "w") as p:
        p.write('{"doctors":\n')
        json.dump(sorted_data, p, indent=4)
        p.write('}')

    main()