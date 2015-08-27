import sublime, sublime_plugin
import json
import sys
import os
import re
##from pprint import pprint

def scan_file(filename, extension='.php'):
    '''
    Returns array of class, function, and member declarations for a given
    PHP source file.
    '''
    declarations = []

    name, ext = os.path.splitext(filename)
    if ext == extension:
        raw_tokens = get_all_tokens(filename=filename)
        declarations = convert_raw_tokens(raw_tokens)

        for i in range(0, len(declarations)):
            declarations[i]['path'] = filename

    return declarations

def scan_all_files(base_folder, extension='.json'):
    '''
    Returns array of class, function, and member declarations for all of the
    PHP source files on a given path.
    '''
    declarations = []
    for root, dirs, files in os.walk(base_folder):
        for name in files:
            filename, ext = os.path.splitext(name)
            if ext == extension:
                path = os.path.join(root, name)
                #sys.stderr.write(path + '\n')
                declarations.append(path)

    return declarations

def getFieldRecursive(fields, title, completions):
	for field in fields:
		if 'subfields' in field:
			completions = getFieldRecursive(field['subfields'], field['label'], completions)
		elif field['name']:
			suggestObj = {
				'label' : field['label'],
				'name' : field['name'],
				'parent' : title
			}
			completions.append(suggestObj)

	return completions;

def collectFrom(base_path):
	#find acf-json
	fields = []
	acf_json_path = os.path.join(base_path, 'acf-json') 
	jsons = scan_all_files(acf_json_path)
	for fieldgroup in jsons:
		with open(fieldgroup) as fieldgroup_content:
			j = json.load(fieldgroup_content)
			fieldgroup_content.close()
			fields = getFieldRecursive(j['fields'], j['title'], fields)
			
	return fields

def getAcfPath(view):
	project_data = view.window().project_data()
	#always the first folder
	base_path = project_data['folders'][0]['path']
	return base_path

def get_autocomplete_list(self, word, collected):
	autocomplete_list = []
	for suggest in collected:
		isFound = re.findall(word, suggest['name'])
		if word in suggest['name']:
			autocomplete_list.append((suggest['name'] + '\t' + 'acf|' + suggest['parent'],suggest['name']))

	return autocomplete_list

class EventListener(sublime_plugin.EventListener):
	def on_query_completions(self, view, prefix, locations):
		# get acf
		base_path = getAcfPath(view)
		collected = collectFrom(base_path)

		lang = view.settings().get('syntax')
		#pprint(view.settings().get('syntax'))
		if lang != 'Packages/PHP/PHP.tmLanguage':
			return

		# get region
		region = view.sel()[0];
		word = view.word(region);
		line = view.line(region)

		# acf field functions
		regexes = [
		    "get_field",
		    "get_sub_field",
		    "has_sub_field"
		    ]

		# Make a regex that matches if any of our regexes match.
		combined = "(" + ")|(".join(regexes) + ")"

		has_get_field = re.findall(combined, view.substr(line))

		if len(has_get_field) > 0:
			completions = get_autocomplete_list(self, view.substr(word), collected)
			#pprint(completions)
			return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)

		#pprint(has_get_field)

class AcfCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		base_path = getAcfPath(self.view)
		collectFrom(base_path)

