# Auto-copy doctor's fax #'s by search

import os
import json
import sys
import re
import pyperclip
import logging
import getpass

from termcolor import colored

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

fax_regex = re.compile(r'''
                           ( \( )?
                           (\d{3})?                # group(2) <###>
                           ( \) )?
                           (\s | - | \. | \\ | //)?
                           (\d{3})?                # group(5)
                           (\s | - | \. | \\ | //)?
                           (\d{4})?                # group(7)
                         ''', re.VERBOSE)


def main():
    arg = input(colored('\n"LAST" or "LAST FIRST" to search. "Help" to display commands: ', 'magenta')).lower()

    try:
        command = command_regex.match(arg).group(1).strip(' ')  # <command> <firstN> <lastN2> <fax>
        lastN = command_regex.search(arg).group(1)  # <lastN> <firstN>
        firstN = command_regex.search(arg).group(6)
        lastN2 = command_regex.search(arg).group(11)
        areacode = command_regex.search(arg).group(17)
        phone1 = command_regex.search(arg).group(20)
        phone2 = command_regex.search(arg).group(22)

        commands = ['list', 'add', 'edit', 'del', 'massadd']

        # Renaming variable for readability if there is a command
        if command in commands:
            last = firstN
            first = lastN2

        # TODO FIX MENU IN END
        if command == 'help':
            print('\n---------COMMAND----------------------------------DESCRIPTION------------------')
            print('1. LIST                                  lists ALL entries')
            print('2. ADD  <LASTNAME> [FIRSTNAME] <FAX>     to add entry LASTN/FIRSTN/FAX#')
            print('2. MASSADD                               add multiple entries w/o getting main menu')
            print('3. EDIT <LASTNAME> [FIRSTNAME]           to edit entry LASTN/FIRSTN/FAX#')
            print('4. DEL  <LASTNAME> [FIRSTNAME]           list entries w/ last name to delete')
            print('5. EXAMPLES                              list examples of commands')
            print('6. Typing a last name defaults to searching file for that last name')
            main()
        elif command == 'list':
            counter, letter_index, index_dict, results, arg = lookup(None, None, True)
            display_results(counter, letter_index, index_dict, results, command)
        elif command == 'add':
            if areacode and phone1 and phone2:
                fax = '1' + areacode + phone1 + phone2

            if last:
                phone = None
            else:
                last, first, fax, phone = add_prompt()

            counter, letter_index, index_dict, results, arg = lookup(last, first, False)
            decision = display_results(counter, [last, first], index_dict, results, command)

            if isinstance(decision, bool):
                add_entry(results, last, first, fax, phone)
            elif decision == 1:
                modify_entry('fax', letter_index, index_dict, results, last, first, fax)
            elif decision == 2:
                modify_entry('edit', letter_index, index_dict, results, last, first, None)
            elif decision == 3:
                modify_entry('del', letter_index, index_dict, results, last, first, None)

        elif command == 'massadd':
            print('Enter: <LAST> <FIRST> <FAX> <PHONE>')
            add_entry(None, '', '', '', '', True)

        elif command == 'edit' or command == 'del':
            if not last:
                last = re.search(r'[a-zA-Z]+',
                                 input("Enter last name of person you would like to modify: ")).group().lower().strip(' ')

            counter, letter_index, index_dict, results, arg = lookup(last, first, False)
            result, first = display_results(counter, [last, first], index_dict, results, command)
            modify_entry(command, letter_index, index_dict, result, last, first, None)

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

        elif lastN:
            counter, letter_index, index_dict, results, arg = lookup(lastN, firstN, False)
            display_results(counter, letter_index, index_dict, results, 'lookup')
    except (AttributeError, IndexError, TypeError, UnboundLocalError):
        print('Invalid command, try again\n')

    main()


# Prompts user for new entry information if 'add <last> <first> <fax>' not performed correctly on commandline
def add_prompt():
    try:
        print("\nIf first or last name has 2 parts, make it into 1. e.g. Del Rio = Delrio")

        last = re.search(r'[a-zA-Z]+', input("Enter last name (req): ")).group().lower().strip(' ')
        first = re.search(r'[a-zA-Z]*', input("Enter first name: ")).group().lower().strip(' ')
        fax = '1' + ''.join(
            re.search(fax_regex, input("Enter 10-digit fax number 1+[###-###-####] (req): ")).group(2, 5, 7))
        phone = input("Enter phone number: ")

        # Formats phone accordingly if None or checks with regex if has input
        if not phone:
            phone = ''
        elif phone:
            phone = re.search(fax_regex, phone).group(2, 5, 7)
            phone = '({}) {}-{}'.format(phone[0], phone[1], phone[2])

        return last, first, fax, phone
    except (AttributeError, TypeError):
        print('Something was entered incorrectly, try again.')


def lookup(lastN, firstN=None, arg=False):  # add=False, phones=False):
    # print(lastN, firstN, arg)
    results = {}  # {"last": "name", "first": "name", "fax": "num", "phone": "num"}
    index_dict = {}  # {1: 0, 2: 1, 3: 2}
    results_list = []

    try:
        # Lists all doctors
        if arg:
            for letter_dict in sorted_data:
                for letter, letter_list in letter_dict.items():
                    for index in letter_list:
                        results_list.append(index)
            for counter, doctor in enumerate(results_list, 1):
                results[counter] = doctor
                index_dict[counter] = doctor["last"][0]
            li = 0
        # Iterate through each listed index of the data (doctors key). Filters last names
        elif not arg:
            letter_index, entry_index = 0, 0
            for letter in sorted_data:
                if lastN[0] in letter:
                    for doctor in letter[lastN[0]]:
                        # Filter both last and first name
                        if lastN in doctor["last"] and (bool(firstN)
                                                        and firstN[0] in doctor["first"][0]
                                                        and firstN in doctor["first"]):
                            results[entry_index] = doctor  # stores doctor into results
                        # Filter only last name
                        elif lastN in doctor["last"] and not bool(firstN):
                            results[entry_index] = doctor  # stores doctor into results
                        li = letter_index  # letter index after sorted, a=0, b=1, c=2, d=3, e=4
                        entry_index += 1
                letter_index += 1
            # Stores the index of the doctor to allow for modifying entry
            for counter, index in enumerate(results, 1):  # index = entry_index
                index_dict[counter] = index  # {counter: index}    {index: entry}
    except (IndexError, AttributeError):
        pass

    if not results:
        return 0, None, None, None, None
    elif results:
        return counter, li, index_dict, results, arg


def add_entry(results, last=None, first=None, fax=None, phone=None, massadd=False):
    def add_person(firstn):
        lists.append(entry_dict)
        firstn = check_first(firstn)
        print("Added person: " + colored("%s, %s, %s, %s \n" % (last.upper(), firstn, fax, phone), 'red'))

    def check_first(upper_first):
        if upper_first:
            upper_first = upper_first.upper()
        return upper_first

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

    if not first:
        first = ''

    if not phone:
        phone = ''

    entry_dict, letter_dict = {}, {}
    entry_list = []

    entry_dict["last"] = last
    entry_dict["first"] = first
    entry_dict["fax"] = fax
    entry_dict["phone"] = phone

    new_letter = str(last[0])
    entry_list.append(entry_dict)
    letter_dict[new_letter] = entry_list

    try:
        if not sorted_data:  # len(sorted_data) == 0:
            sorted_data.append(letter_dict)
            first = check_first(first)
            print("Added person: " + colored("%s, %s, %s, %s \n" % (last.upper(), first, fax, phone), 'red'))
        else:
            firstn_list = []
            seen_letter = False

            for index in range(len(sorted_data)):
                for letters, lists in sorted_data[index].items():
                    if new_letter == letters:  # if last[0] is in alphabet. last[0] == letters
                        seen_letter = True

                        if not results:
                            add_person(first)
                            break
                        elif results:
                            for entry in results.values():
                                firstn_list.append(entry["first"])  # append first names to list to check later
                            if first not in firstn_list:
                                add_person(first)
                                break
                    # last[0] does not exist & reached end of index
                    elif not seen_letter and index == len(sorted_data) - 1:
                        sorted_data.append(letter_dict)
                        first = check_first(first)
                        print(
                            "Added person: " + colored("%s, %s, %s, %s \n" % (last.upper(), first, fax, phone), 'red'))
                        break
    except TypeError:
        pass

    save(sorted_data)

    if massadd:
        add_entry(None, '', '', '', '', True)
    else:
        main()


def display_results(counter, letter_index, index_dict, results, arg):
    # print(counter, letter_index, index_dict, results, arg)
    # print()

    longest_last, longest_first = 0, 0
    matched = False

    def print_column():
        print('{:>3} {} {} {} {}'.format(' ',
                                         'LAST'.center(longest_last, '-'),
                                         'FIRST'.center(longest_first, '-'),
                                         'FAX'.center(13, '-'),
                                         'PHONE'.center(15, '-')))

    if results and arg == 'add':
        for match in results.values():
            if letter_index[0] == match["last"] and letter_index[1] == match["first"]:
                result = '{}, {}, {}, {}'.format(match["last"], match["first"], match["fax"], match["phone"]).upper()
                matched = True
                break

    listed_result = []
    # Defaults phone number to empty if none found. Formats length of columns and justification to longest length name
    if counter != 0:
        for entry in results.values():
            if 'phone' not in entry:
                entry["phone"] = ''
            if len(entry["last"]) > longest_last:
                longest_last = len(entry["last"])
            if len(entry["first"]) > longest_first:
                longest_first = len(entry["first"])
            fax = entry["fax"]
            listed_result.append([entry["last"], entry["first"], entry["fax"], entry["phone"]])

        # Makes columns centered with even amount of '-' on each side
        if longest_last % 2 == 0:
            longest_last += len('LAST')
        else:
            longest_last += len('LAST') + 1
        if longest_first % 2 != 0:
            longest_first += len('FIRST')
        else:
            longest_first += len('FIRST') + 1

    # Prints the results from the lookup function results
    if counter > 1 and arg != 'add':
        enum_result = {}
        letter_dict = {}
        i = 0

        # Maps the keys of index_dict to the values of results for easy access to the entry's index in the data file
        for key in index_dict:
            for value in results.values():
                if value not in enum_result.values():
                    enum_result[key] = value
                    break
                else:
                    continue

        # Iterates through the enumerated results to be printed
        for key, value in enum_result.items():
            last = value["last"]
            first = value["first"]
            fax = value["fax"]
            phone = value["phone"]

            # Print initial column setup
            if not letter_dict:
                print_column()
            # If command 'list', iterating through the enum_result, add each new letter to a dict, else value += 1
            if last[0] not in letter_dict and key > 1:
                i = 1
                letter_dict[last[0]] = i
                print()  # Separates last names by letter
                if len(letter_dict) % 6 == 0:  # Print column after every 5 letters
                    print_column()
            else:
                i += 1
                letter_dict[last[0]] = i
            # Prints each entry line by line
            print('{:>3} {} {} {} {}'.format(key,
                                             last.rjust(longest_last),
                                             first.rjust(longest_first),
                                             fax.rjust(13),
                                             phone.rjust(15)).upper())
        print('Found %s results\n' % counter)

    # Copies fax numbers based on decision
    try:
        if counter > 1 and arg != 'add':
            decision = int(
                input(colored("Enter a number to select entry. (Otherwise 'Enter' for main menu): ", 'magenta')))
            if counter >= decision >= 1 and decision in enum_result:
                # if decision in enum_result:
                result = '{}, {}, {}, {}'.format(enum_result[decision]["last"],
                                                 enum_result[decision]["first"],
                                                 enum_result[decision]["fax"],
                                                 enum_result[decision]["phone"]).upper()
                fax = enum_result[decision]["fax"]

        if arg == 'add':
            if matched:
                print(colored('%s ' % result, 'red') + 'already exists!')
                print('What would you like to do? ')
                decision = int(input(
                    "1. Replace with new fax # \n2. Edit entry "
                    "\n3. Delete entry \n'Enter' for main menu\n"
                    + colored("Select an option: ", 'magenta')))
                print()
                return decision
            elif not matched:
                return True
        elif arg == 'edit' or arg == 'del':
            if counter == 0:
                print("No results found\n")
            elif counter == 1:
                first = results[index_dict[counter]]["first"]
                return results, first
            elif counter > 1:
                result = {}
                index = index_dict.get(decision)

                if index in results:
                    result[index] = results[index]
                    return result, results[index]["first"]

        elif arg == 'lookup' or arg == 'list':
            if counter == 0:
                print("No results found\n")
            elif counter == 1:
                # pyperclip.copy(fax)
                result = ', '.join(listed_result[0]).upper()
                print('Found %s result: ' % counter + colored(('%s' % result), 'red'))
                print('Fax number copied\n')
            elif counter > 1:
                # pyperclip.copy(fax)
                print('Fax number copied for: ' + colored(('%s \n' % result), 'red'))
    except (KeyError, ValueError, UnboundLocalError, IndexError):
        pass


def modify_entry(arg, letter_index, index_dict, results, last, first=None, fax=None):
    # print(arg, letter_index, index_dict, results, last, first, fax)
    doctor_index = 0

    for index, doctor in results.items():
        if last in doctor["last"]:
            doctor_index = index
            break

    doctor = sorted_data[letter_index][last[0]][doctor_index]

    if doctor["first"]:
        entry_first = doctor["first"].upper()
    else:
        entry_first = doctor["first"]
    entry_last = doctor["last"].upper()
    entry_fax = doctor["fax"]
    entry_phone = doctor["phone"]

    try:
        if arg == 'fax':
            print('Old fax: ' + colored(doctor["fax"], 'red') + '--> New fax: ' + colored(fax, 'red'))
            doctor["fax"] = fax
        elif arg == 'edit':

            ask_last = "What would you like to change last name " + colored(entry_last, 'red') + " to?: "
            ask_first = "What would you like to change first name " + colored(entry_first, 'red') + " to?: "
            ask_fax = "What would you like to change fax number " + colored(entry_fax, 'red') + " to?: "
            ask_phone = "What would you like to change phone number " + colored(entry_phone, 'red') + " to?: "

            print('\nWhat would you like to edit about: ' + colored(
                '%s, %s, %s, %s' % (entry_last, entry_first, entry_fax, entry_phone), 'red'))
            print("1. Last Name")
            print("2. First Name")
            print("3. Fax Number")
            print("4. Phone Number")
            print("5. All the Above")
            decision = int(input(colored("\nEnter a number: ", 'magenta')))

            if decision == 1:
                entry_last = re.search(r'[a-zA-Z]+', input(ask_last)).group().lower().strip(' ')
            elif decision == 2:
                entry_first = re.search(r'[a-zA-Z]*', input(ask_first)).group().lower().strip(' ')
            elif decision == 3:
                entry_fax = '1' + ''.join(re.search(fax_regex, input(ask_fax)).group(2, 5, 7))
            elif decision == 4:
                entry_phone = input(ask_phone)
            elif decision == 5:
                entry_last = re.search(r'[a-zA-Z]+', input(ask_last)).group().lower().strip(' ')
                entry_first = re.search(r'[a-zA-Z]*', input(ask_first)).group().lower().strip(' ')
                entry_fax = '1' + ''.join(re.search(fax_regex, input(ask_fax)).group(2, 5, 7))
                entry_phone = input(ask_phone)

            if entry_last[0] != last[0]:
                del sorted_data[letter_index][last[0]][doctor_index]
                add_entry(None, entry_last, entry_first, entry_fax, entry_phone)
            else:
                if not entry_phone:
                    entry_phone = ''
                elif entry_phone:
                    entry_phone = re.search(fax_regex, entry_phone).group(2, 5, 7)
                    if entry_phone[0] and entry_phone[1] and entry_phone[2]:
                        entry_phone = '({}) {}-{}'.format(entry_phone[0], entry_phone[1], entry_phone[2])
                    else:
                        entry_phone = ''

                doctor["last"] = entry_last
                doctor["first"] = entry_first
                doctor["fax"] = entry_fax
                doctor["phone"] = entry_phone
                print('New Entry: ' + colored(
                    '{}, {}, {}, {}'.format(entry_last.upper(), entry_first, entry_fax, entry_phone), 'red'))
        elif arg == 'del':
            decision = input(colored("(y/n) Are you sure you want to delete: ", 'magenta')
                             + colored('%s, %s, %s, %s ' % (entry_last, entry_first, entry_fax, entry_phone),
                                       'red')).lower()

            if decision == 'y':
                print(
                    "Deleted: " + colored('%s, %s, %s, %s ' % (entry_last, entry_first, entry_fax, entry_phone), 'red'))
                del sorted_data[letter_index][last[0]][doctor_index]

        letter_size = len(sorted_data[letter_index][last[0]])
        temp_letter = last[0]

        if not letter_size:
            sorted_data[letter_index][temp_letter] = 1
            del sorted_data[letter_index]
    except (ValueError, UnboundLocalError, NameError):
        pass
    save(sorted_data)


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
            os.chdir(r'C:\Users\%s\Desktop' % getpass.getuser())
        else:
            newPath = r'C:\Users\%s\Desktop' % getpass.getuser()
            os.chdir(newPath)

    if os.path.exists('./faxnum.txt'):
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
