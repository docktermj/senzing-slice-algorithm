#! /usr/bin/env python

# -----------------------------------------------------------------------------
# slice-algorithm.py Loader for streaming input.
# -----------------------------------------------------------------------------

import argparse
import csv
import json
import logging
import os
import sys
import time

__all__ = []
__version__ = 1.0
__date__ = '2018-10-29'
__updated__ = '2019-05-16'

SENZING_PRODUCT_ID = "9999"  # See https://github.com/Senzing/knowledge-base/blob/master/lists/senzing-product-ids.md
log_format = '%(asctime)s %(message)s'

# The "configuration_locator" describes where configuration variables are in:
# 1) Command line options, 2) Environment variables, 3) Configuration files, 4) Default values

configuration_locator = {
    "csv_file": {
        "default": None,
        "env": "SENZING_CSV_FILE",
        "cli": "csv-file"
    },
    "prior_csv_file": {
        "default": None,
        "env": "SENZING_PRIOR_CSV_FILE",
        "cli": "prior-csv-file"
    },
    "current_csv_file": {
        "default": None,
        "env": "SENZING_CURRENT_CSV_FILE",
        "cli": "current-csv-file"
    }
}

# -----------------------------------------------------------------------------
# Define argument parser
# -----------------------------------------------------------------------------


def get_parser():
    '''Parse commandline arguments.'''
    parser = argparse.ArgumentParser(prog="slice-algorithm.py", description="Test the Slice Algorithm. For more information, see https://pdfs.semanticscholar.org/ee8e/13f3f17a2660331a3a17ba8a7cfb06f9b61d.pdf")
    subparsers = parser.add_subparsers(dest='subcommand', help='Subcommands (SENZING_SUBCOMMAND):')

    subparser_1 = subparsers.add_parser('show-entities', help='Test algorithm.')
    subparser_1.add_argument("--csv-file", dest="csv_file", metavar="SENZING_CSV_FILE", help="CSV file.")

    subparser_2 = subparsers.add_parser('test', help='Test algorithm.')
    subparser_2.add_argument("--prior-csv-file", dest="prior_csv_file", metavar="SENZING_PRIOR_CSV_FILE", help="Earlier of the CSV files.")
    subparser_2.add_argument("--current-csv-file", dest="current_csv_file", metavar="SENZING_CURRENT_CSV_FILE", help="Later of the CSV files")

    return parser

# -----------------------------------------------------------------------------
# Message handling
# -----------------------------------------------------------------------------

# 1xx Informational (i.e. logging.info())
# 2xx Warning (i.e. logging.warn())
# 4xx User configuration issues (either logging.warn() or logging.err() for Client errors)
# 5xx Internal error (i.e. logging.error for Server errors)
# 9xx Debugging (i.e. logging.debug())


message_dictionary = {
    "100": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}I",
    "101": "Enter {0}",
    "102": "Exit {0}",
    "103": "Calculated Cost: {0}",
    "104": "Entity id: {0}  Records: {1}",
    "105": "Variable: {0}  Value: {1}",
    "106": "Key: {0}  Value: {1}",
    "199": "{0}",
    "200": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}W",
    "400": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}E",
    "498": "Bad SENZING_SUBCOMMAND: {0}.",
    "499": "No processing done.",
    "500": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}E",
    "501": "Error: {0} for {1}",
    "599": "Program terminated with error.",
    "900": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}D",
    "999": "{0}",
}


def message(index, *args):
    index_string = str(index)
    template = message_dictionary.get(index_string, "No message for index {0}.".format(index_string))
    return template.format(*args)


def message_generic(generic_index, index, *args):
    index_string = str(index)
    return "{0} {1}".format(message(generic_index, index), message(index, *args))


def message_info(index, *args):
    return message_generic(100, index, *args)


def message_warn(index, *args):
    return message_generic(200, index, *args)


def message_error(index, *args):
    return message_generic(500, index, *args)


def message_debug(index, *args):
    return message_generic(900, index, *args)


def get_exception():
    ''' Get details about an exception. '''
    exception_type, exception_object, traceback = sys.exc_info()
    frame = traceback.tb_frame
    line_number = traceback.tb_lineno
    filename = frame.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, line_number, frame.f_globals)
    return {
        "filename": filename,
        "line_number": line_number,
        "line": line.strip(),
        "exception": exception_object,
        "type": exception_type,
        "traceback": traceback,
    }

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


def get_ini_filename(args_dictionary):
    ''' Find the slice-algorithm.ini file in the filesystem.'''

    # Possible locations for slice-algorithm.ini

    filenames = [
        "{0}/slice-algorithm.ini".format(os.getcwd()),
        "{0}/slice-algorithm.ini".format(os.path.dirname(os.path.realpath(__file__))),
        "{0}/slice-algorithm.ini".format(os.path.dirname(os.path.abspath(sys.argv[0]))),
        "/etc/slice-algorithm.ini",
        "/opt/senzing/g2/python/slice-algorithm.ini",
    ]

    # Return first slice-algorithm.ini found.

    for filename in filenames:
        final_filename = os.path.abspath(filename)
        if os.path.isfile(final_filename):
            return final_filename

    # If file not found, return None.

    return None


def get_configuration(args):
    ''' Order of precedence: CLI, OS environment variables, INI file, default.'''
    result = {}

    # Copy default values into configuration dictionary.

    for key, value in configuration_locator.items():
        result[key] = value.get('default', None)

    # "Prime the pump" with command line args. This will be done again as the last step.

    for key, value in args.__dict__.items():
        new_key = key.format(subcommand.replace('-', '_'))
        if value:
            result[new_key] = value

    # Copy INI values into configuration dictionary.

    ini_filename = get_ini_filename(result)
    if ini_filename:

        result['ini_filename'] = ini_filename

        config_parser = configparser.RawConfigParser()
        config_parser.read(ini_filename)

        for key, value in configuration_locator.items():
            keyword_args = value.get('ini', None)
            if keyword_args:
                try:
                    result[key] = config_parser.get(**keyword_args)
                except:
                    pass

    # Copy OS environment variables into configuration dictionary.

    for key, value in configuration_locator.items():
        os_env_var = value.get('env', None)
        if os_env_var:
            os_env_value = os.getenv(os_env_var, None)
            if os_env_value:
                result[key] = os_env_value

    # Copy 'args' into configuration dictionary.

    for key, value in args.__dict__.items():
        new_key = key.format(subcommand.replace('-', '_'))
        if value:
            result[new_key] = value

    # Special case: subcommand from command-line

    if args.subcommand:
        result['subcommand'] = args.subcommand

    # Special case: Change boolean strings to booleans.

    booleans = ['debug']
    for boolean in booleans:
        boolean_value = result.get(boolean)
        if isinstance(boolean_value, str):
            boolean_value_lower_case = boolean_value.lower()
            if boolean_value_lower_case in ['true', '1', 't', 'y', 'yes']:
                result[boolean] = True
            else:
                result[boolean] = False

    # Special case: Change integer strings to integers.

    integers = []
    for integer in integers:
        integer_string = result.get(integer)
        result[integer] = int(integer_string)

    return result


def validate_configuration(config):
    '''Check aggregate configuration from commandline options, environment variables, config files, and defaults.'''

    user_warning_messages = []
    user_error_messages = []

    # Log warning messages.

    for user_warning_message in user_warning_messages:
        logging.warn(user_warning_message)

    # Log error messages.

    for user_error_message in user_error_messages:
        logging.error(user_error_message)

    # Log where to go for help.

    if len(user_warning_messages) > 0 or len(user_error_messages) > 0:
        logging.info(message_info(198))

    # If there are error messages, exit.

    if len(user_error_messages) > 0:
        exit_error(499)

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def entry_template(config):
    '''Format of entry message.'''
    config['start_time'] = time.time()

    # FIXME: Redact sensitive info:  Example: database password.

    config_json = json.dumps(config, sort_keys=True)
    return message_info(101, config_json)


def exit_template(config):
    '''Format of exit message.'''
    stop_time = time.time()
    config['stop_time'] = stop_time
    config['elapsed_time'] = stop_time - config.get('start_time', stop_time)

    # FIXME: Redact sensitive info:  Example: database password.

    config_json = json.dumps(config, sort_keys=True)
    return message_info(102, config_json)


def exit_error(index, *args):
    '''Log error message and exit program.'''
    logging.error(message_error(index, *args))
    logging.error(message_error(599))
    sys.exit(1)


def exit_silently():
    '''Exit program.'''
    sys.exit(1)


def common_prolog(config):
    validate_configuration(config)
    logging.info(entry_template(config))

# -----------------------------------------------------------------------------
# Utility functions for algorithm
# -----------------------------------------------------------------------------


def function_m(a, b):
    return max(a, b)

def function_s(a, b):
    return max(a, b)


def get_generator_from_csv(csv_filename):
    '''Tricky code.  Uses currying technique. Create a generator function
       that reads a CSV file and yields list of records for the same entity.
    '''

    def result_function():
        with open(csv_filename, newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            header = next(csv_reader)  # Read and discard CSV header.
            last_entity_id = 1
            result = []
            for row in csv_reader:
                entity_id = row[0]
                if int(entity_id) == last_entity_id:
                    result.append(row[1])
                else:
                    last_entity_id = int(entity_id)
                    yield result
                    result = [row[1]]
            yield result

    return result_function

# -----------------------------------------------------------------------------
# Algorithm
# -----------------------------------------------------------------------------


def merge_distance(prior_generator, current_generator, merge_cost_function, split_cost_function):

    prior_counter_dictionary = {}
    prior_generator_sizes = {}
    final_cost = 0

    # Translation
    # i = prior_counter
    # R = prior_generator
    # r = prior_item
    # M = prior_counter_dictionary
    # Rsizes = prior_generator_sizes
    # cost = final_cost
    # S = current_generator
    # pMap = partition_map
    # r = current_item
    # SiCost = si_cost
    # totalRecs = total_records

    # Process items in prior_generator.

    prior_counter = 0
    for prior_items in prior_generator():
        prior_counter += 1
        prior_generator_sizes[prior_counter] = len(prior_items)
        for prior_item in prior_items:
            prior_counter_dictionary[prior_item] = prior_counter
    logging.info(message_info(105, 'prior_generator_sizes', prior_generator_sizes))
    logging.info(message_info(105, 'prior_counter_dictionary', prior_counter_dictionary))

    # Process items in current_generator.

    current_counter = 0
    for current_items in current_generator():
        current_counter += 1
        si_cost = 0
        total_records = 0
        partition_map = {}

        # Populate partition_map.

        for current_item in current_items:
            if prior_counter_dictionary.get(current_item) not in partition_map.keys():
                partition_map[prior_counter_dictionary.get(current_item)] = 0
            partition_map[prior_counter_dictionary.get(current_item)] += 1
        logging.info(message_info(105, 'partition_map', partition_map))

        # Calculate si_cost.

        for key, value in partition_map.items():
            logging.info(message_info(106, key, value))
            if prior_generator_sizes[key] > value:
                si_cost = si_cost + split_cost_function(value, prior_generator_sizes[key] - value)
            prior_generator_sizes[key] -= value
            logging.info(message_info(105, 'prior_generator_sizes', prior_generator_sizes))

            if total_records != 0:
                si_cost += merge_cost_function(value, total_records)
            total_records += value
            logging.info(message_info(105, 'si_cost', si_cost))
            logging.info(message_info(105, 'total_records', total_records))
        logging.info(message_info(105, 'final: si_cost', si_cost))

        # Aggregate final cost.

        final_cost += si_cost
        logging.info(message_info(105, 'final_cost', final_cost))

    return final_cost

# -----------------------------------------------------------------------------
# do_* functions
#   Common function signature: do_XXX(args)
# -----------------------------------------------------------------------------


def do_show_entities(args):
    '''Read from URL-addressable file.'''

    # Get context from CLI, environment variables, and ini files.

    config = get_configuration(args)

    # Perform common initialization tasks.

    common_prolog(config)

    # Create generator.

    prior_generator = get_generator_from_csv(config.get('csv_file'))

    # Process lines.

    counter = 0
    for item in prior_generator():
        counter += 1
        logging.info(message_info(104, counter, item))

    # Epilog.

    logging.info(exit_template(config))


def do_test(args):
    '''Read from URL-addressable file.'''

    # Get context from CLI, environment variables, and ini files.

    config = get_configuration(args)

    # Perform common initialization tasks.

    common_prolog(config)

    # Create generators.

    prior_generator = get_generator_from_csv(config.get('prior_csv_file'))
    current_generator = get_generator_from_csv(config.get('current_csv_file'))

    # Calculate cost.

    cost = merge_distance(prior_generator, current_generator, function_m, function_s)
    logging.info(message_info(103, cost))

    # Epilog.

    logging.info(exit_template(config))

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


if __name__ == "__main__":

    # Configure logging. See https://docs.python.org/2/library/logging.html#levels

    log_level_map = {
        "notset": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "fatal": logging.FATAL,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    log_level_parameter = os.getenv("SENZING_LOG_LEVEL", "info").lower()
    log_level = log_level_map.get(log_level_parameter, logging.INFO)
    logging.basicConfig(format=log_format, level=log_level)

    # Parse the command line arguments.

    subcommand = os.getenv("SENZING_SUBCOMMAND", None)
    parser = get_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        subcommand = args.subcommand
    elif subcommand:
        args = argparse.Namespace(subcommand=subcommand)
    else:
        parser.print_help()
        exit_silently()

    # Transform subcommand from CLI parameter to function name string.

    subcommand_function_name = "do_{0}".format(subcommand.replace('-', '_'))

    # Test to see if function exists in the code.

    if subcommand_function_name not in globals():
        logging.warn(message_warn(498, subcommand))
        parser.print_help()
        exit_silently()

    # Tricky code for calling function based on string.

    globals()[subcommand_function_name](args)
