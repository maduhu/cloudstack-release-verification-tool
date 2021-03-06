#!/usr/bin/env python

import sys
import getopt
import subprocess
import ast

class ReleaseVerifier:
    debug = False
    results = []
    end_instructions = "\n\n"
    OKGREEN = '\033[92m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def __init__(self, input_commands, version, commitsh, debug): 
        self.input_commands = input_commands
        self.version = version
        self.commitsh = commitsh
        self.debug = debug

    def do_replacements(self, toclean):
        toclean = toclean.replace("${commit-sh}", self.commitsh)
        toclean = toclean.replace("${version}", self.version)
        return toclean

    def make_call(self, action):
        output = ""

        if "instructions" in action:
            self.end_instructions = self.end_instructions + action["instructions"] + "\n"
            return

        action["command"] = self.do_replacements(action["command"])
        if "cwd" in action:
            action["cwd"] = self.do_replacements(action["cwd"])

        try:
            print self.HEADER + "RUNNING COMMAND: " + action["command"] + self.ENDC
            if "cwd" in action:
                output = subprocess.check_output("cd " + action["cwd"] + "; " + action["command"], stderr=subprocess.STDOUT, shell=True)
            else:
                output = subprocess.check_output(action["command"], stderr=subprocess.STDOUT, shell=True)
            action["result"] = "PASS"
            action["output"] = output
            self.results.append(action)
            if self.debug: 
                print "OUTPUT: " + output
        except:
            if action["must_work"]:
                action["result"] = "FAILED"
                action["output"] = output
                self.results.append(action)
                print "OUTPUT: " + output
                raise
            else:
                action["result"] = "WARNING"
                action["output"] = output
                self.results.append(action)
                print "OUTPUT: " + output

    def make_calls(self):
        continueActions = True
        for action in self.input_commands:
            try:
                if continueActions:
                    self.make_call(action)
                else:
                    action["result"] = "SKIPPED"
                    self.results.append(action)
            except:
                continueActions = False

    def print_results(self):
        print self.HEADER + "AUTOMATED TESTING RESULTS:" + self.ENDC
        for action in self.results:
            if action["result"]=="PASS":
                print "[" + self.OKGREEN + action["result"] + self.ENDC + "]\t\t" + action["command"]
            elif action["result"]=="WARNING":
                print "[" + self.WARNING + action["result"] + self.ENDC + "]\t" + action["command"]
            else:
                print "[" + self.FAIL + action["result"] + self.ENDC + "]\t" + action["command"]
        
        print self.HEADER + "POST AUTOMATION STEPS:" + self.end_instructions + self.ENDC

def print_help():
    print 'verify-release.py -i <inputfile> [-c commitsh] [-v version] [-d]'
    print ' -i : (required) configuration file with instructions to execute'
    print ' -c : A commit-sh which can be used as a replacement string within the configuration file'
    print ' -v : A version number which can be used as a replacement string within the configuration file'
    print ' -d : Debug output (all stdout and stderr is printed for each command'

def main(argv):
    inputfile = ''
    version = ''
    commitsh = ''
    debug = False
    try:
        opts, args = getopt.getopt(argv,"hi:c:v:d")
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-c"):
            commitsh = arg
        elif opt in ("-v"):
            version = arg
        elif opt in ("-d"):
            debug = True

    if inputfile == '':
        print_help()
        sys.exit(2)

    myfile = open(inputfile, "r")
    inputfiletext=myfile.read()

    input_commands = ast.literal_eval(inputfiletext)
    x = ReleaseVerifier(input_commands, version, commitsh, debug)
    x.make_calls()
    x.print_results()

if __name__ == "__main__":
    main(sys.argv[1:])
