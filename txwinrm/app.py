##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import sys
import logging
from getpass import getpass
from argparse import ArgumentParser
from ConfigParser import RawConfigParser
from twisted.internet import reactor, defer

logging.basicConfig()
log = logging.getLogger('zen.winrm')
_exit_status = 0


class Config(object):
    pass


def _parse_config_file(filename):
    parser = RawConfigParser(allow_no_value=True)
    parser.read(filename)
    creds = {}
    index = dict(authentication=0, hostname=1, password=2)
    for key, value in parser.items('credentials'):
        k1, k2 = key.split('.')
        if k1 not in creds:
            creds[k1] = [None, None, None]
        creds[k1][index[k2]] = value
    config = Config()
    config.hosts = {}
    for hostname, cred_key in parser.items('targets'):
        config.hosts[hostname] = (creds[cred_key])
    config.wqls = parser.options('wqls')
    return config


def _adapt_args_to_config(args):
    config = Config()
    config.hosts = \
        {args.remote: (args.authentication, args.username, args.password)}
    config.wqls = [args.filter]
    return config


def _parse_args(add_args_func):
    parser = ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--config", "-c")
    parser.add_argument("--remote", "-r")
    parser.add_argument("--authentication", "-a", default='basic',
                        choices=['basic', 'kerberos'])
    parser.add_argument("--username", "-u")
    add_args_func(parser)
    return parser.parse_args()


def main(tx_main_func, add_args_func, check_args_func=lambda x: True):
    args = _parse_args(add_args_func)
    if args.debug:
        log.setLevel(level=logging.DEBUG)
        defer.setDebugging(True)
    if args.config:
        config = _parse_config_file(args.config)
    elif args.remote and args.username and check_args_func(args):
        args.password = getpass()
        config = _adapt_args_to_config(args)
    else:
        print >>sys.stderr, "ERROR: You must specify a config file with -c " \
                            "or specify remote, username, and other " \
                            "required options"
        sys.exit(1)
    reactor.callWhenRunning(tx_main_func, config)
    reactor.run()
    sys.exit(_exit_status)


def stop_reactor(*args, **kwargs):
    if reactor.running:
        reactor.stop()