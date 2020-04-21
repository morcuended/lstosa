#!/usr/bin/env python2.7
##############################################################################
#
# closer.py
#
#
##############################################################################
from osa.utils.standardhandle import output, verbose, warning, error, stringify, gettag
from osa.configs.config import cfg

__all__ = ["closer", "is_day_closed", "use_night_summary",
"is_raw_data_available", "is_sequencer_successful", "notify_sequencer_errors",
"ask_for_closing", "notify_neither_data_nor_reason_given", "post_process",
"post_process_files","set_closed_in_db", "set_closed_in_analysis_db",
"set_closed_in_summary_db", "set_closed_with_file", "ape", "is_finished_check",
"synchronize_remote", "setclosedfilename"]
##############################################################################
#
# closer
#
##############################################################################
def closer():
    tag = gettag()
    import datetime
    from osa.utils import options, cliopts
    from osa.reports.report import start
    from osa.nightsummary.nightsummary import readnightsummary
    from osa.utils.utils import is_defined

    """ Initiating report. """

    start(tag)

    """ Starting the algorithm. """

    if is_day_closed():
        # Exit
        error(tag, "Night {0} already closed for {1}"\
         .format(options.date, options.tel_id), 1)
    else:
        # Proceed
        if options.seqtoclose != None:
            output(tag, "Closing sequence {0}".format(options.seqtoclose))
        sequencer_tuple = []
        if options.reason != None: 
            # No data
            warning(tag, "No data found")
            sequencer_tuple = [False, []]
            if is_defined(options.reason):
                # Good user, proceed automatically
                pass
            else:
                # Notify and Ask for closing and a reason
                notify_neither_data_nor_reason_given()
                #ask_for_closing()
                ask_for_reason()
            # Proceed with a reason
        #elif is_raw_data_available() or use_night_summary():
        elif use_night_summary():
            # Proceed normally
            verbose(tag, "Checking sequencer_tuple {0}".format(sequencer_tuple))
            night_summary_output = readnightsummary()
            sequencer_tuple = is_finished_check(night_summary_output)

            if is_sequencer_successful(sequencer_tuple):
                # Close automatically
                pass
            else:
                # Notify and ask for closing
                notify_sequencer_errors()
                #ask_for_closing()
        else:
            error(tag, "Never thought about this possibility,\
             please check the code", 9)
        post_process(sequencer_tuple)
##############################################################################
#
# is_day_closed
#
##############################################################################
def is_day_closed():
    tag = gettag()

    """ Get the name and Check for the existence of the Closer flag file. """

    from os.path import exists
    from osa.utils.utils import getlockfile

    answer = False 
    flag_file = getlockfile()
    if exists(flag_file):
        answer = True
    return answer
##############################################################################
#
#
#
##############################################################################
def use_night_summary():
    tag = gettag()

    """ Check for the usage of night summary option and file existance. """

    from os.path import exists
    from osa.nightsummary.nightsummary import getnightsummaryfile
    
    answer = False
    if options.nightsum:
        night_file = getnightsummaryfile()
        if exists(night_file):
            answer = True
        else:
            output(tag, "Night Summary expected but it does not exists.")
            output(tag, "Please check it or use the -r option\
             to give a reason.")
            error(tag, "Night Summary missing and no reason option", 2)
    return answer
##############################################################################
#
#
#
##############################################################################
def is_raw_data_available():
    tag = gettag()

    """ For the moment we are happy to get the rawdir and check existance.
        This means the raw directory could be empty! """

    from os.path import isdir
    from osa.rawcopy.raw import get_check_rawdir
    answer = False
    if options.tel_id != 'ST':
        pass
        raw_dir = get_check_rawdir()
        if isdir(raw_dir):
            answer = True
    else:
        answer = True
    return answer
##############################################################################
#
#
#
##############################################################################
def is_sequencer_successful(seq_tuple):
    tag = gettag()

    """ A strange way to check it.
        TODO: implement a more reliable non-intrusive than is_finished_check.
        """

    answer = seq_tuple[0]
    return answer
##############################################################################
#
#
#
##############################################################################
def notify_sequencer_errors():
    tag = gettag()

    """ A good notification helps the user on deciding to close it or not. """

    output(tag, "Sequencer did not complete or finish unsuccesfully")
    pass
##############################################################################
#
#
#
##############################################################################
def ask_for_closing():
    tag = gettag()

    """ A True (Y/y) closes, while False(N/n) answer stops the program. """

    import sys
    answer = False
    if options.noninteractive:
        """ In not-interactive mode, we assume the answer is yes. """
        pass
    else:
        answer_check = False
        while not answer_check:
            try:
                question = 'Close that day? (y/n): '
                if options.simulate:
                    question += '[SIMULATE ongoing] '
                answer_user = raw_input(question)
            except KeyboardInterrupt:
                print ('')
                warning(tag, "Program quitted by user. No answer")
                sys.exit(1)
            except EOFError as ErrorValue:
                error(tag, "End of file not expected", ErrorValue)
            else:
                answer_check = True
                if answer_user == 'n' or answer_user == 'N':
                    # The user does not want to close
                    output(tag, "Day {0} for {1} will remain open".\
                        format(options.date, options.tel_id))
                    sys.exit(0) 
                elif answer_user == 'y' or answer_user == 'Y':
                    continue
                else:
                    warning(tag, "Answer not understood, please type y or n")
                    answer_check = False
##############################################################################
#
# notify_neither_data_nor_reason_given
#
##############################################################################
def notify_neither_data_nor_reason_given():
    tag = gettag()

    """ Message informing the user of the situation """

    output(tag, "There is no data and you did not enter any reason for that")
##############################################################################
#
# post_process
#
##############################################################################
def post_process(seq_tuple):
    tag = gettag()

    """ Set of last instructions. """
    
    from osa.reports.report import finished_assignments, finished_text
    seq_list = seq_tuple[1]
    #analysis_dict = finished_assignments(seq_list)
    #analysis_text = finished_text(analysis_dict)
    post_process_files(seq_list)
    set_closed_in_db(analysis_dict)
    if options.seqtoclose == None:
        is_closed = set_closed_with_file(analysis_text)
        return is_closed
    return False
##############################################################################
#
# post_process_files
#
##############################################################################
def post_process_files(seq_list):
    tag = gettag()
    
    """ The hard job of executing the last tasks for files. """

    from os.path import join, basename, exists, islink
    from os import rename, unlink
    from filecmp import cmp
    from glob import glob
    from re import search
    from config import cfg
    from veto import createclosed
    from utils import magicdate_to_dir, make_directory
    from register import register_run_concept_files

    concept_set = []
    if options.tel_id == 'LST1' or options.tel_id == 'LST2':
        concept_set = ['SCALIB',  'SSIGNAL', 'SORCERER', 'MERPP',\
        'STARHISTOGRAM', 'STAR']
    elif options.tel_id == 'ST':
        concept_set = ['SUPERSTAR', 'SUPERSTARHISTOGRAM', 'MELIBEA', 'MELIBEAHISTOGRAM'] 

    middle_dir = magicdate_to_dir(options.date)
    root_files = glob(join(options.directory,\
     '*{0}'.format(cfg.get('OSA', 'ROOTSUFFIX'))))
    root_set = set(root_files)
    pattern = None
    for concept in concept_set:
        output(tag, "Processing {0} files, {1} files left".format(concept, len(root_set)))
        if cfg.get('OSA', concept + 'PREFIX'):
            pattern = cfg.get('OSA', concept + 'PREFIX')
        else:
            pattern = cfg.get('OSA', concept + 'PATTERN')

        dir = join(cfg.get(options.tel_id, concept + 'DIR'), middle_dir)
        delete_set = set()
        verbose(tag, "Checking if {0} files need to be moved to {1}".format(concept, dir))
        for r in root_set:
            r_basename = basename(r)
            pattern_found = search(pattern, r_basename)
            verbose(tag, "Was pattern {0} found in {1} ?: {2}"\
             .format(pattern, r_basename, pattern_found))
            if options.seqtoclose != None:
                seqtoclose_found = search(options.seqtoclose, r_basename)
                verbose(tag, "Was pattern {0} found in {1} ?: {2}"\
                 .format(options.seqtoclose, r_basename, seqtoclose_found))
                if seqtoclose_found == None:
                    pattern_found = None
            if pattern_found != None:
                new_dst = join(dir, r_basename)
                if not options.simulate:
                    make_directory(dir)
                    if exists(new_dst):
                        if islink(r):
                            # Delete because the link has been correctly copied
                            verbose(tag, "Original file {0} is just a link".format(r))
                            if options.seqtoclose == None:
                                verbose(tag, "Deleting {0}".format(r))
                                unlink(r)
                        elif cmp(r, new_dst):
                            # Delete
                            verbose(tag, "Destination file exists and it is equal to {0}".format(r))
                            if options.seqtoclose == None:
                                verbose(tag, "Deleting {0}".format(r))
                                unlink(r)
                        else:
                            warning(tag, "Original file {0} is not a link or is different than destination {1}".format(r, new_dst))
                    else:
                        verbose(tag, "Destination file {0} does not exists".format(new_dst))
                        for s in seq_list:
                            verbose(tag, "Looking for {0}".format(s))
                            run_str_found = search(s.run_str, r_basename)
                            if run_str_found != None:
                                # Register and delete
                                verbose(tag, "Registering file {0}".format(run_str_found))
                                register_run_concept_files(s.run_str, concept)
                                if options.seqtoclose == None:
                                    unlink(r)
                                setclosedfilename(s)
                                createclosed(s.closed)
                                break
                delete_set.add(r)
        root_set -= delete_set
##############################################################################
#
# set_closed_in_db
#
############################################################################## 
def set_closed_in_db(ana_dict):
    tag = gettag()

    """ Prepare the calls for the different tables. """

    import config

    servername = config.cfg.get('MYSQL', 'SERVER')
    username = config.cfg.get('MYSQL', 'USER')
    database = config.cfg.get('MYSQL', 'DATABASE')
    if options.seqtoclose == None:
        set_closed_in_analysis_db(servername, username, database, ana_dict)
    # the next line triggers the transfer to PIC, if the day and telescope is
    # closed in the summary database it will look into the storage database to
    # get the the list of files.
    set_closed_in_summary_db(servername, username, database, ana_dict)
##############################################################################
#
#
#
##############################################################################
def set_closed_in_analysis_db(servername, username, database, ana_dict):
    tag = gettag()

    """ Insert the analysis key=value into the database. """

    from os.path import exists, join
    from config import cfg, read_properties
    from mysql import insert_ignore_db

    table = cfg.get('MYSQL', 'ANALYSISTABLE')
    incidences_file = join(options.directory,\
     cfg.get('OSA', 'INCIDENCESPREFIX') + cfg.get('OSA', 'TEXTSUFFIX'))

    assignments = dict()
    assignments.update(ana_dict)

    if exists(incidences_file):
        """ Add the incidences file """
        incidences_cfg = read_properties(incidences_file)
        assignments['COMMENTS'] = incidences_cfg.get('DUMMY', 'COMMENTS')

    del assignments['RAW_GB']
    del assignments['FILES_RAW']
    del assignments['END']
    
    conditions = {}
    insert_ignore_db(servername, username, database, table, assignments,\
     conditions)
##############################################################################
#
#
#
##############################################################################
def set_closed_in_summary_db(servername, username, database, ana_dict):
    tag = gettag()

    """ Insert the analysis key=value into the database. """

    import config
    from mysql import update_or_insert_and_select_id_db
    table = config.cfg.get('MYSQL', 'SUMMARYTABLE')

    conditions = {'ACTIVITY': 'OSA'}
    for i in ['TELESCOPE', 'NIGHT']:
        conditions[i] = ana_dict[i]
    verbose(tag, "Analysis dictionary is {0}".format(ana_dict))
    assignments = {'IS_FINISHED': ana_dict['IS_CLOSED'],\
     'END': ana_dict['END']}

    update_or_insert_and_select_id_db(servername, username, database, table,\
     assignments, conditions)
##############################################################################
#
# set_closed_with_file
#
##############################################################################
def set_closed_with_file(ana_text):
    tag = gettag()

    """ Write the analysis report to the closer file. """

    from utils import getlockfile, createlock
    closer_file = getlockfile()
    is_closed = False
    if not options.simulate:
        is_closed = createlock(closer_file, ana_text)
    else:
        output(tag, "SIMULATE Creation of lock file {0}".format(closer_file))

    """ The close file will be send to a remote monitor server """
    if is_closed:
        synchronize_remote(closer_file)

    return is_closed
##############################################################################
#
# ape
#
##############################################################################
def ape():
    tag = gettag()
    # TODO: include error report from new Mars
    pass
##############################################################################
#
# is_finished_check
#
##############################################################################
def is_finished_check(nightsum):
    tag = gettag()
    from osa.rawcopy.raw import arerawfilestransferred
    from osa.nightsummary.extract import extractsubruns, extractruns, extractsequences
    from osa.jobs.job import arealljobscorrectlyfinished
    # We ought to implement a method of successful or unsuccesful finishing
    # and it is done looking at the files
    sequence_list = None
    sequence_success = False
    if nightsum == '':
        # Empty file (no sensible data)
        sequence_success = True
        sequence_list = []
    else:
        # Building the sequences (the same way than the sequencer)
        #if options.tel_id == "ST":
        #    nightsum_lines = nightsum.split("\n")
        #    lines = [ l for l in nightsum_lines if "CALIBRATION" not in l ]
        #    nightsum = '\n'.join(lines)
        subrun_list = extractsubruns(nightsum)
        run_list = extractruns(subrun_list)
        sequence_list = extractsequences(run_list)
        # Adds the scripts to sequences
        # job.preparejobs(sequence_list, run_list, subrun_list)   
#        if arerawfilestransferred():
#            verbose(tag, "Are files transferred? {0}".format(sequence_list))
#            if arealljobscorrectlyfinished(sequence_list):
#                sequence_success = True
#            else:
#                output(tag,\
#                 "All raw files are transferred but the jobs did not correctly/yet finish")
#        else:
#            output(tag, "More raw files are expected to appear")

    return [sequence_success, sequence_list]
##############################################################################
#
# isfinishedcheck
#
##############################################################################
def synchronize_remote(lockfile):
    tag = gettag()
    from os.path import join, basename
    from re import sub
    import subprocess
    from config import cfg
    user = cfg.get('REMOTE', 'STATISTICSUSER')
    host = cfg.get('REMOTE', 'STATISTICSHOST')
    remotedirectory = join(cfg.get('REMOTE', 'STATISTICSDIR'), options.tel_id)
    remotebasename = options.date + cfg.get('REMOTE', 'STATISTICSSUFFIX')
    remotepath = join(remotedirectory, remotebasename)
    output(tag, "Synchronizing {0} {1} by copying lock file to {2}@{3}:{4}".\
        format(options.tel_id, options.date, user, host, remotepath))
    commandargs = ['scp']
    commandargs.append('-P')
    commandargs.append(cfg.get('REMOTE', 'STATISTICSSSHPORT'))
    commandargs.append(lockfile)
    commandargs.append(user + '@' + host + ':' + join(remotedirectory,\
     remotebasename))
    try:
        subprocess.call(commandargs)
    #except OSError as (ValueError, NameError):
    except OSError as NameError:
        warning(tag, "Could not copy securely with command: {0}, {1}".\
            format(stringify(commandargs), NameError))
##############################################################################
#
# setclosedfilenames
#
##############################################################################
def setclosedfilename(s):
    tag = gettag()
    import os.path
    from config import cfg
    closed_suffix = cfg.get('OSA', 'CLOSEDSUFFIX')
    basename = "sequence_{0}".format(s.jobname)
    s.closed = os.path.join(options.directory, basename + closed_suffix )
##############################################################################
#
# MAIN
#
##############################################################################
if __name__ == '__main__':
    tag = gettag()
    import sys
    from osa.utils import options, cliopts
    # Set the options through cli parsing
    cliopts.closercliparsing()
    # Run the routine
    closer()