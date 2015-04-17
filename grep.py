#!/usr/local/bin/python
# grep.py file
# implementation of GNU grep
# (c) G. Cordina 2014
import sys
import re
import os
import glob
import fnmatch
import stat
import optparse
EXIT_MATCH=0
EXIT_NOMATCH=1
EXIT_TROUBLE=2

 
class Grep:
    def trace(self, msg):
         if self.debug:
            self.output ('*' + msg)
    def trace2(self, msg):
        if self.debug >= 2:
            self.trace(msg)
           
    def match_regexp(self, line, pattern):
        flags = 0
        if self.opt.ignore:
            flags += re.I
       
        if self.opt.line_regexp:
            if pattern[0] != '^':
                pattern = '^' + pattern
            if pattern[-1] != '$':
                pattern = pattern + '$'
               
        match = re.search(pattern, line, flags)
        self.trace2('match=' + str(match))
        match_p = match is not None
        if self.opt.match_direction == match_p:
            if not match_p:
                return line
            else:
                self.trace2('match')
                if self.opt.only_matching:
                    return line[match.start():match.end() + 1]
                else:
                    return line
        else:
            self.trace2('not match')
            return None
       
    def match_fixed(self, line, pattern):
        #TODO: implement option -w, --word-regexp (low priority)
        flags = 0
        if self.opt.ignore:
            return match_regexp(line, pattern)
        else:
            if self.opt.line_regexp:
                match_p = line[:-1] == pattern
            else:
                match_p = line.find(pattern) >= 0
            if self.opt.match_direction == match_p:
                if not match_p:
                    return line
                else:
                    self.trace2('match')
                    if self.opt.only_matching:
                        return line[match.start():match.end() + 1]
                    else:
                        return line
            else:
                self.trace2('not match')
                return None
       
    def __init__(self, pattern=None, files=[], ignore=False, line_number=False,
                  count=False, recursive=False, match_direction=True,
                  with_filename=False, after_ctx=0, before_ctx=0,
                  no_filename=False):
        self.lastmatch_p = False
        self.return_on_first_match_p = False
 
        class OptClass:
            pass
        self.opt = OptClass()
        self.files = files
        self.pattern=pattern
        self.opt.ignore=ignore
        self.opt.line_number=line_number
        self.opt.count=count
        self.opt.recursive=recursive
        self.opt.match_direction=match_direction
        self.opt.with_filename=with_filename
        self.opt.after_ctx=after_ctx
        self.opt.before_ctx=before_ctx
        self.opt.no_filename=no_filename
 
        try:
            self.debug = int(os.environ['PYDB'])
        except:
            if 'PYDB' in os.environ and os.environ['PYDB'] != '0':
                self.debug = 1
            else:
                self.debug = 0
               
    def init_options(self):
        """Initialize command line options into self.opt object """
        self.usage = "usage: %prog [options] PATTERN [FILE...]"
        parser = optparse.OptionParser(usage=self.usage)
        parser.add_option('--debug', action='store_true', default=False)
        parser.add_option("-i", '--ignore', action='store_true', default=False)
        parser.add_option("-n", '--line-number', action='store_true', default=False)
        parser.add_option("-c", '--count', action='store_true', default=False)
        parser.add_option("-r", '--recursive', action='store_true', default=False)
        parser.add_option("-q", '--quiet', action='store_true', default=False)
        parser.add_option("-s", '--no-messages', action='store_true', default=False)
        parser.add_option("-o", '--only-matching', action='store_true', default=False)
        parser.add_option("-e", '--regexp')
        parser.add_option("-E", '--extended-regexp', action='store_true', default=False, help='Does nothing in GNU grep')
        parser.add_option("-G", '--basic-regexp', action='store_true', default=False, help='Does nothing in GNU grep')
        parser.add_option("-F", '--fixed-strings', action='store_true', default=False, help='Interpret the pattern as a list of fixed strings')
        parser.add_option("-v", '--invert-match', dest='match_direction', action='store_false', default=True)
        parser.add_option("-l", '--files-with-matches', action='store_true', default=False)
        parser.add_option("-L", '--files-without-matches', action='store_true', default=False)
        parser.add_option("-H", '--with-filename', action='store_true', default=False)
        parser.add_option("-A", '--after-ctx', default='0', help='Print NUM  lines      of  trailing  ctx  after  matching   lines.')
        parser.add_option("-B", '--before-ctx', default='0', help='Print  NUM  lines  of  leading  ctx  before  matching lines.')
        parser.add_option("-C", '--ctx', default='0', help='Print  NUM  lines of leading and trailing ctx  before  matching lines.')
        parser.add_option("-x", '--line-regexp', action='store_true', default=False)
        parser.add_option('--no-filename', action='store_true', default=False)
        parser.add_option('--group-separator', default="--")
        parser.add_option('--exclude', default=None)
        parser.add_option('--exclude-dir', default=None)
        parser.add_option('--include', default=None)
        parser.add_option('--no-group-separator', action='store_true', default=False)
        (options, args) = parser.parse_args()
        self.opt = options
        self.args = args
       
        try:
            self.opt.after_ctx = int(self.opt.after_ctx)
            self.opt.before_ctx = int(self.opt.before_ctx)
            self.opt.ctx = int(self.opt.ctx)
            if self.opt.ctx > 0:
                self.opt.after_ctx = self.opt.ctx
                self.opt.before_ctx = self.opt.ctx
        except Exception as e:
            self.output(self.usage)
            return False
 
        # cmd-line options take precedence over env-variable options
        if self.opt.debug:
            self.debug = self.opt.debug
           
        self.trace('options=' + str(self.opt))
 
        # Determine the pattern and files arguments
        if self.opt.regexp == None:
            # Not expressed as --regexp, then must be positional
            self.trace('self.opt.regexp == None')
            if self.args == None or len(self.args) == 0:
                self.output(self.usage)
                # Exit 2 for error
                sys.exit(EXIT_TROUBLE)
            elif len(self.args) == 1:
                # pattern is 1st positional param
                self.pattern = self.args[0]
                self.files = None
            else:
                self.pattern = args[0]
                self.files = args[1:]          
        else:
            # expressed as --regexp, then files is the only positional argument
            self.pattern = self.opt.regexp
            if len(self.args) == 0:
                self.files = None
            else:
                self.files = args
        self.trace('pattern=' + self.pattern + ' - files=' + str(self.files))
        return True
               
    def format_line(self, line, linenumber, filename, ctx_p):
        '''Formats the line with prefixes depending on options'''
        sep = '-' if ctx_p else ':'
        if self.opt.with_filename and not self.opt.no_filename and filename is not None:
            prefix_fn = filename + sep
        else:
            prefix_fn = ''
 
        if self.opt.line_number:
            prefix_ln = str(linenumber) + sep
        else:
            prefix_ln = ''
           
        return prefix_fn + prefix_ln + line[:-1]
 
    def output_line(self, line, linenumber, filename, ctx_p):
        '''Outputs the line with formatting. Doesn't output in case of some options'''
        if not self.opt.count and not self.opt.files_with_matches and \
          not self.opt.files_without_matches and not self.opt.quiet:
            if linenumber > self.last_line_printed:
                self.output(self.format_line(line, linenumber, filename, ctx_p))
                self.last_line_printed = linenumber
        
    def output_group_sep(self):
        '''Outputs group separator charactor according to options'''
        if not self.opt.count and not self.opt.files_with_matches and \
          not self.opt.files_without_matches and not self.opt.quiet and \
          not self.opt.no_group_separator:
            self.output(self.opt.group_separator)
       
    def output_message(self, msg):
        '''Outputs message starting with 'grep:' '''
        if not self.opt.no_messages:
            self.output('grep: ' + msg)
       
    def output(self, msg):
        '''The standard grep output'''
        print (msg)
 
    def iter_lines(self, lines, filename=None):
        # lastmatch_p is for printing "--" before the first new match only if
        self.trace('iter_lines:' + str(len(lines)))
        linenumber = result = 0
        after_ctx_dist = -1
        before_ctx_buf = []
        self.last_line_printed = 0 # this is maintained by output_line()
       
        for line in lines:
            linenumber += 1
            if not self.opt.fixed_strings:
                matched = self.match_regexp(line, self.pattern)
            else:
                matched = self.match_fixed(line, self.pattern)
            if matched is not None:
                # line matches: print it with correct prefix, unless counting only, and before ctx lines
                result += 1
                if self.return_on_first_match_p:
                    return result
 
                # add separator from last matching group of previous file
                if self.lastmatch_p and (self.opt.after_ctx>0 or self.opt.before_ctx>0):
                    self.output_group_sep()
                    self.lastmatch_p = False
                # need a separator? checking distance of before and after ctxs
                elif after_ctx_dist != -1:
                    if self.opt.before_ctx > 0 and len(before_ctx_buf) > 0:
                        b4cln = linenumber - len(before_ctx_buf)
                        if b4cln > self.last_line_printed + 1:
                            self.output_group_sep()
                            self.trace('group sep printed for before ctx, b4cln='+str(b4cln))
                    elif self.opt.after_ctx > 0 and after_ctx_dist > self.opt.after_ctx:
                        self.output_group_sep()
                        self.trace('group sep printed for after ctx')
 
                if self.opt.before_ctx > 0:
                    # if we have a before ctx backlog, print it
                    for i, before_line in enumerate(before_ctx_buf):
                        self.output_line(before_line, linenumber - len(before_ctx_buf) + i, filename, ctx_p=True)
                # finally print the matched line
                self.output_line(matched, linenumber, filename, False)
                # reset counter and buffer
                after_ctx_dist = 0
                before_ctx_buf = []
            else:
                # print after ctx lines
                if self.opt.after_ctx > 0 and after_ctx_dist > -1:
                    # increment the distance to the last match line, print the line if within distance
                    after_ctx_dist += 1
                    if after_ctx_dist < self.opt.after_ctx + 1:
                        self.output_line(line, linenumber, filename, True)
                # bufferize before ctx lines
                if self.opt.before_ctx > 0:
                    if before_ctx_buf and len(before_ctx_buf) >= self.opt.before_ctx:
                        before_ctx_buf.pop(0)
                    before_ctx_buf.append(line)
        return result
 
    def list_files(self, files, currentdir=None):
        result = set()
        if not self.opt.recursive:
            # expand the wildcards on every arg, keep only the files
            for name in files:
                found_p = False
                for f in glob.glob(name):
                    if self.opt.exclude is not None and fnmatch.fnmatch(f, self.opt.exclude):
                        self.trace('Exclude %s based on pattern %s' % (f, self.opt.exclude))
                        continue
                    elif self.opt.include is not None and not fnmatch.fnmatch(f, self.opt.include):
                        self.trace('Exclude %s based on "include" pattern %s' % (f, self.opt.include))
                        continue                       
                    elif stat.S_ISREG(os.stat(f).st_mode):
                        result.add(f)
                        found_p = True
                if not found_p:
                    self.output_message('%s: No such file or directory' % name)
           
        else:
            if currentdir is None:
                # first iteration, files contains the grep FILE argument,
                # we use glob to expand the wildcards on them
                for name in files:
                    lst = glob.glob(name)
                    if len(lst) == 0:
                        self.output_message('%s: No such file or directory' % name)
                    else:
                        for f in lst:
                            if f in ('.', '..'):
                                continue
                            elif stat.S_ISDIR(os.stat(f).st_mode):
                                # print f + ' is directory, exploring '
                                if self.opt.exclude_dir is not None and fnmatch.fnmatch(f, self.opt.exclude_dir):
                                    self.trace('Exclude %s based on pattern %s' % (f, self.opt.exclude_dir))
                                    continue
                                result.update(self.list_files(os.listdir(f), f + '/'))
                            else:
                                # Regular file
                                if self.opt.exclude is not None and fnmatch.fnmatch(f, self.opt.exclude):
                                    self.trace('Exclude %s based on pattern %s' % (f, self.opt.exclude))
                                    continue
                                elif self.opt.include is not None and not fnmatch.fnmatch(f, self.opt.include):
                                    self.trace('Exclude %s based on "include" pattern %s' % (f, self.opt.include))
                                    continue                       
                                result.add(f)
            else:
                # second iteration, we add every file reiterate on every subdir
                self.trace('currentdir=' + currentdir)
                for f in files:
                    if self.opt.exclude is not None and fnmatch.fnmatch(f, self.opt.exclude):
                        self.trace('Exclude %s based on pattern %s' % (f, self.opt.exclude))
                        continue
                    elif self.opt.include is not None and not fnmatch.fnmatch(f, self.opt.include):
                        self.trace('Exclude %s based on "include" pattern %s' % (f, self.opt.include))
                        continue                       
                    elif f in ('.', '..'):
                        continue
                    elif stat.S_ISDIR(os.stat(currentdir + f).st_mode):
                        self.trace(currentdir + f + ' is directory, exploring ')
                        result.update(self.list_files(os.listdir(currentdir + f), currentdir + f + '/'))
                    else:
                        result.add(currentdir + f)
                   
        return result
       
   
    def process_file(self, filename):
        '''Runs the grep process on one file'''
        self.trace('process_file:' + str(filename))
        if filename is None:
            f = sys.stdin
        else:
            f = open(filename)
        count = self.iter_lines(f.readlines(), filename)
        # Setting lastmatch_p if the previous file had matches, we want '--' before the next match, \
        # only if there is one, and only if we are printing ctxs
        self.lastmatch_p = (count > 0)
        if self.opt.count:
            # only print the count, per file name
            if self.opt.with_filename and not self.opt.no_filename:
                self.output(filename + ':' + str(count))
            else:
                self.output(str(count))
        elif self.opt.files_with_matches and count > 0:
            self.output(filename)
        elif self.opt.files_without_matches and count == 0:
            self.output(filename)
        elif self.opt.quiet and count > 0:
            # Exit code is 1 if no match is found
            sys.exit(EXIT_NOMATCH)
 
    def run(self):
        """"Process the grep based on options.
        
        Prints out the results"""
        if self.opt.files_with_matches or \
          self.opt.files_without_matches or self.opt.quiet:
            self.return_on_first_match_p = True
           
        if self.files == None:
            # stdin will be used as input
            self.trace('no FILE param')
            self.process_file(None)
        else:
            files = self.list_files(self.files)
            self.trace('list files=' + str(files))
            if len(files) > 1:
                self.opt.with_filename = True
            for f in files:           
                self.process_file(f)
        return True
 
if __name__ == '__main__':
    g = Grep()
    if not g.init_options() or not g.run():
        sys.exit(EXIT_TROUBLE)
        