#!/usr/bin/env python3

# pgn2scid
# Version: 1.2
# Contact: andreaskreisig@gmail.com
# License: MIT

# Copyright (c) 2018 Andreas Kreisig
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys

if float(sys.version[:3]) < 3.4:
    sys.stderr.write("\nThis program requires Python 3.4 or above!\n\n")
    sys.exit(1)

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import PhotoImage
from tkinter.scrolledtext import *
from socket import timeout
from zipfile import BadZipFile
import configparser
import urllib.request
import urllib.error
import webbrowser
import subprocess
import tempfile
import shutil
import platform
import re
import os
import glob
import zipfile
import fileinput
import datetime
import time


# Displays an Error message box. Error level 1 means critical error, 2 means
# non critical error or warnings.  Warnings may also be displayed
# in the console window. Error levels >2 are for special purposes only.
def error_disp(err_level, err_head, err_msg, *args):
    if args:
        tk_parent = twic_file_select_window
    else:
        tk_parent = main_frame
    if err_level == 1:
        messagebox.showerror(err_head, err_msg, parent=tk_parent)
    elif err_level == 2:
        messagebox.showwarning(err_head, err_msg, parent=tk_parent)
    elif err_level == 3:
        w_dir = path_select_frame.get()
        root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        os.chdir(root_dir)
        if messagebox.askyesno(err_head, err_msg):
            if not os.path.isdir('pgn_files'):
                try:
                    os.makedirs('pgn_files')
                except OSError:
                    sys.stderr.write("\nException: error while creating folder!")
            for p2s_filename in os.listdir(w_dir):
                if p2s_filename.startswith('p2s') and p2s_filename.endswith('.pgn'):
                    source = os.path.join(w_dir, p2s_filename)
                    destination = os.path.join(root_dir, 'pgn_files', p2s_filename)
                    try:
                        shutil.move(source, destination)
                    except OSError:
                        sys.stderr.write("\nExeption: error while moving files!")
    elif err_level == 4:
        if messagebox.askyesno(err_head, err_msg, parent=tk_parent):
            create_copy = True
        else:
            create_copy = False
        return create_copy


def start_main():
    global twic_max
    action_flag = False
    OP_SYS = platform.system()
    uzip_list = []  # empty list to be filled with all extracted zip file names to check for doubles
    dt = datetime.datetime.now()
    # Create a unique filename for merged pgn files and for Scid backup
    # File name is a time stamp. Format: p2s_yy-mm-dd_hh-mm-ss.pgn
    out_filename = "p2s_" + dt.strftime('%y-%m-%d_%H-%M-%S') + ".pgn"
    zipped_db_filename = (os.path.basename(file_select_db.get())[:-4]) + '_' + dt.strftime('%y-%m-%d_%H-%M-%S') + ".zip"

    pre_status = check_preconditions(OP_SYS)
    if not pre_status:
        return None
    else:
        start_action_button['state'] = 'disabled'
        w_dir = path_select_frame.get()
        root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        existing_scid_db = file_select_db.get()
        existing_db = existing_scid_db[:-4]
        file_list = []
        empty_list = False

        def write_logfile(log_text):
            root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
            timestamp = str(datetime.datetime.now().replace(microsecond=0)) + "\n"
            p2s_logfile = os.path.join(root_dir, "pgn2scid_error.log")
            with open(p2s_logfile, 'a') as log_input:
                log_input.write(timestamp + log_text + "\n\n")

        def write_message(msg, colour):
            message_frame['state'] = 'normal'
            message_frame.tag_configure('black', foreground='black', justify='left')
            message_frame.tag_configure('green', foreground='green', justify='left')
            message_frame.insert(END, msg, colour)
            message_frame.see('end')
            message_frame.update()
            message_frame['state'] = 'disabled'
            return None

        def write_result(status, colour):
            message_frame['state'] = 'normal'
            message_frame.tag_configure('red', foreground='red', justify='left')
            message_frame.tag_configure('green', foreground='green', justify='left')
            message_frame.insert(END, "[", 'black')
            message_frame.insert(END, status, colour)
            message_frame.see("end")
            message_frame.insert(END, "]", 'black')
            message_frame.update()
            message_frame["state"] = 'disabled'
            return None

        ######################################################################
        # If option is set download files from TWIC server                   #
        ######################################################################

        if twic_dl.get():
            action_flag = True
            os.chdir(w_dir)
            error_flag = False
            write_message("\n\n### Downloading files from TWIC server ###", "black")
            write_message("\nRequesting and parsing information ... ", "black")
            req = urllib.request.Request('http://theweekinchess.com/twic')

            try:
                with urllib.request.urlopen(req, timeout=15) as url:
                    html_content = url.read().decode('utf-8')
            except urllib.error.HTTPError as http_error:
                error_flag = True
                write_result("FAILED", 'red')
                log_text = "NETWORK ERROR - Request information from TWIC server: " + str(http_error.code)
                write_logfile(log_text)
                error_header = "Network error"
                error_text = "An error occurred while trying to request information from TWIC server! The server" \
                             " responded: " + str(http_error.code) + " - " + str(http_error.reason)
                error_disp(1, error_header, error_text)
            except urllib.error.URLError as url_error:
                error_flag = True
                write_result("FAILED", 'red')
                log_text = "NETWORK ERROR - Request information from TWIC server: " + str(url_error.reason)
                write_logfile(log_text)
                error_header = "Network error"
                error_text = "An error occurred while trying to request information from TWIC server! Error message: " + str(
                    url_error.reason)
                error_disp(1, error_header, error_text)
            except timeout:
                error_flag = True
                write_result("FAILED", 'red')
                log_text = "NETWORK ERROR - Connect to TWIC server: connection timed out"
                write_logfile(log_text)
                error_header = "Network error"
                error_text = "A Timeout error occured while trying to connect to TWIC server. Please try again later."
                error_disp(1, error_header, error_text)

            if not error_flag:
                # A simple regex based HTML parser
                # Patterns below are for reference. They work, but they might be subject to change.
                # TWIC issue (n)                    /<td>(\d+)</td>/
                # TWIC date (dd/mm/yyyy)            /<td>(\d{2}/\d{2}/\d{4})</td>/
                # TWIC info (URL)                   /(http:\/\/www\.\w+\.com\/html\/twic\d+\.html).+read/
                # TWIC target (URL)(filename)       /(http:\/\/www\.\w+\.com.+)(twic\d+g\.zip)/

                twic_issue = re.compile(r'<td>(\d+)</td>')
                twic_date = re.compile(r'<td>(\d{2}/\d{2}/\d{4})</td>')
                twic_info = re.compile(r'(http:\/\/www\.\w+\.com\/html\/twic\d+\.html).+read', re.IGNORECASE)
                twic_target = re.compile(r'(http:\/\/www\.\w+\.com.+)(twic\d+g\.zip)', re.IGNORECASE)

                twic_issue_list = twic_issue.findall(html_content)
                twic_date_list = twic_date.findall(html_content)
                twic_info_list = twic_info.findall(html_content)
                twic_target_list = twic_target.findall(html_content)

                twic_record = []
                twic_set = []

                for i in range(len(twic_issue_list)):
                    if int(twic_issue_list[i]) > int(twic_max):
                        twic_set.append(twic_issue_list[i])
                        twic_set.append(twic_date_list[i])
                        twic_set.append(twic_info_list[i])
                        twic_set.append(twic_target_list[i])
                        twic_record.append(twic_set)
                        twic_set = []
                write_result("DONE", 'green')

                # Pass the 'twic_record' list to a function which creates the TWIC file select window and
                # which returns a list of indices representing the files to be downloaded
                if twic_record:
                    file_list = twic_file_select(twic_record, OP_SYS)
                    while file_list == 'empty':
                        error_disp(2, "No files selected", "You have to select at least one file!", twic_file_select_window)
                        twic_file_select_window.destroy()
                        file_list = twic_file_select(twic_record, OP_SYS)
                else:
                    empty_list = True
                    write_message("\nNo new TWIC files to download ... ", 'black')
                    write_result("SKIPPED", 'red')

                # Join appropriate list elements from 'twic_record' based on the indices in 'file_list'
                # to create a list of complete URLs targeting to the desired TWIC pgn files
                complete_url_list = []
                twic_number_list = []
                if file_list != 'dummy' and empty_list is False:
                    for dl_target in file_list:
                        dl_link = (twic_record[dl_target][3][0] + twic_record[dl_target][3][1])
                        twic_number = (twic_record[dl_target][0])
                        complete_url_list.append(dl_link)
                        twic_number_list.append(twic_number)
                elif file_list == 'dummy':
                    write_message("\nDownloading TWIC files ... ", 'black')
                    write_result("CANCELED", 'red')

                # Download files and determine the highest TWIC issue number
                if complete_url_list:
                    complete_url_list = complete_url_list[::-1]
                    twic_digit = re.compile(r'\d+')
                    for i, url in enumerate(complete_url_list):
                        _, _, _, _, filename = url.split('/')
                        write_message("\nDownloading file '" + filename + "' ... ", 'black')
                        try:
                            with urllib.request.urlopen(url, timeout=15) as in_file, open(os.path.join(w_dir, filename),
                                                                                          'wb') as out_file:
                                shutil.copyfileobj(in_file, out_file)
                            twic_dl_issue = twic_digit.search(filename)
                            twic_dl_x = int(twic_dl_issue.group())
                            if twic_dl_x > int(twic_max):
                                twic_max = twic_dl_x
                            write_result("DONE", 'green')
                        except urllib.error.HTTPError as http_error:
                            write_result("FAILED", 'red')
                            log_text = ("NETWORK ERROR - Downloading file " + filename + " from TWIC server: "
                                        + str(http_error.code) + " - " + str(http_error.reason))
                            write_logfile(log_text)
                            error_header = "Network error"
                            error_text = ("An error occurred while trying to download files from TWIC server! The server"
                                          " responded: " + str(http_error.code) + " - " + str(http_error.reason))
                            error_disp(1, error_header, error_text)
                            break
                        except urllib.error.URLError as url_error:
                            write_result("FAILED", 'red')
                            log_text = ("NETWORK ERROR - Downloading file '" + filename + "' from TWIC server: "
                                        + str(url_error.reason))
                            write_logfile(log_text)
                            error_header = "Network error"
                            error_text = "An error occurred while trying to download files from TWIC server! Error message: "\
                                         + str(url_error.reason)
                            error_disp(1, error_header, error_text)
                            break
                        except timeout:
                            write_result("FAILED", 'red')
                            log_text = ("NETWORK ERROR - Downloading file '" + filename + "' from TWIC server: connection timed out")
                            write_logfile(log_text)
                            error_header = "Network error"
                            error_text = "A Timeout error occured while trying to dowload files from TWIC server. Please try again later."
                            error_disp(1, error_header, error_text)
                            break

        #############################################################################
        # If option is set extract all zipped pgn files within the specified folder #
        #############################################################################
        if do_zip.get():
            action_flag = True
            os.chdir(w_dir)
            member_count = 0
            do_not_ask = False
            write_message("\n\n### Extracting PGN files from ZIP archives ###", 'black')
            while 1:
                zip_files = glob.glob('*.zip')
                if zip_files:
                    for zip_filename in zip_files:  # Iterate over all zip files
                        try:
                            with zipfile.ZipFile(zip_filename) as zip_members:
                                for member in zip_members.namelist():  # A single member within the zip file
                                    # Excludes folders and hidden MAC files from being unzipped
                                    filename = os.path.basename(member)
                                    sub_dir = os.path.dirname(member)
                                    if not filename or sub_dir == '__MACOSX':
                                        continue
                                    if member[-3:] == 'pgn' or member[-3:] == 'zip':
                                        write_message("\nExtracting '" + member + "' from archive '" + zip_filename + "' ... ",
                                                      "black")
                                        if member in uzip_list:  # Does the filename already exists?
                                            if not do_not_ask:
                                                custom_msg_header = "File already exists!"
                                                custom_msg_text = "Extracting pgn files: the file '" + member + "' already exists!\n" "How to proceed?"
                                                button1 = "Skip"
                                                button2 = "Overwrite"
                                                button3 = "Auto rename"
                                                dont_ask_flag = True
                                                choice, do_not_ask = custom_msg_box(custom_msg_header, custom_msg_text,
                                                                                    dont_ask_flag, button1, button2, button3)

                                            if choice == 1:
                                                # Skip / don't unzip the actual zip
                                                # member
                                                write_result("SKIPPED", 'red')
                                                continue
                                            elif choice == 2:
                                                # Overwrite an already existing file.
                                                with zip_members.open(member) as source:
                                                    with open(os.path.join(w_dir, member), 'wb') as target:
                                                        shutil.copyfileobj(source, target)
                                                member_count += 1
                                                uzip_list.append(member)
                                                write_result("DONE", 'green')
                                                continue
                                            elif choice == 3:
                                                tmp_dir = tempfile.gettempdir()
                                                # If there's no system temp folder,
                                                # create one within the working
                                                # directory ...
                                                if not (tmp_dir or os.path.isdir('tmp')):
                                                    try:
                                                        os.makedirs(os.path.join(w_dir, 'tmp'))
                                                    except OSError as os_error:
                                                        write_message("\nSTOPPED", 'black')
                                                        error_disp(1, "Unexpected error",
                                                                    "An unexpected error occured while\n"
                                                                    "trying to create a temp folder!\n\n"
                                                                    + str(os_error)
                                                                    + "\npgn2scid has been STOPPED!")
                                                        start_action_button['state'] = 'normal'
                                                        return
                                                    tmp_dir = os.path.join(w_dir, 'tmp')

                                                # ... and extract the zip member into this folder
                                                with zip_members.open(member) as source:
                                                    with open(os.path.join(tmp_dir, member), 'wb') as target:
                                                        shutil.copyfileobj(source, target)

                                                new_filename = auto_rename(member, w_dir)

                                                source = os.path.join(tmp_dir, member)
                                                destination = os.path.join(w_dir, new_filename)
                                                try:
                                                    shutil.copy(source, destination)
                                                    write_result("DONE", 'green')
                                                except OSError as os_error:
                                                    write_message("\nSTOPPED", 'black')
                                                    error_disp(1, "Unexpected error",
                                                                "An unexpected error occured while\n"
                                                                "trying to move uncompressed ZIP files\n"
                                                                "from tmp_dir to w_dir!\n\n"
                                                                + str(os_error)
                                                                + "\npgn2scid has been STOPPED!")
                                                    start_action_button['state'] = 'normal'
                                                    return

                                                member_count += 1
                                                uzip_list.append(new_filename)
                                                if os.path.isdir(os.path.join(w_dir, 'tmp')):
                                                    shutil.rmtree(tmp_dir, ignore_errors=True)
                                        else:
                                            with zip_members.open(member) as source:
                                                with open(os.path.join(w_dir, member), 'wb') as target:
                                                    shutil.copyfileobj(source, target)
                                            write_result("DONE", 'green')
                                            member_count += 1
                                            uzip_list.append(member)
                                    else:
                                        write_message(
                                            "\nThe file '" + member + "' from archive '" + zip_filename + "' seems not the be a pgn file ... ",
                                            'black')
                                        write_result("SKIPPED", 'red')
                        except BadZipFile as bad_zip_file:
                            write_message("\nDecompressing '" + zip_filename + "' ... ", 'black')
                            error_disp(1, "Unzip Error", "An error orcured while trying to decompress '" + zip_filename + "'!"
                                       + "\nError message: " + str(bad_zip_file))
                            write_result("SKIPPED", 'red')
                            continue
                    if member_count == 0:
                        write_message("\nNo valid PGN files found in ZIP archive '" + zip_filename + "'!\n", 'black')
                else:
                    write_message("\nNo ZIP files found to decompress ... ", 'black')
                    write_result("SKIPPED", 'red')

                    break

                ###############################################################
                # If option is set delete all zip files after decompressing   #
                ###############################################################
                if delete_zip.get():
                    write_message("\nDeleting ZIP files ... ", 'black')
                    try:
                        for zip_filename in zip_files:
                            os.remove(os.path.join(w_dir, zip_filename))
                        write_result("DONE", 'green')
                    except OSError as os_error:
                        write_result("FAILED", 'red')
                        write_message("\nSTOPPED", 'black')
                        error_disp(1, "Unexpected error",
                                    "An unexpected error occured while\n"
                                    "trying to delete ZIP files!\n"
                                    + str(os_error)
                                    + "\n\npgn2scid has been STOPPED!")
                        start_action_button['state'] = 'normal'
                        return

                ###############################################################
                # If no deletion is desired, move all zip files to folder     #
                # "zip_files" to keep the working directory clean.            #
                ###############################################################
                else:
                    move_index = 0
                    file_index = 0
                    if not os.path.isdir(os.path.join(root_dir, 'zip_files')):
                        write_message("\nCreating folder 'zip_files' ...", 'black')
                        try:
                            os.makedirs(os.path.join(root_dir, 'zip_files'))
                            write_result("DONE", 'green')
                        except OSError as os_error:
                            write_result("FAILED", 'red')
                            write_message("\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to create the folder 'zip_files'!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            return

                    zip_list = []
                    write_message("\nMoving ZIP files to folder 'zip_files' ... ", 'black')
                    zip_dir = os.path.join(root_dir, 'zip_files')
                    for zips in os.listdir(zip_dir):
                        zip_list.append(zips)

                    for filename in os.listdir(w_dir):
                        if filename.endswith('.zip'):
                            file_index += 1
                            if filename in zip_list:
                                new_filename = auto_rename(filename, zip_dir)
                            else:
                                new_filename = filename
                            source = os.path.join(w_dir, filename)
                            destination = os.path.join(root_dir, 'zip_files', new_filename)
                            try:
                                os.rename(source, destination)
                                move_index += 1
                            except OSError as os_error:
                                write_result("FAILED", 'red')
                                write_message("\nSTOPPED", 'black')
                                error_disp(1, "Unexpected error",
                                            "An unexpected error occured while\n"
                                            "trying to move ZIP files!\n"
                                            + str(os_error)
                                            + "\n\npgn2scid has been STOPPED!")
                                start_action_button['state'] = 'normal'
                                return

                    if move_index == file_index:
                        write_result("DONE", 'green')
                    else:
                        write_result("FAILED", 'red')



        ########################################
        # If option is set merge all pgn files #
        ########################################
        if do_merge.get():
            action_flag = True
            pgn_count = 0
            write_message("\n\n### Merging PGN files ###", 'black')
            for in_filename in os.listdir(w_dir):
                if in_filename.endswith('.pgn') and not in_filename.startswith('p2s'):
                    write_message("\nAdding '" + in_filename + "' to '" + out_filename + "' ... ", 'black')
                    try:
                        with open(out_filename, 'a', errors='ignore') as f_out, fileinput.input(
                                os.path.join(w_dir, in_filename),
                                openhook=fileinput.hook_encoded('latin-1')) as f_in:
                            for line in f_in:
                                f_out.write(line)
                            pgn_count += 1
                            write_result("DONE", 'green')
                    except OSError as os_error:
                        write_result("FAILED", 'red')
                        write_message("\n\nSTOPPED", 'black')
                        error_disp(1, "Unexpeted error",
                                    "An uncexpected error ocurred while\n"
                                    "trying to merge PGN files!\n"
                                    + str(os_error)
                                    + "\n\npgn2scid has been STOPPED!")
                        start_action_button['state'] = 'normal'
                        return

            if pgn_count == 0:
                write_message("\nNo PGN files found to merge ... ", 'black')
                write_result("SKIPPED", 'red')

            ###################################################################
            # If option is set delete all pgn files after merging             #
            ###################################################################
            if delete_pgn.get() and pgn_count > 0:
                write_message("\nDeleting PGN files ... ", 'black')
                for filename in os.listdir(w_dir):
                    if not filename.startswith("p2s") and filename.endswith('.pgn'):
                        try:
                            os.remove(os.path.join(w_dir, filename))
                        except OSError as os_error:
                            write_result("FAILED", 'red')
                            write_message("\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to delete PGN files!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            return
                write_result("DONE", 'green')

            ###################################################################
            # If no deletion is desired, move all pgn files to folder         #
            # "pgn_files" to keep the working directory clean.                #
            ###################################################################
            else:
                if pgn_count > 0:
                    move_index = 0
                    file_index = 0
                    if not os.path.isdir(os.path.join(root_dir, 'pgn_files')):
                        write_message("\nCreating folder 'pgn_files' ... ", 'black')
                        try:
                            os.makedirs(os.path.join(root_dir, 'pgn_files'))
                            write_result("DONE", 'green')
                        except OSError as os_error:
                            write_result("FAILED", 'red')
                            write_message("\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to create the folder 'pgn_files'!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            return

                    pgn_list = []
                    write_message("\nMoving PGN files to folder 'pgn_files' ... ", 'black')
                    pgn_dir = os.path.join(root_dir, 'pgn_files')
                    for pgns in os.listdir(pgn_dir):
                        pgn_list.append(pgns)

                    for filename in os.listdir(w_dir):
                        if filename.endswith('.pgn') and not filename.startswith('p2s'):
                            file_index += 1
                            if filename in pgn_list:
                                new_filename = auto_rename(filename, pgn_dir)
                            else:
                                new_filename = filename
                            source = os.path.join(w_dir, filename)
                            destination = os.path.join(root_dir, 'pgn_files', new_filename)
                            try:
                                os.rename(source, destination)
                                move_index += 1
                            except OSError as os_error:
                                write_message("\nSTOPPED", 'black')
                                error_disp(1, "Unexpected error",
                                            "An unexpected error occured while\n"
                                            "trying to move PGN files!\n"
                                            + str(os_error)
                                            + "\n\npgn2scid has been STOPPED!")
                                start_action_button['state'] = 'normal'
                                return
                    if move_index == file_index:
                        write_result("DONE", 'green')
                    else:
                        write_result("FAILED", 'red')

        ######################################################################
        # Invoking pgnscid to convert pgn files to native Scid format        #
        ######################################################################
        if do_scid.get():
            action_flag = True
            pgn_count = games_count = players_count = events_count = sites_count = 0

            write_message("\n\n### Converting PGN files to native Scid format ### ", 'black')
            for filename in os.listdir(w_dir):
                # Define some regex patterns to display a brief statistic based on the pgnscid output
                games_stat = re.compile(r'[^`\w+](\d+)\s(games)')
                players_stat = re.compile(r'[^`\w+](\d+)\s(players)')
                events_stat = re.compile(r'[^`\w+](\d+)\s(events)')
                sites_stat = re.compile(r'[^`\w+](\d+)\s(sites)')
                if filename.endswith(".pgn"):
                    pgn_count += 1
                    write_message("\nConverting " + filename + " ... ", "black")
                    try:
                        pgnscid_output = subprocess.check_output(["pgnscid", os.path.join(w_dir, filename)], shell=False,
                                                                 stderr=subprocess.STDOUT)
                        while not pgnscid_output:
                            time.sleep(0.5)
                        write_result("DONE", 'green')
                    except subprocess.CalledProcessError as process_error:
                        out_text = process_error.output.decode("utf-8")
                        error_header = "pgnscid: critical error"
                        error_text = out_text + "Exit code: " + str(process_error.returncode)
                        error_disp(1, error_header, error_text)
                        write_result("FAILED", 'red')
                        write_message("\n\nSTOPPED", 'black')
                        break
                    pgnscid_output = pgnscid_output.decode("utf-8")

                    # Check for an *.err file within the working directory in case
                    # of any errors or warnings
                    return_val, log_text = check_for_errors(w_dir, root_dir)
                    p2s_logfile = os.path.join(root_dir, "pgn2scid_error.log")
                    if return_val == 1:
                        log_text += filename + ": error(s) IGNORED by user!\n\n"
                        with open(p2s_logfile, 'a') as write_logfile:
                            write_logfile.write(log_text)

                    elif return_val == 2:
                        for scid_suffix in ['.si4', '.sg4', '.sn4']:
                            try:
                                os.remove(filename[:-4] + scid_suffix)
                            except OSError as os_error:
                                write_message("\nSTOPPED", 'black')
                                error_disp(1, "Unexpected error",
                                            "An unexpected error occured while\n"
                                            "trying to remove Scid files based\n"
                                            "on a faulty PGN file!\n"
                                            + str(os_error)
                                            + "\n\npgn2scid has been STOPPED!")
                                start_action_button['state'] = 'normal'
                                return
                        pgn_count -= 1
                        log_text += filename + (": file SUSPENDED by user!\nSuspended file moved to "
                                                + os.path.join(root_dir, "suspended_pgn_files") + "\n\n")
                        with open(p2s_logfile, 'a', errors='ignore') as logfile:
                            logfile.write(log_text)
                        write_message("\nFile " + filename + " has been ... ", 'black')
                        write_result("SUSPENDED", 'red')

                        # Move faulty file to 'suspended_pgn_files' in root_dir
                        susp_pgn_list = []
                        write_message("\nMoving suspended PGN file to folder 'suspended_pgn_files' ... ", 'black')
                        susp_pgn_dir = os.path.join(root_dir, 'suspended_pgn_files')
                        for susp_pgns in os.listdir(susp_pgn_dir):
                            susp_pgn_list.append(susp_pgns)
                        if filename in susp_pgn_list:
                            new_filename = auto_rename(filename, susp_pgn_dir)
                        else:
                            new_filename = filename
                        source = os.path.join(w_dir, filename)
                        destination = os.path.join(root_dir, 'suspended_pgn_files', new_filename)
                        try:
                            os.rename(source, destination)
                            write_result("DONE", 'green')
                        except OSError as os_error:
                            write_result("FAILED", 'red')
                            write_message("\n\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to move the suspended PGN file!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            return

                    if return_val == 0 or return_val == 1:
                        games_x = games_stat.search(pgnscid_output)
                        games_stat = int(games_x.group(1))
                        games_count += games_stat

                        players_x = players_stat.search(pgnscid_output)
                        players_stat = int(players_x.group(1))
                        players_count += players_stat

                        events_x = events_stat.search(pgnscid_output)
                        events_stat = int(events_x.group(1))
                        events_count += events_stat

                        sites_x = sites_stat.search(pgnscid_output)
                        sites_stat = int(sites_x.group(1))
                        sites_count += sites_stat

            if pgn_count:
                write_message("\nSummary after PGN to Scid conversion:", 'black')
                write_message("\nGames:    " + str(games_count), 'black')
                write_message("\nPlayers:    " + str(players_count), 'black')
                write_message("\nEvents:    " + str(events_count), 'black')
                write_message("\nSites:    " + str(sites_count), 'black')
            else:
                write_message("\nNo PGN files found to convert ... ", "black")
                write_result("SKIPPED", "red")

            ###################################################################
            # If option is set delete all pgn file                            #
            ###################################################################
            if delete_mpgn.get() and pgn_count > 0:
                write_message("\nDeleting remaining PGN files ...", "black")
                for filename in os.listdir(w_dir):
                    if filename.endswith('.pgn'):
                        try:
                            os.remove(os.path.join(w_dir, filename))
                        except OSError as os_error:
                            write_message("\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to delete remaining PGN files!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            write_result("FAILED", "red")
                            return
                write_result("DONE", "green")

            ###################################################################
            # If no deletion is desired, move remaining pgn file to folder    #
            # "pgn_files" to keep the working directory clean.                #
            ###################################################################
            elif pgn_count:
                move_index = 0
                file_index = 0
                if not os.path.isdir(os.path.join(root_dir, 'pgn_files')):
                    write_message("\nCreating folder 'pgn_files' ... ", "black")
                    try:
                        os.makedirs(os.path.join(root_dir, 'pgn_files'))
                    except OSError as os_error:
                        write_result("FAILED", 'red')
                        write_message("\nSTOPPED", 'black')
                        error_disp(1, "Unexpected error",
                                    "An unexpected error occured while\n"
                                    "trying to create the folder 'pgn_files'!\n"
                                    + str(os_error)
                                    + "\n\npgn2scid has been STOPPED!")
                        start_action_button['state'] = 'normal'
                        return

                pgn_list = []
                write_message("\nMoving remaining PGN files to folder 'pgn_files' ... ", 'black')
                pgn_dir = os.path.join(root_dir, 'pgn_files')
                try:
                    for pgns in os.listdir(pgn_dir):
                        pgn_list.append(pgns)

                    for filename in os.listdir(w_dir):
                        if filename.endswith('.pgn'):
                            file_index += 1
                            if filename in pgn_dir:
                                new_filename = auto_rename(filename, pgn_dir)
                            else:
                                new_filename = filename
                            source = os.path.join(w_dir, filename)
                            destination = os.path.join(root_dir, 'pgn_files', new_filename)
                            shutil.move(source, destination)
                            move_index += 1
                except OSError as os_error:
                    write_result("FAILED", 'red')
                    write_message("\n\nSTOPPED", 'black')
                    error_disp(1, "Unexpected error",
                                "An unexpected error occured while\n"
                                "trying to move remaining PGN files!\n"
                                + str(os_error)
                                + "\n\npgn2scid has been STOPPED!")
                    start_action_button['state'] = 'normal'
                    return
                if move_index == file_index:
                    write_result("DONE", 'green')
                else:
                    write_result("FAILED", 'red')

        ######################################################################
        # Invoke scmerge to merge scid file(s) with an existing database     #
        ######################################################################
        if do_scmerge.get():
            action_flag = True
            os.chdir(w_dir)
            write_message("\n\n### Merging Scid files with " + existing_db + " ###", 'black')
            si4_count = 0

            # Zip compress a copy of the existing database
            if zip_scid_db.get():
                create_zip = True
                os.chdir(w_dir)
                # os.chdir(os.path.dirname(existing_scid_db))
                write_message("\nCreating a ZIP compressed copy of the existing database ... ", 'black')
                si4_files = glob.glob('*.si4')
                if not si4_files:
                    create_zip = error_disp(4, "No Scid files to merge",
                                            "There are no Scid files to merge. Do you want"
                                            " to create a ZIP compressed copy of your"
                                            " existing Scid database anyway?")
                if create_zip:
                    try:
                        with zipfile.ZipFile(zipped_db_filename, 'a') as zipped_db:
                            for scid_suffix in ['.si4', '.sg4', '.sn4']:
                                zipped_db.write(os.path.join(existing_scid_db, existing_db + scid_suffix),
                                                os.path.basename(existing_db + scid_suffix))
                        write_result("DONE", 'green')
                    except OSError as os_error:
                        write_result("FAILED", 'red')
                        write_message("\n\nSTOPPED", 'black')
                        error_disp(1, "Unexpected error",
                                    "An unexpected error occured while\n"
                                    "trying to create a zipped copy!\n"
                                    "of the existing database!\n"
                                    + str(os_error)
                                    + "\n\npgn2scid has been STOPPED!")
                        start_action_button['state'] = 'normal'
                        return

                    if not os.path.isdir(os.path.join(root_dir, 'scid_db_copy')):
                        write_message("\nCreating folder 'scid_db_copy' ...", 'black')
                        try:
                            os.makedirs(os.path.join(root_dir, 'scid_db_copy'))
                            write_result("DONE", 'green')
                        except OSError as os_error:
                            write_message("\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to create the folder 'scid_db_copy"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                    write_message("\nMoving ZIP compressed database to folder 'scid_db_copy' ... ", 'black')
                    source = os.path.join(w_dir, zipped_db_filename)
                    destination = os.path.join(root_dir, 'scid_db_copy')
                    try:
                        shutil.move(source, destination)
                        write_result("DONE", 'green')
                    except OSError as os_error:
                        write_result("FAILED", 'red')
                        write_message("\n\nSTOPPED", 'black')
                        error_disp(1, "Unexpected Error",
                                    "Unexpected error while moving ZIP compressed"
                                    " Scid files. Please make you sure\n"
                                    " you have read / write access to "
                                    + destination + "\n"
                                    + str(os_error)
                                    + "\n\npgn2scid has been STOPPED")
                        start_action_button['state'] = 'normal'
                        return
                else:
                    write_result("SKIPPED", 'red')
            # Merge database files
            scmerge_out_list = []
            for filename in os.listdir(w_dir):
                if filename.endswith('.si4') and filename != os.path.basename(existing_scid_db):
                    write_message("\nMerging " + filename[:-4] + " ... ", 'black')
                    try:
                        scmerge_output = subprocess.check_output(["scmerge", "new_db", filename[:-4], existing_db],
                                                                 shell=False, stderr=subprocess.STDOUT)
                        write_result("DONE", 'green')
                    except subprocess.CalledProcessError as process_error:
                        out_text = process_error.output.decode('utf-8')
                        error_header = "smerge: critical error"
                        error_text = "scmerge: abnormal program termination!\n" + out_text + "Exit code:" + str(
                            process_error.returncode)
                        error_disp(1, error_header, error_text)
                        write_result("FAILED", 'red')
                        write_message("\n\nSTOPPED", 'black')
                        start_action_button['state'] = 'normal'
                        return
                    for scid_suffix in ['.si4', '.sg4', '.sn4']:
                        os.remove(existing_db + scid_suffix)
                        os.rename("new_db" + scid_suffix, existing_db + scid_suffix)
                    scmerge_output = scmerge_output.decode("utf-8")
                    scmerge_out_list = scmerge_output.split()
                    si4_count += 1
            if si4_count:
                write_message("\nTotal number of games in your database now: " + scmerge_out_list[5], 'black')
            else:
                write_message("\nNo Scid files found to merge ... ", 'black')
                write_result("SKIPPED", 'red')

            ###################################################################
            # If option is set delete remaining Scid files                    #
            ###################################################################
            if delete_scidfile.get() and si4_count > 0:
                write_message("\nDeleting remaining Scid files ... ", 'black')
                for filename in os.listdir(w_dir):
                    for scid_suffix in ['.si4', '.sg4', '.sn4']:
                        if filename.endswith(scid_suffix) and filename != os.path.basename(existing_scid_db):
                            try:
                                os.remove(os.path.join(w_dir, filename))
                            except OSError as os_error:
                                write_result("FAILED", "red")
                                write_message("\nSTOPPED", 'black')
                                error_disp(1, "Unexpected error",
                                            "An unexpected error occured while\n"
                                            "trying to delete remaining Scid files!\n"
                                            + str(os_error)
                                            + "\n\npgn2scid has been STOPPED!")
                                start_action_button['state'] = 'normal'
                                return
                write_result("DONE", 'green')

            ###################################################################
            # If no deletion is desired, move scid files to folder            #
            # "scid_files" to keep the working directory clean.               #
            ###################################################################
            else:
                if si4_count > 0:
                    move_index = 0
                    file_index = 0
                    if not os.path.isdir(os.path.join(root_dir, 'scid_files')):
                        write_message("\nCreating folder 'scid_files' ...", 'black')
                        try:
                            os.makedirs(os.path.join(root_dir, 'scid_files'))
                            write_result("DONE", 'green')
                        except OSError as os_error:
                            write_message("\n\nSTOPPED", 'black')
                            error_disp(1, "Unexpected error",
                                        "An unexpected error occured while\n"
                                        "trying to move remaining Scid files!\n"
                                        + str(os_error)
                                        + "\n\npgn2scid has been STOPPED!")
                            start_action_button['state'] = 'normal'
                            write_result("FAILED", "red")
                            return
                    scid_list = []
                    write_message("\nMoving remaining Scid files to folder 'scid_files' ...", "black")
                    scid_dir = os.path.join(root_dir, 'scid_files')
                    for si4s in os.listdir(scid_dir):
                        scid_list.append(si4s)

                    for filename in os.listdir(w_dir):
                        for scid_suffix in ['.si4', '.sg4', '.sn4']:
                            if filename.endswith(scid_suffix) and filename != os.path.basename(existing_scid_db):
                                file_index += 1
                                if filename in scid_list:
                                    new_filename = auto_rename(filename, scid_dir)
                                else:
                                    new_filename = filename
                                source = os.path.join(w_dir, filename)
                                destination = os.path.join(root_dir, "scid_files", new_filename)
                                try:
                                    os.rename(source, destination)
                                    move_index += 1
                                except OSError as os_error:
                                    write_result("FAILED", 'red')
                                    write_message("\n\nSTOPPED", 'black')
                                    error_disp(1, "Unexpeced error",
                                                "An unexpected error occured while\n"
                                                "trying to move remaining Scid files!"
                                                + str(os_error)
                                                + "\n\npgn2scid has been STOPPED!")
                                    start_action_button['state'] = 'normal'
                                    return
                    if move_index == file_index:
                        write_result("DONE", 'green')
                    else:
                        write_result("FAILED", 'red')

        if action_flag:
            write_message("\n\nFINISHED", 'black')
            start_action_button["state"] = 'normal'
            init_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'pgn2scid.ini')
            config = configparser.ConfigParser()
            try:
                # Write settings to pgn2scid.ini
                dir_name = path_select_frame.get()
                enable_twic_value = twic_dl.get()
                twic_max_value = twic_max
                extract_pgn_value = do_zip.get()
                delete_zip_value = delete_zip.get()
                merge_pgn_value = do_merge.get()
                delete_pgn_value = delete_pgn.get()
                convert_pgn_value = do_scid.get()
                delete_remaining_pgn_value = delete_mpgn.get()
                merge_scid_value = do_scmerge.get()
                write_zipped_scid_value = zip_scid_db.get()
                delete_scid_value = delete_scidfile.get()
                file_name = file_select_db.get()

                config['GENERAL'] = {'enable_twic_auto_dl': enable_twic_value, 'twic_max': twic_max_value,
                                     'extract_pgn_files': extract_pgn_value, 'delete_zip_files': delete_zip_value,
                                     'merge_pgn_files': merge_pgn_value, 'delete_pgn_files': delete_pgn_value,
                                     'convert_pgn_to_scid': convert_pgn_value,
                                     'delete_remaining_pgn': delete_remaining_pgn_value,
                                     'merge_scid_database': merge_scid_value,
                                     'write_zipped_scid_copy': write_zipped_scid_value,
                                     'delete_scid_files': delete_scid_value}
                config['PATHS'] = {'work_path': dir_name, 'database_dir': file_name}
                with open(init_file, 'w') as configfile:
                    config.write(configfile)
            except IOError:
                error_disp(1, "Error while writing config file",
                            "Unexpected I/O Error while trying"
                            " to write a pgn2scid.ini config file.")
        else:
            write_message("\n\nNothing to do", "black")
            start_action_button["state"] = "normal"
            return


def auto_rename(old_filename, dir):
    n_max = 0
    regex = re.compile(r'\((\d+)\)$')
    # Split filename and file suffix for later recomposing
    filename, file_suffix = os.path.splitext(old_filename)
    for files in os.listdir(dir):
        if files.startswith(filename):
            # Search for the pattern '(n)' at the end of filebase
            filebase = os.path.splitext(files)[0]
            pattern = regex.search(filebase)
            if pattern:
                # Determine the highest value for 'n' in filebase(n)
                n = int(pattern.group(1))
                if n > n_max:
                    n_max = n
    if n_max == 0:
        # Add '(1)' to the filename, and add the suffix
        new_filename = filename + '(1)' + file_suffix
    else:
        n_max += 1
        new_filename = filename + '(' + str(n_max) + ')' + file_suffix
    return new_filename


def twic_file_select(twic_record, OP_SYS):
    file_list = []
    global twic_file_select_window

    def download(twic_pointer):
        nonlocal file_list
        for pt, var in zip(twic_pointer, vars):
            value = var.get()
            if value:
                file_list.append(pt)
        if file_list:
            twic_file_select_window.destroy()
        else:
            file_list = "empty"

    def cancel():
        nonlocal file_list
        file_list = "dummy"
        twic_file_select_window.destroy()

    x = main_frame.winfo_rootx()
    y = main_frame.winfo_rooty()
    twic_file_select_window = Toplevel()
    twic_file_select_window.wm_title("Select TWIC files")
    twic_file_select_window.geometry("+%d+%d" % (x + 70, y + 100))
    twic_file_select_window.resizable(0, 0)
    system_bg_colour = main_frame.cget('bg')

    # Some MS Windows specific adjustments to make this window look the same
    # as on Linux systems
    if OP_SYS == "Windows":
        w1 = 3
        w2 = 18
        f1 = 12
        f2 = 22
        f3 = 15
        f5 = 10
    else:
        w1 = 4
        w2 = 25
        f1 = 12
        f2 = 18
        f3 = 13
        f5 = 19

    twic_file_select_blank = Label(twic_file_select_window, background=system_bg_colour, relief='groove', width=w1,
                                   height=1, font=("arial", 10))
    twic_file_select_blank.grid(column=0, row=0, padx=(5, 0), pady=(15, 0))
    twic_file_select_twic = Label(twic_file_select_window, text="TWIC", background=system_bg_colour, relief='groove',
                                  width=8, height=1, anchor="w", font=("arial", 10))
    twic_file_select_twic.grid(column=1, row=0, pady=(15, 0))
    twic_file_select_date = Label(twic_file_select_window, text="Date", background=system_bg_colour, relief='groove',
                                  width=13, height=1, anchor="w", font=("arial", 10))
    twic_file_select_date.grid(column=2, row=0, pady=(15, 0))
    twic_file_select_info = Label(twic_file_select_window, text="Info", background=system_bg_colour, relief='groove',
                                  width=10, height=1, anchor="w", font=("arial", 10))
    twic_file_select_info.grid(column=3, row=0, pady=(15, 0))
    twic_file_select_file = Label(twic_file_select_window, text="File", background=system_bg_colour, relief='groove',
                                  width=w2, height=1, anchor="w", font=("arial", 10))
    twic_file_select_file.grid(column=4, row=0, pady=(15, 0))
    twic_file_select_frame = ScrolledText(twic_file_select_window, background="white", width=60, height=10,
                                          font=("arial", 10))
    twic_file_select_frame.tag_configure("left", justify="left")
    twic_file_select_frame.grid(column=0, columnspan=5, row=1, padx=5, pady=(0, 5))

    sub_frame1 = Frame(twic_file_select_window)
    sub_frame1.grid(column=0, row=2, columnspan=5, sticky='nesw')
    sub_frame2 = Frame(twic_file_select_window)
    sub_frame2.columnconfigure(0, weight=1)
    sub_frame2.columnconfigure(1, weight=1)
    sub_frame2.grid(column=0, row=3, columnspan=5, sticky='nesw')

    def click(event):
        w = event.widget
        x, y = event.x, event.y
        tags = w.tag_names("@%d,%d" % (x, y))
        # Generate URL from index
        url = (twic_record[int(tags[2])][2])
        try:
            webbrowser.open_new(url)
        except webbrowser.Error:
            error_disp(2, "Webbrowser error", "An error occured while trying to open the default\nwebbrowser. Please"
                                              "ensure that a default webbrowser is configured in your system settings.")
        return

    def show_hand_cursor(event):
        event.widget.configure(cursor="hand1")

    def show_arrow_cursor(event):
        event.widget.configure(cursor="left_ptr")

    twic_pointer = []
    vars = []
    twic_file_select_frame.tag_config("even_colour", background="white")
    twic_file_select_frame.tag_config("odd_colour", background="light blue")
    # configure URL tag
    twic_file_select_frame.tag_config("href", foreground="blue", underline=1)
    twic_file_select_frame.tag_bind("href", "<Enter>", show_hand_cursor)
    twic_file_select_frame.tag_bind("href", "<Leave>", show_arrow_cursor)
    twic_file_select_frame.tag_bind("href", "<Button-1>", click)
    twic_file_select_frame.config(cursor="arrow")
    tag = "even_colour"

    # Create a table to be displayed in the TWIC file select frame
    twic_file_select_frame["state"] = "normal"
    for i in range(len(twic_record)):
        var = IntVar(value=0)
        if tag == "even_colour":
            bg_colour = "white"
        else:
            bg_colour = "light blue"

        cb = Checkbutton(twic_file_select_frame, background=bg_colour, variable=var, onvalue=1, offvalue=0)
        twic_file_select_frame.window_create("end", window=cb)
        if int(twic_max) != 0:
            var.set(1)
        twic_file_select_frame.insert(END, '{}{:{f1}}'.format(" ", twic_record[i][0], f1=f1), tag)
        twic_file_select_frame.insert(END, '{}{:{f2}}'.format(" ", twic_record[i][1], f2=f2), tag)
        twic_file_select_frame.insert(END, "link", ("href", tag, i))
        twic_file_select_frame.insert(END, '{:{f3}}'.format(" ", f3=f3), tag)
        twic_file_select_frame.insert(END, '{}{:13}'.format(" ", twic_record[i][3][1]), tag)
        twic_file_select_frame.insert(END, '{:{f5}}'.format(" ", f5=f5), tag)

        twic_pointer.append(i)
        vars.append(var)

        if tag == "odd_colour":
            tag = "even_colour"
        else:
            tag = "odd_colour"

        twic_file_select_frame.insert(END, "\n")
    twic_file_select_frame['state'] = 'disabled'

    separator1 = LabelFrame(sub_frame1, bg="#101010", relief="ridge", height=1, width=440)
    separator1.grid(column=0, row=0, columnspan=5)

    def click(event):
        try:
            webbrowser.open_new('http://theweekinchess.com/')
        except webbrowser.Error:
            error_disp(2, "Webbrowser error", "An error occured while trying to open the default\nwebbrowser. Please"
                                              "ensure that a default webbrowser is configured in your system settings.")

    def show_hand_cursor(event):
        event.widget.configure(cursor="hand1")

    def show_arrow_cursor(event):
        event.widget.configure(cursor="")

    note = Text(sub_frame1, background="light grey", wrap=WORD, relief=FLAT, width=62, height=5,
                font=("arial", 10, "italic"))
    note.tag_config('bold', font=('arial', 10, 'italic', 'bold'))
    note.tag_config('hyperlink', foreground='blue', underline=1, )
    note.tag_bind('hyperlink', '<Enter>', show_hand_cursor)
    note.tag_bind('hypelrink', '<Leave>', show_arrow_cursor)
    note.tag_bind('hyperlink', '<Button-1>', click)
    note['state'] = 'normal'
    note.insert(END, "Please note: ", 'bold')
    note.insert(END, "TWIC downloads is a service provided by 'The Week in Chess', founded by Mark Crowther. It's "
                     "completely free of charge for personal use. If you download files regularly you should consider to "
                     "donate in order to keep this service living. For more information please visit ")
    note.insert(END, "http://theweekinchess.com", 'hyperlink')
    note['state'] = 'disabled'
    note.grid(column=0, row=1, padx=5, pady=(5, 5))

    separator2 = LabelFrame(sub_frame2, bg="#101010", relief="ridge", height=1, width=440)
    separator2.grid(column=0, row=0, columnspan=5)

    download_button = Button(sub_frame2, text="DOWNLOAD", font=("", 11), width=1,
                             command=lambda: download(twic_pointer))
    download_button.grid(column=0, row=1, pady=(5, 0), sticky="nesw")
    cancel_button = Button(sub_frame2, text="Cancel", font=("", 11), width=1, command=cancel)
    cancel_button.grid(column=1, row=1, pady=(5, 0), sticky="nesw")

    while not file_list:
        twic_file_select_window.update()
        time.sleep(0.1)  # To reduce CPU load

    return file_list


def check_for_errors(w_dir, root_dir):
    value = 0
    log_content = ""
    for err_file in os.listdir(w_dir):
        if err_file.endswith(".err"):
            timestamp = datetime.datetime.now().replace(microsecond=0)

            def ignore():
                nonlocal value
                value = 1
                error_log_window.destroy()

            def suspend():
                nonlocal value
                value = 2
                error_log_window.destroy()

            path_to_logfile = os.path.join(w_dir, err_file)
            try:
                with open(path_to_logfile, encoding='ascii', errors='surrogateescape') as pgnscid_error_log:
                    pgnscid_error_text = pgnscid_error_log.read()
            except IOError as io_error:
                write_message("\n\nSTOPPED", 'black')
                error_disp(2, "Unexpected error",
                            "An unexpected error occured while\n"
                            "trying to read the pgnscid error log file!\n"
                            + str(io_error),
                            + "\n\npgn2scid has been STOPPED!")
                start_action_button['state'] = 'normal'
                return

            error_log_text = ("Data conversion from PGN to native Scid format is finished, but"
                              " pgnscid reported errors or warnings.\nFor details see the error log"
                              " above.\n\nHow to proceed?")
            x = main_frame.winfo_rootx()
            y = main_frame.winfo_rooty()
            error_log_window = Toplevel()
            system_bg_colour = error_log_window.cget('bg')
            error_log_window.wm_title("pgnscid error log")
            error_log_window.geometry("+%d+%d" % (x - 80, y + 50))
            error_text_frame = ScrolledText(error_log_window, background=system_bg_colour, wrap=WORD, width=90,
                                            height=10, font=('courier', 10))
            error_text_frame.tag_configure('left', justify='left')
            error_text_frame.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
            error_text_frame['state'] = 'normal'
            error_text_frame.insert(END, timestamp)
            error_text_frame.insert(END, "\n")
            error_text_frame.insert(END, pgnscid_error_text + "\n")
            error_text_frame['state'] = 'disabled'
            log_msg_subframe = Frame(error_log_window)
            log_msg_subframe.columnconfigure(0, weight=0)
            log_msg_subframe.columnconfigure(1, weight=1)
            log_msg_subframe.grid(column=0, row=1, columnspan=2, sticky='news')
            icon = Label(log_msg_subframe, image=warning_icon)
            icon.image = warning_icon
            icon.grid(column=0, row=0, padx=(6, 0), pady=(5, 0), sticky='nw')
            err_text = Label(log_msg_subframe, text=error_log_text, justify='left', font=("", 10))
            err_text.grid(column=1, row=0, padx=(6, 0), sticky='w')
            error_log_subframe = Frame(error_log_window)
            error_log_subframe.columnconfigure(0, weight=1)
            error_log_subframe.columnconfigure(1, weight=1)
            error_log_subframe.grid(column=0, row=2, columnspan=2, sticky="nesw")
            ignore_button = Button(error_log_subframe, text="Ignore errors", font=("", 11), command=ignore)
            ignore_button.rowconfigure(0, weight=1)
            ignore_button.grid(column=0, row=0, pady=(5, 0), sticky="nesw")
            skip_file_button = Button(error_log_subframe, text="Suspend file", font=("", 11), command=suspend)
            skip_file_button.rowconfigure(1, weight=1)
            skip_file_button.grid(column=1, row=0, pady=(5, 0), sticky="nesw")
            error_log_window.resizable(0, 0)

            log_content = error_text_frame.get("1.0", "end-2c")
            # Remove original pgnscid error logfile
            os.remove(path_to_logfile)
            # Create master logfile if not already existent
            p2s_logfile = os.path.join(root_dir, "pgn2scid_error.log")
            if not os.path.isfile(p2s_logfile):
                open(p2s_logfile, 'a').close()
            # Create a folder for suspended pgn files if not already existent
            if not os.path.isdir(os.path.join(root_dir, 'suspended_pgn_files')):
                os.mkdir(os.path.join(root_dir, 'suspended_pgn_files'))

            while value == 0:
                error_log_window.update()
                time.sleep(0.1)

    return value, log_content


def custom_msg_box(header, error_text, flag, button1, button2, button3):
    selection = 0
    do_not_ask = False

    def option1():
        nonlocal selection
        selection = 1

    def option2():
        nonlocal selection
        selection = 2

    def option3():
        nonlocal selection
        selection = 3

    # Display a message box centered relative to root window
    x = main_frame.winfo_rootx()
    y = main_frame.winfo_rooty()
    root_width = main_frame.winfo_width()
    root_height = main_frame.winfo_height()
    x_pos = x + (root_width // 2) - (root_width // 2)
    y_pos = y + (root_height // 2) - (root_height // 2)
    err_msg = Toplevel(main_frame)
    err_msg.resizable(0, 0)
    err_msg.wm_title(header)
    err_msg.geometry("+%d+%d" % (x_pos, y_pos))

    # Convert base64 data to gif image and display custom message box
    icon = Label(err_msg, image=warning_icon)
    icon.image = warning_icon
    icon.grid(column=0, row=0, padx=6, pady=(10, 0), sticky=N)
    err_text = Label(err_msg, text=error_text, justify="left")
    err_text.grid(column=1, row=0, pady=10)

    if flag:
        do_not_ask = IntVar()
        ask_ckb = Checkbutton(err_msg, text=" Don't ask me again", variable=do_not_ask)
        ask_ckb.grid(column=0, row=1, pady=(0, 0), sticky="W", columnspan=2)

    button_frame = Frame(err_msg)
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.columnconfigure(2, weight=1)
    button_frame.grid(column=0, row=2, sticky="nesw", columnspan=2)
    skip_button = Button(button_frame, text=button1, width=11, command=option1)
    skip_button.grid(column=0, row=0, sticky="ew")
    overwrite_button = Button(button_frame, text=button2, width=11, command=option2)
    overwrite_button.grid(column=1, row=0, sticky="ew")
    rename_button = Button(button_frame, text=button3, width=11, command=option3)
    rename_button.grid(column=2, row=0, sticky="ew")

    while selection == 0:
        err_msg.update()
        time.sleep(0.1)

    if flag:
        err_msg.destroy()
        return selection, do_not_ask.get()
    else:
        err_msg.destroy()
        return selection


def check_preconditions(OP_SYS):
    # This is not strictly necessary, but I prefer to do some checks
    # before performing any action to pgn or scid files

    # Does the specified working path exist?
    w_dir = path_select_frame.get()

    if not os.path.isdir(w_dir):
        error_header = "Invalid path"
        error_text = "Working path doesn't exist. Please specify a valid path."
        error_disp(1, error_header, error_text)
        return False

    # Are there any pgn files generated by pgn2scid left within the working
    # directory?
    try:
        os.chdir(w_dir)
    except OSError as os_error:
        message_frame['state'] = 'normal'
        message_frame.insert(END, "\nSTOPPED")
        message_frame['state'] = 'disabled'
        error_disp(1, "Unexpected error", "An unexpected error occured while\n "
                                          "trying to check preconditions\n"
                                          "bevore running pgn2scid!\n "
                                          "pgn2scid has been STOPPED!\n\n" + str(os_error))
        start_action_button['state'] = 'normal'
        return
    if glob.glob("p2s*.pgn"):
        error_header = "Already merged pgn files found!"
        error_text = ("There is at least one older and already merged pgn file in your working directory."
                    " In order to keep the working directory clean this or these file(s) should be moved to the folder "
                    "'pgn_files', located in the applications root directory. Otherwise pgn2scid may process them again and you "
                    "may end up with doubled or unwanted games in your database.\n\n"
                    "Move old p2s*.pgn files to folder 'pgn_files'?")
        error_disp(3, error_header, error_text)

    # Does the (path to the) given Scid database file exist?
    if do_scmerge.get() and not os.path.isfile(file_select_db.get()):
        error_header = "No database selected"
        error_text = "No valid Scid database selected. " \
                     "Please specify a valid path " \
                     "and file."
        error_disp(1, error_header, error_text)
        return False

    # Check for pgnscid if data conversion from pgn to native Scid database
    # format is desired
    if do_scid.get():
        if OP_SYS == "Windows":
            app_name = "\pgnscid.exe"
        else:
            app_name = "/pgnscid"

        pgnscid_located = False
        search_path = os.get_exec_path()

        for path in search_path:
            if os.path.isfile(path + app_name):
                pgnscid_located = True
                break

        if not pgnscid_located:
            error_header = "pgnscid not found"
            error_text = "Unable to locate 'pgnscid'! Either 'pgnscid' " \
                         "is not installed properly or not in $PATH."
            error_disp(1, error_header, error_text)
            return False

    # Check for scmerge if scid file merging is desired
    if do_scmerge.get():
        if OP_SYS == "Windows":
            app_name = "\scmerge.exe"
        else:
            app_name = "/scmerge"

        scmerge_located = False
        search_path = os.get_exec_path()

        for path in search_path:
            if os.path.isfile(path + app_name):
                scmerge_located = True
                break

        if not scmerge_located:
            error_header = "scmerge not found"
            error_text = "Unable to locate 'scmerge'! Either 'scmerge' " \
                         "is not installed properly or not in $PATH."
            error_disp(1, error_header, error_text)
            return False

    # All preconditions met
    return True


def main_exit():
    main_frame.destroy()


def select_path():
    dir_name = filedialog.askdirectory()
    path_select_frame.delete(0, END)
    path_select_frame.insert(0, dir_name)
    return None


def select_file():
    file_name = filedialog.askopenfilename(filetypes=[("Scid database files", "*.si4")])
    file_select_db.delete(0, END)
    file_select_db.insert(0, file_name)
    return None


def enable_decompress_options():
    if do_zip.get():
        delete_zip_checkbutton["state"] = "normal"
    else:
        delete_zip_checkbutton["state"] = "disabled"
    return None


def enable_merge_options():
    if do_merge.get() and do_scid.get():
        delete_pgn_checkbutton["state"] = "normal"
    elif do_merge.get():
        delete_pgn_checkbutton["state"] = "normal"
    else:
        delete_pgn_checkbutton["state"] = "disabled"
    return None


def enable_pgnscid_options():
    if do_scid.get():
        delete_mpgn_checkbutton["state"] = "normal"
    else:
        delete_mpgn_checkbutton["state"] = "disabled"
    return None


def enable_scmerge_options():
    if do_scmerge.get():
        delete_scidfile_checkbutton["state"] = "normal"
        label_set_dbpath["state"] = "normal"
        file_select_db["state"] = "normal"
        file_select_button["state"] = "normal"
        zip_scid_db_checkbutton["state"] = "normal"
    else:
        delete_scidfile_checkbutton["state"] = "disabled"
        label_set_dbpath["state"] = "disabled"
        file_select_db["state"] = "disabled"
        file_select_button["state"] = "disabled"
        zip_scid_db_checkbutton["state"] = "disabled"
    return None


def sep_line1(row_nr):
    separator = LabelFrame(main_frame, bg="#101010", relief="ridge", height=1, width=580)
    separator.grid(column=0, row=row_nr, columnspan=4)
    return None


main_frame = Tk()
main_frame.wm_title("pgn2scid")

# Base64 encoded inline images to avoid additional files
warning_icon_b64 = '''\
R0lGODlhIAAgAMZ4ALsAALwAAL4AAL8AAMAAAMEAAMIAAMMAAMQAAMUAAMYAAMcAAMkAAMoAAM
sAAMwAAM0AAM4AAM8AANAAANEAANIAANMAANQAANUAANYAANcAANgAANkAANoAANsAANwAAN0A
AN4AAN8AAOAAAOEAAOIAAOMAAOQAAOUAAOYAAOcAAOgAAOkAAOoAAOsAAOwAAO0AAO4AAO8AAP
AAAPEAAPIAAPMAAPQAAPUAAPYAAPcAAPgAAPkAAPoAAPsAAPwAAP0AAO8EBP4AAP8AAPgFBewL
C/EMDP8XF/4aGvQyMvo1NeZCQupERO9FRfNUVPZYWPhtbf1wcPR5efZ8fPunp/moqP+pqfurq/
+qqv6trdm3t/+trdq3t9u3t9y3t923t963t9+3t+C3t+G3t+K3t/3MzNvW1t3W1v/Pz9zc3PrW
1vrX1/vY2Pvh4fzh4fzi4v/s7P/t7f/u7v/v7/7y8v7z8/709P/09P////////////////////
///////////yH5BAEKAH8ALAAAAAAgACAAAAf+gEOCg4SFhoRCPz48Ozk4h5CRQkCLOjk3NJGa
iJQ8jjY0M4NppKWmp6inNDIyo2dksLGys7BjtmNiZ2kzMTCjZJuIPz08Ojg2YmkxLi2/wYKJxM
agYWnMLM6HR1hwcVtIip43oDLVLSsp2YZYeO14WT2N46sw1ejpgmnAh3HueHGNjtF7ASYNihMm
1BWa40/Op1XLWBQ8UYKEQkJo/JU5NkMGDBcsVBQsMWLExUFW/FGp0fEjC3Rf0pAQEeLkECFR/E
GhBxLdiZghPnw4SUmJvyQema1AYaJEzA8ePFyk1IPInXZ0gsBoEZIpSS9pPHDYoJBqoyvtqrwA
qeIgyRD+YDloyKAOyLAdOG48aeeErdsRIUCAzYDhQja7xfLWMGKnTpGQKSjS/NChSxoMFir8ml
TpEksZU6R0NTEzaIcNli1Q0JyPTCdLNz5vXdGWNGDKci1TkCDh1yJ5LGO8OFebxO0Oci9wSSMB
AoRRYxjlAMVreBM2bJi8pbwhwwULyyE4eCAISJox04KvZfGmnRsRIDyc9q56+YMGDaKdP6aebX
s8bYDAHWGqSbAcAwssEE4aYsTGy2yRMbGGGksMiBkFEUCgRRoLKKBAJQzW4NFw6DBVGncaXFDB
BBk6sKECCCBQTA4MyiDcOSmYOJlc3q3YnAMMbIiAAQZ8ksYZYYRTAcaSYHzhpBdQdiElF1Ryoc
WVZqRRAAEECJTKl2CSQoAAA1An3EuRVQSffN19h+F9CCZwgAFjBiBADTQsgyNFMwkoVooFQvAA
ggrIWcAAAgAQQCAAOw==
'''
warning_icon = PhotoImage(data=warning_icon_b64)

open_database_icon_b64 = '''\
R0lGODlhFAAUAIABAAAAAP///yH5BAEKAAEALAAAAAAUABQAAAIjhI+pwerIwptt2osziLz7qiVRaIwkSKbq8bXdWkqpGaLwjRUAOw==
'''
open_database_icon = PhotoImage(data=open_database_icon_b64)

open_folder_icon_b64 = '''\
R0lGODlhFAASAIABAAAAAP///yH5BAEKAAEALAAAAAAUABIAAAIajI8Gy5vf4kOx2ouznJzqD4biSJbmiaZqWQAAOw==
'''
open_folder_icon = PhotoImage(data=open_folder_icon_b64)

# Center root window relative to screen size
main_frame.withdraw()
main_frame.update_idletasks()
x = main_frame.winfo_screenwidth() // 2 - 300
y = main_frame.winfo_screenheight() // 2 - 280
main_frame.geometry("+%d+%d" % (x, y))
main_frame.resizable(0, 0)
main_frame.deiconify()

# Message frame for program output and status messages
message_frame = ScrolledText(main_frame, background="white", wrap=WORD, width=80, height=8, font=("arial", 10))
message_frame.tag_configure("left", justify="left")
message_frame.tag_configure("center", justify="center")
message_frame.grid(column=0, row=0, columnspan=4, padx=5, pady=5)
message_frame["state"] = "normal"

message_frame.insert(END, "pgn2scid v1.2\n", "center")
message_frame.insert(END, "Copyright (c) 2017, 2018 by Andreas Kreisig\n", "center")
message_frame.insert(END, "Released under the terms of the MIT license \n", "center")
message_frame.insert(END, "This program comes with absolutely NO WARRANTY!\n", "center")
message_frame.insert(END, "pgnscid, scmerge copyright (c) by Shane Hudson\n", "center")
message_frame["state"] = "disabled"

# Separator line
sep_line1(1)

# Label for working path selection
label_set_wpath = Label(main_frame, text="Set working path:", font=("arial", 10))
label_set_wpath.grid(column=0, row=2, padx=5, pady=(5, 0), sticky=W)

# Path selection frame
path_select_frame = Entry(main_frame, background="white", width=54, font=("arial", 10))
path_select_frame.grid(column=1, row=2, columnspan=2, pady=(5, 0), sticky=W)

# Path select button frame
path_select_button = Button(main_frame, image=open_folder_icon, width=40, height=24, command=select_path)
path_select_button.grid(column=3, row=2, pady=(5, 0))

# Enable TWIC auto downloader

twic_dl = IntVar()
twic_dl_checkbutton = Checkbutton(main_frame, text=" Enable the TWIC auto downloader", variable=twic_dl,
                                  font=("arial", 10))
twic_dl_checkbutton.grid(column=0, row=3, columnspan=4, pady=(5, 15), sticky=NW)

# Decompress zip files and enable deleting them afterwards
do_zip = IntVar()
process_zip_checkbutton = Checkbutton(main_frame, text=" Extract PGN files from zip"
                                                       " archives", variable=do_zip, font=("arial", 10),
                                      command=enable_decompress_options)
process_zip_checkbutton.grid(column=0, row=4, columnspan=4, pady=(15, 0), sticky=W)

# Delete zip files after decompressing
delete_zip = IntVar()
delete_zip_checkbutton = Checkbutton(main_frame, text=" Delete ZIP files after decompressing", font=("arial", 10),
                                     variable=delete_zip)
delete_zip_checkbutton.grid(column=0, row=5, columnspan=4, padx=20, sticky=W)
delete_zip_checkbutton["state"] = "disabled"

# Merge all pgn files to one monolithic file
do_merge = IntVar()
merge_pgn_checkbutton = Checkbutton(main_frame, text=" Merge all PGN files to"
                                                     " one monolithic file", font=("arial", 10), variable=do_merge,
                                    command=enable_merge_options)
merge_pgn_checkbutton.grid(column=0, row=6, columnspan=4, pady=(15, 0), sticky=W)

# Delete all pgn files except the merged one!
delete_pgn = IntVar()
delete_pgn_checkbutton = Checkbutton(main_frame, text=" Delete single PGN"
                                                      " files after merging", font=("arial", 10), variable=delete_pgn)
delete_pgn_checkbutton.grid(column=0, row=7, columnspan=4, padx=20, sticky=(W, N))
delete_pgn_checkbutton["state"] = "disabled"

# Checkbox for converting pgn file(s) to native scid format
do_scid = IntVar()
convert_checkbutton = Checkbutton(main_frame, text=" Invoke 'pgnscid' to convert PGN files to"
                                                   " native Scid format", font=("arial", 10), variable=do_scid,
                                  command=enable_pgnscid_options)
convert_checkbutton.grid(column=0, row=8, columnspan=4, pady=(15, 0), sticky=W)

# Delete merged pgn file
delete_mpgn = IntVar()
delete_mpgn_checkbutton = Checkbutton(main_frame, text=" Delete remaining PGN files after data conversion",
                                      font=("arial", 10), variable=delete_mpgn)
delete_mpgn_checkbutton.grid(column=0, row=9, columnspan=4, padx=20, sticky=W)
delete_mpgn_checkbutton["state"] = "disabled"

# Checkbox to invoke scmerge
do_scmerge = IntVar()
do_scmerge_checkbutton = Checkbutton(main_frame, text=" Invoke 'scmerge' to merge Scid files"
                                                      " with an existing database", font=("arial", 10),
                                     variable=do_scmerge, command=enable_scmerge_options)
do_scmerge_checkbutton.grid(column=0, row=10, columnspan=4, pady=(15, 0), sticky=W)

# Checkbox to zip compress an existing Scid database
zip_scid_db = IntVar()
zip_scid_db_checkbutton = Checkbutton(main_frame, text=" Create a ZIP compressed copy of the existing database before"
                                                        " merging", font=("arial", 10), variable=zip_scid_db)
zip_scid_db_checkbutton.grid(column=0, row=11, columnspan=4, padx=20, sticky=W)
zip_scid_db_checkbutton["state"] = "disabled"

# Checkbox to delete unwanted Scid files after merging
delete_scidfile = IntVar()
delete_scidfile_checkbutton = Checkbutton(main_frame, text=" Delete remaining Scid files after merging",
                                          font=("arial", 10), variable=delete_scidfile)
delete_scidfile_checkbutton["state"] = "disabled"
delete_scidfile_checkbutton.grid(column=0, row=12, columnspan=4, padx=20, sticky=W)

label_set_dbpath = Label(main_frame, text=" Select database:", font=("arial", 10))
label_set_dbpath["state"] = "disabled"
label_set_dbpath.grid(column=0, row=13, pady=(0, 5), padx=20, sticky=W)

# file selection frame for existing db
file_select_db = Entry(main_frame, background="white", width=54, font=("arial", 10))
file_select_db["state"] = "disabled"
file_select_db.grid(column=1, row=13, columnspan=2, pady=(0, 5), sticky=W)

# File select button for existing db
file_select_button = Button(main_frame, image=open_database_icon, width=40, height=24, command=select_file)
file_select_button["state"] = "disabled"
file_select_button.grid(column=3, row=13, pady=(0, 5), padx=10, sticky=E)

sep_line1(14)

main_subframe = Frame(main_frame)
main_subframe.grid(column=0, row=15, pady=(5, 0), columnspan=5, sticky='nesw')
main_subframe.columnconfigure(0, weight=1)
main_subframe.columnconfigure(1, weight=1)

# Start action button
start_action_button = Button(main_subframe, text="START", font=("", 15), command=start_main)
start_action_button.grid(column=0, row=0, sticky='nesw')

# End program button
exit_button = Button(main_subframe, text="Exit", font=("", 15), command=main_exit)
exit_button.grid(column=1, row=0, sticky='nesw')

# Read and set options from init file
init_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'pgn2scid.ini')
config = configparser.ConfigParser()

if os.path.isfile(init_file):
    try:
        config.read(init_file)
        dir_name = config.get('PATHS', 'work_path')
        path_select_frame.delete(0, END)
        path_select_frame.insert(0, dir_name)
        enable_twic_value = config.getboolean('GENERAL', 'enable_twic_auto_dl')
        twic_dl.set(enable_twic_value)
        twic_max = config.get('GENERAL', 'twic_max')
        extract_pgn_value = config.getboolean('GENERAL', 'extract_pgn_files')
        do_zip.set(extract_pgn_value)
        if extract_pgn_value:
            enable_decompress_options()
        delete_zip_value = config.getboolean('GENERAL', 'delete_zip_files')
        delete_zip.set(delete_zip_value)
        merge_pgn_value = config.getboolean('GENERAL', 'merge_pgn_files')
        do_merge.set(merge_pgn_value)
        if merge_pgn_value:
            enable_merge_options()
        delete_pgn_value = config.getboolean('GENERAL', 'delete_pgn_files')
        delete_pgn.set(delete_pgn_value)
        convert_pgn_value = config.getboolean('GENERAL', 'convert_pgn_to_scid')
        do_scid.set(convert_pgn_value)
        if convert_pgn_value:
            enable_pgnscid_options()
        delete_mpgn_value = config.getboolean('GENERAL', 'delete_remaining_pgn')
        delete_mpgn.set(delete_mpgn_value)
        merge_scid_value = config.getboolean('GENERAL', 'merge_scid_database')
        do_scmerge.set(merge_scid_value)
        if merge_scid_value:
            enable_scmerge_options()
        write_zipped_scid_value = config.getboolean('GENERAL', 'write_zipped_scid_copy')
        zip_scid_db.set(write_zipped_scid_value)
        delete_scid_value = config.getboolean('GENERAL', 'delete_scid_files')
        delete_scidfile.set(delete_scid_value)
        file_name = config.get('PATHS', 'database_dir')
        file_select_db["state"] = "normal"
        file_select_db.delete(0, END)
        file_select_db.insert(0, file_name)
        if not merge_scid_value:
            file_select_db["state"] = "disabled"
    except configparser.ParsingError as parsing_error:
        error_disp(2, 'Parsing Error', str(parsing_error))
    except configparser.NoSectionError as no_section_error:
        error_disp(2, 'Missing Section', str(no_section_error))
    except ValueError as val_error:
        error_disp(2, 'Value Error', str(val_error))
    except KeyError as key_error:
        error_disp(2, 'Key Error', str(key_error))
    except Exception:
        error_disp(1, 'Unexpected Error', 'Unexpected error while\n trying to read pgn2scid.ini!')
else:
    twic_max = 0

main_frame.mainloop()
