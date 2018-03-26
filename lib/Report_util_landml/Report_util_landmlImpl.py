# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import shutil
#import uuid
from Bio import SeqIO
from pprint import pprint, pformat
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from KBaseReport.KBaseReportClient import KBaseReport
from DataFileUtil.DataFileUtilClient import DataFileUtil

#END_HEADER


class Report_util_landml:
    '''
    Module Name:
    Report_util_landml

    Module Description:
    A KBase module: Report_util_landml
This sample module for creating text report for data objects
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/landml/Report_util_landml"
    GIT_COMMIT_HASH = "b4809d875cc70c4843964658397c1235a1e8e560"

    #BEGIN_CLASS_HEADER
    def create_report(self, token, ws, report_string, read_file_path):
        # type: (object, object, object, object) -> object
        output_html_files = list()
        output_zip_files = list()
        first_file = ""
        html_string = ""
        html_count = 0
        with open('/kb/module/data/index_start.txt', 'r') as start_file:
            html_string = start_file.read()

        # Make HTML folder
        html_folder = os.path.join(read_file_path, 'html')
        os.mkdir(html_folder)
        for file in os.listdir(read_file_path):
            label = ".".join(file.split(".")[1:])
            if (file.endswith(".zip")):
                desc = 'Zip file generated by the Report '
                output_zip_files.append({'path': os.path.join(read_file_path, file),
                                         'name': file,
                                         'label': label,
                                         'description': desc})
            if (file.endswith(".txt")):
                desc = 'Text file generated by the Report '
                output_zip_files.append({'path': os.path.join(read_file_path, file),
                                         'name': file,
                                         'label': label,
                                         'description': desc})
            if (file.endswith(".html")):
                # Move html into html folder
                shutil.move(os.path.join(read_file_path, file), os.path.join(html_folder, file))

                if (first_file == ""):
                    first_file = file

                html_string += "            <button data-button=\"page " + str(html_count) + \
                               "\" data-page=\"" + file + "\">Page " + str(html_count + 1) + "</button>\n"
                html_count += 1

        html_string += "        </div>    </div>    <div id=\"body\">\n"
        html_string += "        <iframe id=\"content\" "
        html_string += "style=\"width: 100%; border: none; \" src=\"" + first_file + "\"></iframe>\n    </div>"

        with open('/kb/module/data/index_end.txt', 'r') as end_file:
            html_string += end_file.read()

        with open(os.path.join(html_folder, "index.html"), 'w') as index_file:
            index_file.write(html_string)

        shock = self.dfu.file_to_shock({'file_path': html_folder,
                                        'make_handle': 0,
                                        'pack': 'zip'})
        desc = 'HTML files generated by the Report that contains report'
        output_html_files.append({'shock_id': shock['shock_id'],
                                  'name': 'index.html',
                                  'label': 'html files',
                                  'description': desc})

        report_params = {
            'message' : report_string,
#            'direct_html_link_index': 0,
            'file_links': output_zip_files,
            #'html_links': output_html_files,
            'html_links': [],
            'workspace_name': ws,
            'report_object_name': 'Report_util_report'
        }
        kbase_report_client = KBaseReport(self.callback_url, token=token)
        output = kbase_report_client.create_extended_report(report_params)
        return output

    # -----------------------------------------------------------------
    #    Create a Delimited Table version of the genes in a genome
    #
    def delimitedTable(self, genome, format, features):
        line = ""
        index = 0
        lineList = ["Feature ID", "Feature type", "Contig", "Location", "Strand", "Feature function", "Aliases"]
        if format == 'tab':
            line += "\t".join(lineList) + "\n"
        else:
            line += ",".join(lineList) + "\n"
        for feat in genome[features]:
            if 'function' not in feat:
                feat['function'] = 'unknown'

            aliases = ''
            if 'aliases' in feat:
                aliases = ', '.join(feat['aliases'])
            if 'type' not in feat:
                feat['type'] = features

            location = ''
            contig = ''
            strand = ''
            if len(feat['location']) > 0:
                locList = []
                # For those REALLY rare occassions when there is more than one location in Prokaryotes
                for loc in feat['location']:
                    contig = loc[0]
                    strand = loc[2]
                    if strand == '+':
                        start = loc[1]
                        stop = loc[1] + loc[3] - 1
                    else:
                        start = loc[1]
                        stop = loc[1] - loc[3] + 1
                    locList.append(str(start) + '..' + str(stop))

                location = ", ".join(locList)

            if format == 'tab':
                lineList = [feat['id'], feat['type'], contig, location, strand, feat['function'], aliases]
                line += "\t".join(lineList) + "\n"
            else:
                feat['function'] = '"' + feat['function'] + '"'
                aliases = '"' + aliases + '"'
                location = '"' + location + '"'
                lineList = [feat['id'], feat['type'], contig, location, strand, feat['function'], aliases]
                line += ",".join(lineList) + "\n"

            # print line
            index += 1

            #        To Test - un-comment the next two lines

        return line

    # -----------------------------------------------------------------
    #    Create a GFF3 version of the features in a genome
    #
    def gff3(self, genome, features):
        line = ""
        index = 0
        for feat in genome[features]:
            if 'function' not in feat:
                feat['function'] = 'unknown'

            aliases = ''
            if 'aliases' in feat:
                aliases = ':'.join(feat['aliases'])

            if 'type' not in feat:
                feat['type'] = features

            location = ''
            contig = ''
            strand = ''
            start = 0
            stop = 0
            if len(feat['location']) > 0:
                locList = []
                # For those REALLY rare occassions when there is more than one location in Prokaryotes
                for loc in feat['location']:
                    contig = loc[0]
                    strand = loc[2]
                    if strand == '+':
                        start = loc[1]
                        stop = loc[1] + loc[3] - 1
                        locList.append(str(start) + '..' + str(stop))
                    else:
                        start = loc[1]
                        stop = loc[1] - loc[3] + 1
                        locList.append(str(start) + '..' + str(stop))

                location = ", ".join(locList)

            ph = "."  # Placeholder for missing data
            attrib = "ID=" + feat['id']
            if feat['function'] != 'unknown':
                attrib += ";FUNCTION=" + feat['function']
            if aliases > '     ':
                attrib += ";ALIASES=" + aliases

            lineList = [contig, ph, feat['type'], str(start), str(stop), ph, strand, ph, attrib]
            line += "\t".join(lineList) + "\n"

            # print line
            index += 1

            #        To Test - un-comment the next two lines
            if index > 5 and testing.upper() == 'YES':
                break

        return line

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.dfu = DataFileUtil(self.callback_url)
        self.scratch = os.path.abspath(config['scratch'])
        #END_CONSTRUCTOR
        pass


    def assembly_metadata_report(self, ctx, params):
        """
        The actual function is declared using 'funcdef' to specify the name
        and input/return arguments to the function.  For all typical KBase
        Apps that run in the Narrative, your function should have the 
        'authentication required' modifier.
        :param params: instance of type "AssemblyMetadataReportParams" (A
           'typedef' can also be used to define compound or container
           objects, like lists, maps, and structures.  The standard KBase
           convention is to use structures, as shown here, to define the
           input and output of your function.  Here the input is a reference
           to the Assembly data object, a workspace to save output, and a
           length threshold for filtering. To define lists and maps, use a
           syntax similar to C++ templates to indicate the type contained in
           the list or map.  For example: list <string> list_of_strings;
           mapping <string, int> map_of_ints;) -> structure: parameter
           "assembly_input_ref" of type "assembly_ref", parameter
           "workspace_name" of String, parameter "showContigs" of type
           "boolean" (A boolean. 0 = false, other = true.)
        :returns: instance of type "ReportResults" (Here is the definition of
           the output of the function.  The output can be used by other SDK
           modules which call your code, or the output visualizations in the
           Narrative.  'report_name' and 'report_ref' are special output
           fields- if defined, the Narrative can automatically render your
           Report.) -> structure: parameter "report_name" of String,
           parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN assembly_metadata_report
        token = ctx['token']

        # Print statements to stdout/stderr are captured and available as the App log
        print('Starting Assembly MetaData Report Function. Params=')
        pprint(params)

        # Step 1 - Parse/examine the parameters and catch any errors
        # It is important to check that parameters exist and are defined, and that nice error
        # messages are returned to users.
        print('Validating parameters.')
        if 'workspace_name' not in params:
            raise ValueError('Parameter workspace_name is not set in input arguments')
        workspace_name = params['workspace_name']
        if 'assembly_input_ref' not in params:
            raise ValueError('Parameter assembly_input_ref is not set in input arguments')
        assembly_input_ref = params['assembly_input_ref']
        if 'showContigs' not in params:
            raise ValueError('Parameter showContigs is not set in input arguments')
        showContigs_orig = params['showContigs']
        showContigs = None
        try:
            showContigs = int(showContigs_orig)
        except ValueError:
            raise ValueError('Cannot parse integer from showContigs parameter (' + str(showContigs_orig) + ')')
        if showContigs < 0:
            raise ValueError('showContigs parameter cannot be negative (' + str(showContigs) + ')')
        if showContigs > 1:
            raise ValueError('showContigs parameter cannot be greater than one (' + str(showContigs) + ')')

        # Step 2 - Download the input data as a Fasta and
        # We can use the AssemblyUtils module to download a FASTA file from our Assembly data object.
        # The return object gives us the path to the file that was created.
        #print('Downloading Assembly data as a Fasta file.')
        #        assemblyUtil = AssemblyUtil(self.callback_url)
        #        fasta_file = assemblyUtil.get_assembly_as_fasta({'ref': assembly_input_ref})

        # Step 3 - Actually perform the filter operation, saving the good contigs to a new fasta file.
        # We can use BioPython to parse the Fasta file and build and save the output to a file.

        data_file_cli = DataFileUtil(self.callback_url)
#        assembly_metadata = data_file_cli.get_objects({'object_refs': ['assembly_input_ref']})['data'][0]['data']
        assembly = data_file_cli.get_objects({'object_refs': [assembly_input_ref]})
        assembly_metadata = assembly['data'][0]['data']

        string = "\nAssembly Metadata\n"
        list = ['assembly_id', 'dna_size', 'gc_content', 'num_contigs',
                'fasta_handle_ref', 'md5', 'type', 'taxon_ref']
        for item in list:
            if item in assembly_metadata:
                string += "\t{:20} = {}".format(item, assembly_metadata[item]) + "\n"

        if 'fasta_handle_info' in assembly_metadata and 'node_file_name' in assembly_metadata['fasta_handle_info']:
            string += "\tfilename             = " + assembly_metadata['fasta_handle_info']['node_file_name'] + "\n"
        string += "BASE counts\n"
        for base in assembly_metadata['base_counts']:
            #            string += "\t" + base + str(assembly_metadata['base_counts'][base]) + "\n"
            string += "\t{:5} = {}".format(base, str(assembly_metadata['base_counts'][base])) + "\n"
        string += "\nName\tLength\tGC content\tContigID\tDescription\n"
        if 'contigs' in assembly_metadata:
            myContig = assembly_metadata['contigs']
            for ctg in myContig:
                list = ['length', 'gc_content', 'contig_id', 'description']
                string += ctg
                #                describeDict(myContig[ctg])
                for item in list:
                    if item in myContig[ctg]:
                        string += "\t{}".format(myContig[ctg][item])
                    else:
                        string += "\t"
                string += "\n"

        report_path = os.path.join(self.scratch, 'assembly_metadata_report.txt')
        report_txt = open(report_path, "w")
        report_txt.write(string)
        report_txt.close()
        report_path = os.path.join(self.scratch, 'assembly_metadata_report.html')
        report_txt = open(report_path, "w")
        report_txt.write("<pre>" + string + "</pre>")
        report_txt.close()

        if showContigs:
            string += "This is the place where the list of contigs will go when that part gets created\n"

        print string


        reported_output = self.create_report(token, params['workspace_name'],
                                    string, self.scratch)

        output = {'report_name': reported_output['name'],
                           'report_ref': reported_output['ref']}

        print('returning: ' + pformat(output))
        print('Not returning: ' + pformat(reported_output))
        #END assembly_metadata_report

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method assembly_metadata_report return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def genome_report(self, ctx, params):
        """
        :param params: instance of type "GenomeReportParams" -> structure:
           parameter "genome_input_ref" of type "genome_ref", parameter
           "workspace_name" of String, parameter "report_format" of String
        :returns: instance of type "ReportResults" (Here is the definition of
           the output of the function.  The output can be used by other SDK
           modules which call your code, or the output visualizations in the
           Narrative.  'report_name' and 'report_ref' are special output
           fields- if defined, the Narrative can automatically render your
           Report.) -> structure: parameter "report_name" of String,
           parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN genome_report
        token = ctx['token']

        # Print statements to stdout/stderr are captured and available as the App log
        print('Starting Genome Report Function. Params=')
        pprint(params)

        # Step 1 - Parse/examine the parameters and catch any errors
        # It is important to check that parameters exist and are defined, and that nice error
        # messages are returned to users.
        print('Validating parameters.')
        if 'workspace_name' not in params:
            raise ValueError('Parameter workspace_name is not set in input arguments')
        workspace_name = params['workspace_name']
        if 'genome_input_ref' not in params:
            raise ValueError('Parameter genome_input_ref is not set in input arguments')
        genome_input_ref = params['genome_input_ref']


        # Step 2 - Get the input data
        # We can use the AssemblyUtils module to download a FASTA file from our Assembly data object.
        # The return object gives us the path to the file that was created.
        # print('Downloading Assembly data as a Fasta file.')
        #        assemblyUtil = AssemblyUtil(self.callback_url)
        #        fasta_file = assemblyUtil.get_assembly_as_fasta({'ref': assembly_input_ref})

        # Step 3 - Actually perform the filter operation, saving the good contigs to a new fasta file.
        # We can use BioPython to parse the Fasta file and build and save the output to a file.

        data_file_cli = DataFileUtil(self.callback_url)
        genome = data_file_cli.get_objects({'object_refs': [genome_input_ref]})
        genome_data = genome['data'][0]['data']

        report_format = params['report_format']
        string = ''
        if report_format == 'tab':
            string = self.delimitedTable(genome_data, 'tab', 'features')
            report_path = os.path.join(self.scratch, 'genome_report.txt')
        elif report_format == 'csv':
            string = self.delimitedTable(genome_data, 'csv', 'features')
            report_path = os.path.join(self.scratch, 'genome_report.csv')
        elif report_format == 'gff':
            string = self.gff3(genome_data, 'gff', 'features')
            report_path = os.path.join(self.scratch, 'genome_report.gff')
        elif report_format == 'fasta':
            string = self.delimitedTable(genome_data, 'csv', 'features')
            report_path = os.path.join(self.scratch, 'genome_report.faa')
        else:
            raise ValueError('Invalid report option.' + str(report_format))

        report_txt = open(report_path, "w")
        report_txt.write(string)
        report_txt.close()
        report_path = os.path.join(self.scratch, 'text_report.html')
        report_txt = open(report_path, "w")
        report_txt.write("<pre>" + string + "</pre>")
        report_txt.close()

#        print string

        reported_output = self.create_report(token, params['workspace_name'],
                                    string, self.scratch)

        output = {'report_name': reported_output['name'],
                  'report_ref': reported_output['ref']}

        print('returning: ' + pformat(output))
        print('Not returning: ' + pformat(reported_output))
        #END genome_report

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method genome_report return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
