#!/usr/bin/env python

"""Base class for building command line applications.

This class includes logging, exception handling, and argument processing.  It
also sets up an option parser for the user to simply extend.

Version 1.1
Version 1.0 was by ???

Copyright (c) 2009, John Wiegley.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

- Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

- Neither the name of New Artisans LLC nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys
import os
import optparse
import inspect
import logging

LEVELS = {'DEBUG':    logging.DEBUG,
          'INFO':     logging.INFO,
          'WARNING':  logging.WARNING,
          'ERROR':    logging.ERROR,
          'CRITICAL': logging.CRITICAL}

class CommandLineApp(object):
    "Base class for building command line applications."

    force_exit  = True           # If true, always ends run() with sys.exit()
    log_handler = None

    options = {
        'debug':    False,
        'verbose':  False,
        'logfile':  False,
        'loglevel': False
    }

    def __init__(self):
        "Initialize CommandLineApp."
        # Create the logger
        self.log = logging.getLogger(os.path.basename(sys.argv[0]))
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s: %(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        self.log.addHandler(ch)
        self.log_handler = ch

        # Setup the options parser
        op = self.option_parser = optparse.OptionParser()

        op.add_option('', '--debug',
                      action='store_true', dest='debug',
                      default=False, help='show debug messages and pass exceptions')
        op.add_option('-v', '--verbose',
                      action='store_true', dest='verbose',
                      default=False, help='show informational messages')
        op.add_option('-l', '--logfile', metavar='FILE',
                      type='string', action='store', dest='logfile',
                      default=False, help='append logging data to FILE')
        op.add_option('-L', '--loglevel', metavar='LEVEL',
                      type='string', action='store', dest='loglevel',
                      default=False, help='set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL')
        return

    def main(self, *args):
        """Main body of your application.

        This is the main portion of the app, and is run after all of the
        arguments are processed.  Override this method to implment the primary
        processing section of your application."""
        pass

    def handleInterrupt(self):
        """Called when the program is interrupted via Control-C or SIGINT.
        Returns exit code."""
        self.log.error('Canceled by user.')
        return 1

    def handleMainException(self):
        "Invoked when there is an error in the main() method."
        if not self.options.debug:
            self.log.exception('Caught exception')
        return 1

    ## INTERNALS (Subclasses should not need to override these methods)

    def run(self):
        """Entry point.

        Process options and execute callback functions as needed.  This method
        should not need to be overridden, if the main() method is defined."""
        # Process the options supported and given
        self.options, main_args = self.option_parser.parse_args()

        if self.options.logfile:
            fh = logging.handlers.RotatingFileHandler(self.options.logfile,
                                                      maxBytes = (1024 * 1024),
                                                      backupCount = 5)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
            fh.setFormatter(formatter)
            self.log.addHandler(fh)
            self.log.removeHandler(self.log_handler)
            self.log_handler = fh

        if self.options.loglevel:
            self.log.setLevel(LEVELS[self.options.loglevel])
        elif self.options.debug:
            self.log.setLevel(logging.DEBUG)
        elif self.options.verbose:
            self.log.setLevel(logging.INFO)
        
        exit_code = 0
        try:
            # We could just call main() and catch a TypeError, but that would
            # not let us differentiate between application errors and a case
            # where the user has not passed us enough arguments.  So, we check
            # the argument count ourself.
            argspec = inspect.getargspec(self.main)
            expected_arg_count = len(argspec[0]) - 1

            if len(main_args) >= expected_arg_count:
                exit_code = self.main(*main_args)
            else:
                self.log.error('Incorrect argument count (expected %d, got %d)' %
                               (expected_arg_count, len(main_args)))
                exit_code = 1

        except KeyboardInterrupt:
            exit_code = self.handleInterrupt()

        except SystemExit, msg:
            exit_code = msg.args[0]

        except Exception:
            exit_code = self.handleMainException()
            if self.options.debug:
                raise
            
        if self.force_exit:
            sys.exit(exit_code)
        return exit_code


if __name__ == "__main__":
    class sample(CommandLineApp):
        def main(self, *args):
            self.log.info("Saw args: %s" % (args,))
            x = 1 / 0           # logged as an exception

    sample().run()
