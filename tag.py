#!/usr/bin/env python
#
# TERNIP: Temporal Expression Recognition and Normalisation in Python
#

import optparse
import sys

import ternip.formats
import ternip.rule_engine

option_parser = optparse.OptionParser(usage='%prog [options] FILENAME', version=""" $Id$, """)

# The options we take
io_group = optparse.OptionGroup(option_parser, "Format Options", "Options for dealing with the type of input and output files")
io_group.add_option('-t', '--doctype', dest='doc_type', type='choice', choices=['timex2','timex3','tern','timeml'], help='The format of the document and resulting tags. Supported values: timex2 - XML document resulting in TIMEX2 tags; timex3 - XML document resulting in TIMEX3 tags; tern - a document from the TERN corpus; timeml - a document annotated with TimeML')
io_group.add_option('-s', '--strip-timexes', dest='strip_timexes', default=False, action="store_true", help='If set, any timexes in the document are stripped, and then tagging starts afresh. If you don\'t enable this, feed in a document which already has TIMEXes in it and are doing recognition, you may end up with duplicate TIMEX tags.')
io_group.add_option('-b', '--body-tag', dest='body_tag', default=None, type='string', help='If set, this tag only the contents of this tag is tagged.')
io_group.add_option('--s-tag', dest='has_S', metavar='S_tag', default=None, type='string', help='If set, this tag name is used to denote sentence boundaries. If unset, NLTK is used to tokenise.')
io_group.add_option('--lex-tag', dest='has_LEX', metavar='LEX_tag', default=None, type='string', help='If set, this tag name is used to denote token boundaries. If unset, NLTK is used to tokenise.')
io_group.add_option('--pos-attr', dest='pos_attr', metavar='POS_attr', default=None, type='string', help='If set, then this attribute on the tag set by --lex-tag is used to denote the POS tag of that token. If unset, NLTK is used for POS tagging.')
option_parser.add_option_group(io_group)

recog_group = optparse.OptionGroup(option_parser, "Recognition Rules")
recog_group.add_option('-r', '--recognition-engine', dest='recognition_engine', type='choice', default='default', choices=['none','rule','default'], help='Selects the engine to use for TIMEX recognition. Defaults to the currently recommended TERNIP engine. Other options are \'rule\' for the rule engine and \'none\' to disable recognition (e.g., if the document already has TIMEXs annotated, but just needs normalising)')
recog_group.add_option('--recognition-rules', dest='recognition_rules', type='string', default=None, help='Path to recognition rules. Defaults to ./rules/recognition/')
option_parser.add_option_group(recog_group)

norm_group = optparse.OptionGroup(option_parser, "Normalisation Rules")
norm_group.add_option('-n', '--normalisation-engine', dest='normalisation_engine', type='choice', default='default', choices=['none','rule','default'], help='Selects the engine to use for TIMEX recognition. Defaults to the currently recommended TERNIP engine. Other options are \'rule\' for the rule engine and \'none\' to disable recognition (e.g., to just do recognition)')
norm_group.add_option('--normalisation-rules', dest='normalisation_rules', type='string', default=None, help='Path to normalisation rules. Defaults to ./rules/normalisation/')
option_parser.add_option('-c', '--dct', dest='dct', default=None, type='string', help='The document creation time used as the basis for normalisation. If not set, it will attempt to be extracted from the document.')
option_parser.add_option_group(norm_group)

(options, args) = option_parser.parse_args()

if len(args) != 1:
    # Only parse one file at a time
    option_parser.print_help()
    print >>sys.stderr, "ERROR: multiple input files specified" if len(args) > 1 else "ERROR: no input files specified"
    sys.exit(1)

input_file = args[0]

# Create document for input file
if options.doc_type == 'timex2':
    with open(input_file) as fd:
        doc = ternip.formats.timex2(fd.read(), options.body_tag, options.has_S, options.has_LEX, options.pos_attr)
elif options.doc_type == 'timex3':
    with open(input_file) as fd:
        doc = ternip.formats.timex3(fd.read(), options.body_tag, options.has_S, options.has_LEX, options.pos_attr)
elif options.doc_type == 'timeml':
    if options.body_tag != None or options.has_S != None or options.has_LEX != None or options.pos_attr != None:
        option_parser.print_help()
        print >>sys.stderr, "ERROR: incompatible options with document type"
        sys.exit(1)
    with open(input_file) as fd:
        doc = ternip.formats.timeml(fd.read())
elif options.doc_type == 'tern':
    if options.body_tag != None or options.has_S != None or options.has_LEX != None or options.pos_attr != None:
        option_parser.print_help()
        print  >>sys.stderr,"ERROR: incompatible options with document type"
        sys.exit(1)
    with open(input_file) as fd:
        doc = ternip.formats.tern(fd.read())
else:
    option_parser.print_help()
    print >>sys.stderr, "ERROR: invalid document type specified"
    sys.exit(1)

# Strip TIMEXes from the input document if need be
if options.strip_timexes:
    doc.strip_timexes()

# Get internal representation
sents = doc.get_sents()

# Load correct recognition engine
if options.recognition_engine == 'none':
    recogniser = None
elif options.recognition_engine == 'default':
    recogniser = ternip.recogniser()
elif options.recognition_engine == 'rule':
    recogniser = ternip.rule_engine.recognition_rule_engine()
else:
    option_parser.print_help()
    print >>sys.stderr, "ERROR: invalid recognition engine specified"
    sys.exit(1)

# Load rules
if options.recognition_rules != None and options.recognition_engine == 'rule':
    recogniser.load_rules(options.recognition_rules)
elif options.recognition_rules == None and options.recognition_engine == 'rule':
    print >>sys.stderr, "WARNING: no recognition rules set to load"
elif options.recognition_rules != None and options.recognition_engine != 'rule':
    print >>sys.stderr, "WARNING: recognition rule path only valid when rule engine specified"

# Do recognition
if recogniser is not None:
    if options.dct == None:
        dct_sents = doc.get_dct_sents()
        dct_sents = recogniser.tag(dct_sents)
    sents = recogniser.tag(sents)

# Load correct recognition engine
if options.normalisation_engine == 'none':
    normaliser = None
elif options.normalisation_engine == 'default':
    normaliser = ternip.normaliser()
elif options.normalisation_engine == 'rule':
    normaliser = ternip.rule_engine.normalisation_rule_engine()
    normaliser.load_rules(options.normalisation_rules)
else:
    option_parser.print_help()
    print >>sys.stderr, "ERROR: invalid normalisation engine specified"
    sys.exit(1)

# Load rules
if options.normalisation_rules != None and options.normalisation_engine == 'rule':
    normaliser.load_rules(options.normalisation_rules)
elif options.normalisation_rules == None and options.normalisation_engine == 'rule':
    print >>sys.stderr, "WARNING: no normsalisation rules set to load"
elif options.normalisation_rules != None and options.normalisation_engine != 'rule':
    print >>sys.stderr, "WARNING: normalisation rule path only valid when rule engine specified"

# Do normalisation
if normaliser is not None:
    dct = ''
    if options.dct == None:
        # Get DCT from normaliser
        normaliser.annotate(dct_sents, 'XXXXXXXX')
        doc.reconcile_dct(dct_sents)
        # Get dct value
        for sent in dct_sents:
            for (tok, pos, ts) in sent:
                for t in ts:
                    if dct == '' and t.value != None:
                        dct = t.value
    else:
        dct = options.dct
    
    # Now check if we got a dct
    if dct == '':
        print >>sys.stderr, "WARNING: Could not determine document creation time, use -c to override"
    normaliser.annotate(sents, dct)
    
# Now apply the changes back to the internal document
doc.reconcile(sents)

# Now output the final document
if options.doc_type == 'tern':
    print str(doc)[22:]
else:
    print str(doc)