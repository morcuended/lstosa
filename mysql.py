#!/usr/bin/env python2.6
from standardhandle import output, warning, verbose, error, stringify, gettag
import options, cliopts 
import config
##############################################################################
#
# select_db
#
##############################################################################
def select_db(servername, username, database, table, selections, conditions):
    tag = gettag()

    appendix = None
    feedback = select_appendix_db(servername, username, database, table,\
     selections, conditions, appendix)
    return feedback
##############################################################################
#
# select_appendix_db
#
##############################################################################
def select_appendix_db(servername, username, database, table, selections,\
     conditions, appendix):
    tag = gettag()

    verb = select_selections(selections)
    assignments = {}
    feedback = query_db(servername, username, database, table, verb,\
     assignments, conditions, appendix)
    """ The returned object will be a matrix: list of lists """
    matrix = []
    if feedback:
        for line in feedback.splitlines():
            fields = line.split('\t')
            if len(fields) == len(selections):
                # Allright
                pass
            else:
                error(tag, "Wrong number of selected items {0}".format(fields), 8)
            matrix.append(fields)
    return matrix
##############################################################################
#
# insert_and_select_id_db
#
##############################################################################
def insert_and_select_id_db(servername, username, database, table,\
     assignments, conditions):
    tag = gettag()

    id = None
    verb = 'INSERT IGNORE'
    appendix = '; SELECT LAST_INSERT_ID()'
    feedback = query_db(servername, username, database, table, verb,\
                assignments, conditions, appendix)
    """ If simulation, better have a method to return 0 anyway """
    if not feedback:
       id = 0
    else:
       id = int(feedback.strip())
    verbose(tag, "LAST_INSERT_ID is {0}".format(id))
    return id
##############################################################################
#
# update_and_select_id_db
#
##############################################################################
def update_and_select_id_db(servername, username, database, table,\
     assignments, conditions):
    tag = gettag()

    id = None
    selections = ['ID']
    feedback = select_db(servername, username, database, table,\
                selections, conditions)
    if len(feedback) > 0:
        id = int(feedback[0][0])
        conditions = {'ID': id}
        verb = 'UPDATE IGNORE'
        appendix = None
        feedback = query_db(servername, username, database, table, verb,\
                    assignments, conditions, appendix)
    else:
        """ If simulation, better have a method to return 0 anyway """
        id = 0
    return id 
#############################################################################
#
# update_or_insert_and_select_id_db
#
##############################################################################
def update_or_insert_and_select_id_db(servername, username, database, table,\
     assignments, conditions):
    tag = gettag()

    """ It tries an update of the db and, if it fails, then inserts """
    feedback = None
    id = update_and_select_id_db(servername, username, database, table,\
          assignments, conditions)
    if id == 0:
        """ There was no update, proceed with insertion """
        assignments.update(conditions)
        conditions = {}
        id = insert_and_select_id_db(servername, username, database, table,\
              assignments, conditions)
        verbose(tag, "Inserted with ID={0}".format(id))
    else:
        verbose(tag, "Updated with ID={0}".format(id))
    return id
##############################################################################
#
# insert_db
#
##############################################################################
def insert_db(servername, username, database, table, assignments,\
     conditions):
    tag = gettag()

    verb = 'INSERT'
    appendix = None
    feedback = query_db(servername, username, database, table, verb,\
     assignments, conditions, appendix)
    return feedback
##############################################################################
#
# update_db
#
##############################################################################
def update_db(servername, username, database, table, assignments,\
     conditions):
    tag = gettag()

    verb = 'UPDATE'
    appendix = None
    feedback = query_db(servername, username, database, table, verb,\
     assignments, conditions, appendix)
    return feedback
##############################################################################
#
# insert_ignore_db
#
##############################################################################
def insert_ignore_db(servername, username, database, table, assignments,\
     conditions):
    tag = gettag()

    verb = 'INSERT IGNORE'
    appendix = None
    feedback = query_db(servername, username, database, table, verb,\
     assignments, conditions, appendix)
    return feedback
##############################################################################
#
# update_ignore_db
#
##############################################################################
def update_ignore_db(servername, username, database, table, assignments,\
     conditions):
    tag = gettag()

    verb = 'UPDATE IGNORE'
    appendix = None
    feedback = query_db(servername, username, database, table, verb,\
     assignments, conditions, appendix)
    return feedback
##############################################################################
#
# query_db
#
##############################################################################
def query_db(servername, username, database, table, verb, assignments,\
     conditions, appendix):
    tag = gettag()
    set_a = set_assignments(assignments)
    where_c = where_conditions(conditions)
    sql_command = "{0} {1} {2} {3}".format(verb, table, set_a, where_c)
    if appendix:
        sql_command += " {0}".format(appendix) 
    feedback = connect_or_call(servername, username, database, sql_command)
    return feedback
##############################################################################
#
# select_selections
#
##############################################################################
def select_selections(selections):
    tag = gettag()

    string = phrase_builder('SELECT', ',', selections)
    string += ' FROM'
    return string
##############################################################################
#
# set_assignments_where_conditions
#
##############################################################################
def set_assignments(assignments):
    tag = gettag()

    string = phrase_builder('SET', ',', assignments)
    return string
##############################################################################
#
# where_conditions
#
##############################################################################
def where_conditions(conditions):
    tag = gettag()

    string = phrase_builder('WHERE', ' AND', conditions)
    return string
##############################################################################
#
# phrase_builder
#
##############################################################################
def phrase_builder(instruction, junction, assignments):
    tag = gettag()

    """ With the assignments as a dictionary, we can compose a sentence,
        starting by instruction and separated by the junction. """

    import types
    string = ''
    if len(assignments) != 0:
        phrase = instruction
        #if type(assignments) == types.DictType:
        if type(assignments) == types.MemberDescriptorType:
            for key in assignments:
                if assignments[key] != None:
                    if key=="MD5SUM":
                        # Force checksums to be strings
                        phrase += " {0}='{1}'{2}".format(key, assignments[key], junction)
                    elif is_number(assignments[key]) or is_parenthesis(assignments[key]):
                        phrase += " {0}={1}{2}".format(key, assignments[key], junction)
                    else:
                        phrase += " {0}='{1}'{2}".format(key, assignments[key], junction)
                else:
                    phrase += " {0}=NULL{1}".format(key, junction)
        #elif type(assignments) == types.ListType:
        elif type(assignments) == types.FrameType:
            for element in assignments:
                phrase += " {0}{1}".format(element, junction)
        string = phrase.rstrip(junction)
    return string
##############################################################################
#
# is_number 
#
##############################################################################
def is_number(s):
    tag = gettag()

    """ It allows to check if the entry s is a number or not. """

    try:
        # chapuza to make it slightly more robust: 
        # even if we can convert to float 
        # it is not a number if the number is absurdly
        # long and there's no decimal point 
        float(s)
        assert(len(s)<20 or "." in s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False
    except AssertionError:
        return False
##############################################################################
#
# is_parenthesis 
#
##############################################################################
def is_parenthesis(s):
    tag = gettag()

    """ It checks wheter the string is enclosed by parenthesis """
    if isinstance(s, str) and len(s)> 0:
        if s[0] == '(' and s[-1] == ')':
            return True
    return False
##############################################################################
#
# connect_or_call (fill the mysql table)
#
##############################################################################
def connect_or_call(servername, username, database, sql_command):
    tag = gettag()

    """ This is a frontend def to allow making a subprocess call if the api is
    not available, instead of crying because of broken python installation. """

    feedback = None
    if not options.simulate:
        try:
            import MySQLdb
        except ImportError:
            feedback = subprocess_call_db(servername, username, database, sql_command)
        else:
            feedback = connect_db(servername, username, database, sql_command)
    else:
        verbose(tag, "SIMULATE query to database: {0}".format(sql_command))
    return feedback
##############################################################################
#
# subprocess_call_db
#
##############################################################################
def subprocess_call_db(servername, username, database, sql_command):
    tag = gettag()
    # Let's do it through a system call
    import subprocess
    feedback = None
    commandargs = ['mysql']
    if servername:
        commandargs.append('-h')
        commandargs.append(servername)
    if username:
        commandargs.append('-u')
        commandargs.append(username)
    if database:
        commandargs.append('-D')
        commandargs.append(database)
    commandargs.append('--batch')
    commandargs.append('-N')
    commandargs.append('-e')
    '''
    if len(sql_command.split(" MD5SUM=")) != 1:
        md5sum_text = str(sql_command.split(' MD5SUM=')[-1].split(',')[0])
        outer  = sql_command.split(md5sum_text)
        #print(md5sum_text)
        #new = "'%s'"% md5sum
        #print(md5sum, new)
        #sql_command.replace(old, inew)
        if "NULL" not in md5sum_text:
            sql_command = str("%s'%s'%s" %(outer[0],md5sum_text,outer[1]))
    '''
    commandargs.append(sql_command)
    #print(commandargs)
    try:
        feedback = subprocess.check_output(commandargs)
    #except OSError as (ErrorValue, ErrorName):
    except OSError as ErrorValue:
        error(tag, ErrorName, ErrorValue)
    except subprocess.CalledProcessError as e:
        error(tag, "MySQL> {0}: {1}".format(stringify(e.cmd), e.output), e.returncode)
    else:
        verbose(tag, "Database query OK: {0}".format(sql_command))
    return feedback
##############################################################################
#
# connect_db
#
##############################################################################
def connect_db(servername, username, database, sql_command):
    tag = gettag()
    # Let's do it through the API
    import MySQLdb
    try:
        conn = MySQLdb.connect(host=servername, user=username, db=database)
    except MySQLdb.OperationalError (ValueError, NameError):
        error("Could not connect to Database {0}, {1}".format(database, NameError), ValueError)
    else:
        x = conn.cursor()
        try:
            x.execute(sql_command)
        except MySQLdb.Error (ValueError, NameError):
            conn.rollback()
            error(tag, "MySQL> {0}: {1}".format(sql_command, NameError), ValueError)
        else:
            feedback = x.fetchall()
            conn.commit()
            verbose(tag, "Database query OK: {0}".format(sql_command))
        conn.close()
    return feedback
