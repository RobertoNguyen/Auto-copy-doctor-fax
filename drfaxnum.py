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

def main():
    arg = input('\n"LAST" or "LAST FIRST" to search. "Help" to display commands: ').lower()

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
            fax = '1' + areacode + phone1 + phone2


        if command == 'help':
            print('\n---------COMMAND----------------------------------DESCRIPTION------------------')
            print('1. LIST                                  lists ALL entries')
            print('2. ADD  <LASTNAME> [FIRSTNAME] <FAX>     to add entry LASTN/FIRSTN/FAX#')
            print('2. MASSADD                               add multiple entries w/o getting main menu')
            print('3. EDIT <LASTNAME> [FIRSTNAME]           to edit entry LASTN/FIRSTN/FAX#')
            print('4. DEL  <LASTNAME> [FIRSTNAME]           list entries w/ last name to delete')
            print('5. PHONES                                search by phone numbers')
            print('6. EXAMPLES                              list examplex of commands')
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
                last = input("Enter last name: ").lower().strip(' ')
                first = input("Enter first name: ").strip(' ')
                fax = input("Enter 10-digit fax number 1+[###-###-####]: ")
                phone = input("Enter phone number: ")

                if first == None or first == '':
                    pass
                else:
                    first = first.lower()

                if len(fax) < 10:
                    fax = input("Try again [Fax must have 10 digits]:")

                areacode = phone_regex.search(fax).group(2)
                fax1 = phone_regex.search(fax).group(5)
                fax2 = phone_regex.search(fax).group(7)

                if areacode and fax1 and fax2:
                    fax = '1' + areacode + fax1 + fax2
                    add_entry(last, first, fax, phone)
        elif command == 'massadd':
            print('Enter: <LAST> <FIRST> <FAX> <PHONE>')
            add_entry('', '', '', '', True)

        elif command == 'phones':
            search_phone(command_regex)
            
        elif command == 'edit':
            modify_entry(firstN, lastN2, fax, True)

        elif command == 'del':
            modify_entry(firstN, lastN2)

        elif command == 'list':
            list_data()

        elif command == 'examples':
            print('\n------------------------------------EXAMPLES------------------------------------')
            print('command <last> <first>')
            print('<last> & <first> can be any substring length of the name being searched')
            print('\nFUNCTION__|______________VARIOUS WAYS FOR COMMANDS______________________________')
            print('search:   | lin, david | lin david | l d | lin d | li da ')
            print('add:      | add lin david 1234567890 | add lin 1234567890 (10 digit fax w/o \'1\')')
            print('massadd:  | add lin david 11234567890 (11 digit fax w/ leading \'1\')')
            print('edit:     | edit lin | edit li  | edit lin david | edit l d ')
            print('del:      | del lin  | del  li da | del l')

        elif lastN != None:
            lookup(lastN, firstN)
    except (AttributeError, IndexError, TypeError):
        print('Invalid command, try again\n')

    main()


def lookup(lastN, firstN=None, add=False, phones=False):
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
            if firstN[0] in temp_dict[i]["first"][0]:
                search_counter += 1
                search_results[search_counter] = temp_dict[i]
        if add and not phones:
            return search_results
        elif not phones:
            if search_counter == 0:     # No search results
                display_results(search_counter, '%s, %s' % (lastN, firstN))
            else:
                display_results(search_counter, search_results)

    # Returns to add_entry function to check name exists or not
    if add and not firstN:
        return temp_dict
    elif add:
        return search_results

    if phones:
        phone_dict = {}
        phone_counter = 0
        if firstN:
            nameList = search_results
        else:
            nameList = temp_dict

        for key, entry in nameList.items():
            if 'phone' in entry and len(entry["phone"]) > 8:
                phone_counter += 1
                phone_dict[phone_counter] = entry

        display_results(phone_counter, phone_dict, True)

    # <lastN>
    if result_counter == 0:         # No search results
        display_results(result_counter, lastN)
    else:
        display_results(result_counter, temp_dict)


# Takes arguments from lookup function and displays to user based on # of results
def display_results(result_counter, temp_dict, phones=False):
    if phones:
        title = 'phone'
        column_title = 'PHONE'
    else:
        title = 'fax'
        column_title = 'FAX'

    if result_counter == 0:
        if phones:
            print('No results found\n')
        else:
            print('No results found for: %s \n' % temp_dict)
    elif result_counter == 1:
        result = '{:>5}, {:>5} {:>13}'.format(temp_dict[1]["last"], temp_dict[1]["first"], temp_dict[1][title]).upper()

        if phones:
            print(result)
        else:
            pyperclip.copy(temp_dict[1]["fax"])
            print('Found %s result' % result_counter)
            print('Copied fax number for: %s \n' % result)

    elif result_counter > 1:
        print('  ', 'LAST'.center(15, '-'), 'FIRST'.center(16, '-'), column_title.center(13, '-'))

        for i in range(1, result_counter + 1):
            result = '{:>2} {:>15} {:>16} {:>13}'.format(i, temp_dict[i]["last"], temp_dict[i]["first"],
                                                         temp_dict[i][title]).upper()
            print(result)

        try:
            num_input = int(input(
                '\nEnter a number between {}-{} for {} number (0 for main menu/Enter to search again): '
                    .format('1', result_counter, title)))
            if result_counter >= num_input and num_input >= 1:
                result = '{:>5}, {:>5} {:>13}'.format(temp_dict[num_input]["last"], temp_dict[num_input]["first"],
                                                      temp_dict[num_input][title]).upper()

                if phones:
                    print(result)
                else:
                    pyperclip.copy(temp_dict[num_input]["fax"])
                    print('Copied fax number for: %s \n' % result)
            elif num_input == 0:
                print()
                main()

        except (ValueError, KeyError):
            pass
    if phones:
        search_phone(command_regex)
    else:
        main()


# Lists all doctors
def list_data():
    temp_dict = {}
    result_counter = 0  # resets counter if already been used before in other functions

    for letters in range(len(sorted_data)):
        if letters % 5 == 0: print('  ', 'LAST'.center(16, '-'), 'FIRST'.center(16, '-'), 'FAX'.center(12, '-'),
                                   'PHONE'.center(15, '-'))
        for dr in sorted_data[letters].values():
            for index in range(len(dr)):

                if 'phone' not in dr[index]:
                    dr[index]['phone'] = ''

                result_counter += 1
                temp_dict[result_counter] = dr[index]

                if result_counter < 100:
                    entry = '{:>3} {:>15} {:>16} {:>12} {:>15}' \
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"],
                                dr[index]["phone"]).upper()
                else:
                    entry = '{} {:>14} {:>16} {:>13} {:>15}' \
                        .format(result_counter, dr[index]["last"], dr[index]["first"], dr[index]["fax"],
                                dr[index]["phone"]).upper()
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


def add_entry(last=None, first=None, fax=None, phone=None, massadd=False):
    def add_person(first):
        lists.append(entry_dict)
        if first == None or first == '':
            first = ''
        else:
            first = first.upper()
        print("Added person: %s, %s %s %s" % (last.upper(), first, fax, phone))

    entry_dict, letter_dict = {}, {}
    entry_list = []
    seenLetter = False

    if last == '' and first == '' and fax == '' and phone == '':
        arg = input('(Enter to exit) Add: ').lower().split()

        if arg[-1] == "''":
            arg[-1] = ''
        print(arg)
        if len(arg) == 5:
            last = arg[0]
            first = arg[1]
            fax = arg[2]
            phone = "".join(arg[3:])  # + ' ' + arg[4]
        elif len(arg) == 4:
            last = arg[0]
            first = arg[1]
            fax = arg[2]
            phone = arg[3]
        elif len(arg) == 3:  # TODO regex for <last><first><fax> and <last><fax><phone>
            if arg[-1] == '':
                last = arg[0]
                first = ''
                fax = arg[1]
                phone = ''
            # else

    if phone == None or phone == '':
        phone = ''

    if first == None or first == '':
        first = ''
    else:
        first.upper()

    entry_dict["last"] = last
    entry_dict["first"] = first
    entry_dict["fax"] = fax
    entry_dict["phone"] = phone

    newletter = str(last[0])
    entry_list.append(entry_dict)
    letter_dict[newletter] = entry_list

    result_list = lookup(last, first, True)

    try:
        if len(sorted_data) == 0:
            sorted_data.append(letter_dict)
            if first != None: first = first.upper()
            print("Added person: %s, %s %s %s" % (last.upper(), first, fax, phone))
        else:
            for index in range(len(sorted_data)):
                for letters, lists in sorted_data[index].items():
                    if newletter == letters:  # last[0] == letters
                        seenLetter = True

                        for keys, listed in result_list.items():  # uses lookup function to check if last, first exists
                            if last == listed["last"] and first == listed["first"] and fax == listed["fax"]:
                                print("Person already exists: %s, %s %s %s" % (last, first, fax, phone))
                                break
                            elif last == listed["last"] and first == listed["first"] and fax != listed[
                                "fax"] and keys == len(result_list):

                                results = '{}, {}, {} {}'.format(listed["last"].upper(), listed["first"].upper(),
                                                                 listed["fax"], listed["phone"])
                                decision = int(input(
                                    "A different fax # exists for the same person: " + results +
                                    "\n0. Main menu \n1. Replace with new fax # "
                                    "\n2. Edit entry \n3. Delete entry \nEnter a number:"))

                                if decision == 0:  # main menu
                                    pass
                                elif decision == 1:  # replace old fax #
                                    listed["fax"] = fax
                                elif decision == 2:  # edit searched entry
                                    modify_entry(listed["last"], listed["first"], listed["fax"], True)
                                elif decision == 3:
                                    modify_entry(listed["last"], listed["first"])
                        if not result_list:
                            add_person(first)
                            break
                        elif result_list:
                            for val in result_list.values():
                                if (last != val["last"] or last == val["last"]) and first != val["first"]:
                                    add_person(first)
                                    break
                    elif not seenLetter and index == len(
                            sorted_data) - 1:  # last[0] does not exist & reached end of index
                        sorted_data.append(letter_dict)
                        if first != None: first = first.upper()
                        print("Added person: %s, %s %s %s" % (last.upper(), first, fax, phone))
                        break
    except TypeError:
        pass

    save(sorted_data)
    if massadd:
        add_entry('', '', '', '', True)
    else:
        main()


def modify_entry(last, first=None, fax=None, edit=False):
    letter_index, entry_index = 0, 0
    temp_dict = {}  # {1: '2string', 2: '3string', 3: '4string'} extracts into the next 3 variables
    temp_list = []  # ['string', 'string', 'string']
    temp_index_list = []  # [2, 3, 4]
    get_index_dict = {}  # {1: 2, 2: 3, 3: 4}

    try:
        for letter in sorted_data:  # gets entire alphabet lettered dictionary: {"a": vals}
            if last[0] in letter:  # gets list of key entries for letter: {last[0]: [{LIST}, {OF}, {VALUES}]}
                for doctor in letter[last[0]]:  # single entry. {'last': name, 'first': name, 'fax': ##########}

                    if 'phone' not in doctor:
                        doctor['phone'] = ''

                    if first:
                        if last in doctor["last"] and first in doctor["first"]:
                            result = '{:>15} {:>16} {:>13} {:>15}'.format(doctor["last"].upper(),
                                                                          doctor["first"].upper(),
                                                                          doctor["fax"], doctor["phone"])
                            temp_index_list.append(entry_index)
                            temp_list.append(result)
                    elif last in doctor["last"]:
                        result = '{:>15} {:>16} {:>13} {:>15}'.format(doctor["last"].upper(), doctor["first"].upper(),
                                                                      doctor["fax"], doctor["phone"])
                        temp_index_list.append(entry_index)
                        temp_list.append(result)
                    li = letter_index
                    entry_index = entry_index + 1
            letter_index = letter_index + 1

        for counter, result in enumerate(temp_list, 1):
            temp_dict[counter] = result

        i = 0
        if len(temp_index_list) >= 1:
            print()
            if len(temp_index_list) > 1:
                print(' ', 'LAST'.center(16, '-'), 'FIRST'.center(16, '-'), 'FAX'.center(13, '-'),
                      'PHONE'.center(15, '-'))

            while i != len(temp_index_list):
                for keys in temp_dict.keys():
                    get_index_dict[keys] = temp_index_list[i]
                    if len(temp_index_list) != 1:
                        print('', keys, temp_list[i])
                    i += 1

            if edit:
                if len(get_index_dict) == 1:
                    dec = 1
                else:
                    dec = int(input("Enter a number to edit entry: "))

                for key, val in get_index_dict.items():
                    if dec == key:
                        temp_index = val
                        entry_last = sorted_data[li][last[0]][val]["last"].upper()
                        entry_first = sorted_data[li][last[0]][val]["first"].upper()
                        entry_fax = sorted_data[li][last[0]][val]["fax"]
                        entry_phone = sorted_data[li][last[0]][val]["phone"]

                print('\nWhat would you like to edit about: %s, %s %s %s' % (
                entry_last, entry_first, entry_fax, entry_phone))
                print("0. Main Menu")
                print("1. Last Name")
                print("2. First Name")
                print("3. Fax Number")
                print("4. Phone Number")
                print("5. All the Above")
                decision = int(input("\nEnter a number: "))
                print(decision)

                if 5 >= decision >= 0:
                    if decision == 0:
                        main()
                    if decision == 1:
                        entry_last = input("What would you like to change last name %s to?: " % entry_last)
                        sorted_data[li][last[0]][temp_index]["last"] = entry_last.lower()
                        save(sorted_data)
                    elif decision == 2:
                        entry_first = input("What would you like to change first name %s to?:" % entry_first)
                        sorted_data[li][last[0]][temp_index]["first"] = entry_first.lower()
                        save(sorted_data)
                    elif decision == 3:
                        entry_fax = input("What would you like to change fax number %s to?: " % entry_fax)
                        sorted_data[li][last[0]][temp_index]["fax"] = entry_fax
                        save(sorted_data)
                    elif decision == 4:
                        entry_phone = input("What would you like to change phone number %s to?: " % entry_phone)
                        sorted_data[li][last[0]][temp_index]["phone"] = entry_phone
                        save(sorted_data)
                    elif decision == 5:
                        entry_last = input("What would you like to change last name %s to?: " % entry_last)
                        entry_first = input("What would you like to change first name %s to?: " % entry_first)
                        entry_fax = input("What would you like to change fax number %s to?: " % entry_fax)
                        entry_phone = input("What would you like to change phone number %s to?: " % entry_phone)

                        if entry_last[0] != last[0]:
                            del sorted_data[li][last[0]][temp_index]
                            if (entry_last != None or entry_last != '') and (entry_fax != None or entry_fax != '') \
                                    and len(entry_fax) == 10:
                                add_entry(entry_last, entry_first, entry_fax, entry_phone)
                        elif entry_last[0] == last[0]:
                            sorted_data[li][last[0]][temp_index]["last"] = entry_last.lower()
                            sorted_data[li][last[0]][temp_index]["first"] = entry_first.lower()
                            sorted_data[li][last[0]][temp_index]["fax"] = '1' + entry_fax
                            sorted_data[li][last[0]][temp_index]["phone"] = entry_phone
                            save(sorted_data)
            elif not edit:
                dec = int(input("Enter a number to delete entry: "))
                temp_index = None
                for key, val in get_index_dict.items():
                    if dec == key:
                        temp_index = val
                        entry_last = sorted_data[li][last[0]][val]["last"].upper()
                        entry_first = sorted_data[li][last[0]][val]["first"].upper()
                        entry_fax = sorted_data[li][last[0]][val]["fax"]

                decision = input(
                    "Are you sure you want to delete %s, %s %s? (y/n): " % (entry_last, entry_first, entry_fax)).lower()

                if decision == 'y':
                    print("Deleted: %s, %s %s" % (entry_last, entry_first, entry_fax))
                    del sorted_data[li][last[0]][temp_index]
                    save(sorted_data)

        letter_size = len(sorted_data[li][last[0]])
        temp_letter = last[0]

        if letter_size == 0 or letter_size == None:
            sorted_data[li][temp_letter] = 1
            del sorted_data[li]
            save(sorted_data)

    except (ValueError, UnboundLocalError, NameError):
        pass
    main()


# TODO NOT WORKING CAUSE REGEX IS IN MAIN FUNC
def search_phone(command_regex):
    try:
        phone_search = input('\nSearch by "LAST" or "LAST FIRST" (Enter for main menu): ')
        last = command_regex.search(phone_search).group(1)
        first = command_regex.search(phone_search).group(6)
        if last == 'list':
            list_data()
            search_phone(command_regex)
        else:
            lookup(last, first, False, True)
    except (ValueError, KeyError, UnboundLocalError, NameError, TypeError):
        pass


# Saves all data to this file
def save(newdata):
    #print(newdata)
    # TODO NEED TO FIX sort_alphabet/sort_drs so it knows how to sort entries w/o first name and w/ first name
    #for length in range(len(newdata)):
    #    unsorted_drs = sort_alphabet(newdata[length])  # "a": [{'last':},..]
    #    for keys, values in unsorted_drs.items():
    #        sorted_drs = sort_drs(values)
    #        newdata[length][keys] = sorted_drs

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

    if os.path.exists('./faxnum.txt') :
        with open('faxnum.txt') as f:
            data = json.load(f)
            sorted_data = data["doctors"]
            sorted_data = sort_alphabet(sorted_data)
        for length in range(len(sorted_data)):
            unsorted_drs = sort_alphabet(sorted_data[length])  # "a": [{'last':},..]
            for keys, values in unsorted_drs.items():
                sorted_drs = sort_drs(values)
                sorted_data[length][keys] = sorted_drs

        with open('faxnum.txt', "w") as q:
            q.write('{"doctors":\n')
            json.dump(sorted_data, q, indent=4)
            q.write('}')
    else:
        f = open("faxnum.txt", "w")
        f.write('{"doctors": []}\n')
        f.close()


    main()
