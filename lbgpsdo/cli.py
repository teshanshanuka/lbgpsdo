import argparse
import json
import sys

from .lbgpsdo import *

#
# Command Callbacks
#

def command_list(args):
    for d in GPSDODevice.enumerate():
        sys.stdout.write("%04x:%04x %-16s  %s  %s\n" % \
            (
                d['vendor_id'],
                d['product_id'],
                d['path'].decode(),
                d['serial_number'],
                d['product_string'],
            ))


def command_status(args):
    for d in GPSDODevice.openall(serial = args.serial, device = args.device):
        d.read_status()
        sys.stdout.write("%-8s  %s: SAT %-8s  PLL %-8s  Loss: %d\n" % \
            (
                d.serial,
                d.path,
                "locked" if d.sat_lock else "unlocked",
                "locked" if d.pll_lock else "unlocked",
                d.loss_count,
            ))


def command_detail(args):
    first = True
    for d in GPSDODevice.openall(serial = args.serial, device = args.device):
        d.read()
        if first:
            first = False
        else:
            sys.stdout.write("\n\n")
        sys.stdout.write(d.infotext())


def command_modify(args):
    d = GPSDODevice.open(serial = args.serial, device = args.device)

    try:
        d.read()
        d.update(**parser_get_config(args))
        sys.stdout.write(d.infotext(show_status = args.show_status, show_freq = args.show_freq))
        if not args.pretend:
            d.write(ignore_freq_limits = args.ignore_freq_limits)
    except GPSDOConfigurationException as e:
        sys.stdout.write("Parameter error:\n")
        sys.stdout.write(e.errortext())


def command_backup(args):
    d = GPSDODevice.open(serial = args.serial, device = args.device)

    try:
        d.read()
        sys.stdout.write(d.infotext(show_status = args.show_status, show_freq = args.show_freq))
        json.dump(d.asdict(ignore_freq_limits = args.ignore_freq_limits),
                  args.output_file, indent = 2)
    except GPSDOConfigurationException as e:
        sys.stdout.write("Parameter error:\n")
        sys.stdout.write(e.errortext())


def command_restore(args):
    d = GPSDODevice.open(serial = args.serial, device = args.device)

    try:
        d.update(**json.load(args.input_file))
        sys.stdout.write(d.infotext(show_status = False, show_freq = args.show_freq))
        if not args.pretend:
            d.write(ignore_freq_limits = args.ignore_freq_limits)
    except GPSDOConfigurationException as e:
        sys.stdout.write("Parameter error:\n")
        sys.stdout.write(e.errortext())


def command_identify(args):
    d = GPSDODevice.open(serial = args.serial, device = args.device)
    d.identify(args.out)


def command_analyze(args):
    if args.input_device or args.output_device:
        d = GPSDODevice.open(serial = args.serial, device = args.device)
    else:
        d = GPSDO()

    try:
        if args.input_device:
            d.read()
        elif args.input_file:
            d.update(**json.load(args.input_file))

        d.update(**parser_get_config(args))
        sys.stdout.write(d.infotext(show_status = False))

        if args.output_device:
            d.write(ignore_freq_limits = args.ignore_freq_limits)
        elif args.output_file:
            json.dump(d.asdict(ignore_freq_limits = args.ignore_freq_limits),
                      args.output_file, indent = 2)

    except GPSDOConfigurationException as e:
        sys.stdout.write("Parameter error:\n")
        sys.stdout.write(e.errortext())


def command_pll(args):
    sys.stdout.write(GPSDO().plltext())

#
# Command Line Parser Helper Functions
#

def parser_add_device(p):
    p.add_argument(
        '-s', '--serial',
        dest = 'serial',
        metavar = 'S/N',
        help = "Serial number of GPS device")

    p.add_argument(
        '-d', '--device',
        dest = 'device',
        metavar = 'PATH',
        help = "Path specification of the USB HID device")


def parser_add_input(p, required = False):
    p.add_argument(
        '-i', '--input-file',
        required = required,
        dest = 'input_file',
        metavar = 'FILE',
        type = argparse.FileType('r'),
        help = "Input configuration file")


def parser_add_multiinput(p):
    parser_multiinput = p.add_argument_group(
        title = "Input options")

    parser_multiinput = parser_multiinput.add_mutually_exclusive_group()

    parser_add_input(parser_multiinput)

    parser_multiinput.add_argument(
        '-I', '--input-device',
        dest = 'input_device',
        action = 'store_true',
        help = "Read configuration from device")


def parser_add_output(p, required = False):
    p.add_argument(
        '-o', '--output-file',
        required = required,
        dest = 'output_file',
        metavar = 'FILE',
        type = argparse.FileType('w'),
        help = "Output configuration file")


def parser_add_multioutput(p):
    parser_multioutput = p.add_argument_group(
        title = "Output options")

    parser_add_output(parser_multioutput)

    parser_multioutput.add_argument(
        '-O', '--output-device',
        dest = 'output_device',
        action = 'store_true',
        help = "Write configuration to device")


def parser_add_config(p):
    parser_config = p.add_argument_group(
        title = "Configuration")

    parser_config.add_argument(
        '--fin',
        dest = 'fin',
        metavar = 'HZ',
        type = int,
        help = "GPS reference frequency")

    parser_config.add_argument(
        '--n3',
        dest = 'n3',
        metavar = 'N',
        type = int,
        help = "Input divider factor")

    parser_config.add_argument(
        '--n2-hs',
        dest = 'n2_hs',
        metavar = 'N',
        type = int,
        help = "Feedback divider factor (high speed)")

    parser_config.add_argument(
        '--n2-ls',
        dest = 'n2_ls',
        metavar = 'N',
        type = int,
        help = "Feedback divider factor (low speed)")

    parser_config.add_argument(
        '--n1-hs',
        dest = 'n1_hs',
        metavar = 'N',
        type = int,
        help = "Output divider factor (high speed)")

    parser_config.add_argument(
        '--nc1-ls',
        dest = 'nc1_ls',
        metavar = 'N',
        type = int,
        help = "Output 1 divider factor (low speed)")

    parser_config.add_argument(
        '--nc2-ls',
        dest = 'nc2_ls',
        metavar = 'N',
        type = int,
        help = "Output 2 divider factor (low speed)")

    parser_config.add_argument(
        '--skew',
        dest = 'skew',
        metavar = 'N',
        type = int,
        help = "Output 2 clock skew")

    parser_config.add_argument(
        '--bw',
        dest = 'bw',
        metavar = 'MODE',
        type = int,
        help = "Bandwith mode")

    parser_config.add_argument(
        '--enable-out1',
        dest = 'out1',
        action = 'store_const',
        const = True,
        help = "Enable output 1")

    parser_config.add_argument(
        '--disable-out1',
        dest = 'out1',
        action = 'store_const',
        const = False,
        help = "Disable output 1")

    parser_config.add_argument(
        '--enable-out2',
        dest = 'out2',
        action = 'store_const',
        const = True,
        help = "Enable output 1")

    parser_config.add_argument(
        '--disable-out2',
        dest = 'out2',
        action = 'store_const',
        const = False,
        help = "Disable output 1")

    parser_config.add_argument(
        '--level',
        dest = 'level',
        metavar = 'CURRENT',
        type = int,
        choices = [ 8, 16, 24, 32 ],
        help = "Output drive level in mA")


def parser_add_pretend(p):
    p.add_argument(
        '-p', '--pretend',
        dest = 'pretend',
        action = 'store_true',
        help = "Don't modify device configuration")


def parser_add_show_status(p):
    p.add_argument(
        '-S', '--show-status',
        dest = 'show_status',
        action = 'store_true',
        help = "Show device status")


def parser_add_show_freq(p):
    p.add_argument(
        '-F', '--show-freq',
        dest = 'show_freq',
        action = 'store_true',
        help = "Show frequency plan")


def parser_add_ignore_freq_limits(p):
    p.add_argument(
        '--ignore-freq-limits',
        action = 'store_true',
        help = "Ignore frequency limits specified in the datasheet")


def parser_get_config(args):
    result = {}
    for attr in [ 'fin', 'n3', 'n2_hs', 'n2_ls', 'n1_hs', 'nc1_ls', 'nc2_ls', 'skew', 'bw', 'out1', 'out2' ]:
        result[attr] = getattr(args, attr, None)

    level = getattr(args, 'level', None)
    if level is not None:
        result['level'] = GPSDO.LEVEL_VALUE[level]

    return result


def main():

    #
    # Command Line Parser Definition
    #

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()


    parser_list = subparsers.add_parser(
        'list',
        aliases = [ 'l' ],
        help = "List devices")

    parser_list.set_defaults(func = command_list)


    parser_status = subparsers.add_parser(
        'status',
        aliases = [ 's' ],
        help = "Show lock status of a device")

    parser_add_device(parser_status)
    parser_status.set_defaults(func = command_status)


    parser_detail = subparsers.add_parser(
        'detail',
        aliases = [ 'd' ],
        help = "Show details of a device")

    parser_add_device(parser_detail)
    parser_detail.set_defaults(func = command_detail)


    parser_modify = subparsers.add_parser(
        'modify',
        aliases = [ 'm' ],
        help = "Change configuration of a single device")

    parser_add_device(parser_modify)
    parser_add_pretend(parser_modify)
    parser_add_show_status(parser_modify)
    parser_add_show_freq(parser_modify)
    parser_add_config(parser_modify)
    parser_add_ignore_freq_limits(parser_modify)
    parser_modify.set_defaults(func = command_modify)


    parser_backup = subparsers.add_parser(
        'backup',
        aliases = [ 'b' ],
        help = "Save configuration of a device")

    parser_add_device(parser_backup)
    parser_add_show_status(parser_backup)
    parser_add_show_freq(parser_backup)
    parser_add_ignore_freq_limits(parser_backup)
    parser_add_output(parser_backup, required = True)
    parser_backup.set_defaults(func = command_backup)


    parser_restore = subparsers.add_parser(
        'restore',
        aliases = [ 'r' ],
        help = "Restore configuration of a device")

    parser_add_device(parser_restore)
    parser_add_pretend(parser_restore)
    parser_add_show_freq(parser_restore)
    parser_add_ignore_freq_limits(parser_restore)
    parser_add_input(parser_restore, required = True)
    parser_restore.set_defaults(func = command_restore)


    parser_identify = subparsers.add_parser(
        'identify',
        aliases = [ 'i' ],
        help = "Identify output channel of a device")

    parser_add_device(parser_identify)

    parser_identify_output = parser_identify.add_mutually_exclusive_group(required = True)

    parser_identify_output.add_argument(
        '--off',
        dest = 'out',
        action = 'store_const',
        const = 0,
        help = "Disable Identification")

    parser_identify_output.add_argument(
        '--out1',
        dest = 'out',
        action = 'store_const',
        const = GPSDODevice.OUTPUT1,
        help = "Channel 1")

    parser_identify_output.add_argument(
        '--out2',
        dest = 'out',
        action = 'store_const',
        const = GPSDODevice.OUTPUT2,
        help = "Channel 2")

    parser_identify.set_defaults(func = command_identify)


    parser_analyze = subparsers.add_parser(
        'analyze',
        aliases = [ 'a' ],
        help = "Analyze a configuration")

    parser_add_device(parser_analyze)
    parser_add_multiinput(parser_analyze)
    parser_add_multioutput(parser_analyze)
    parser_add_config(parser_analyze)
    parser_add_ignore_freq_limits(parser_analyze)
    parser_analyze.set_defaults(func = command_analyze)


    parser_pll = subparsers.add_parser(
        'pll',
        aliases = [ 'p' ],
        help = "Show PLL diagram")

    parser_add_config(parser_pll)
    parser_pll.set_defaults(func = command_pll)



    #
    # Here we go.
    #

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
