import collections, sys, re
from anytree import Node, RenderTree, PreOrderIter
	
def loadFile(name):
	with open( name ) as f:
		read_data = f.read()
		return read_data

def match_regexes(content, name, imported, type_matches_list, id_matches_list):
	new_types_list = [] 
	print ("Parsing {}. {} external files imported so far.".format(name, len(imported)))

	RE_string_obj_type = re.compile(r'(.*)(?:[ \t])(OBJECT-TYPE)(?:(?:\n)(?:.*)(SYNTAX)(.*))?(?:(?:\n)(?:.*)(ACCESS)(.*))?(?:\n(?:.*)(STATUS)(.*))?(?:(?:\n(?:.*)(DESCRIPTION)(?:.*))?\n(?:.*)"([A-Za-z0-9\t\n .,:;!?*"\'^`()/+-]*)")?(?:\n(?:.*)(INDEX)(.*))?\n(?:.*)::= {[ ]?(.*)[ ](\d+)[ ]?}')
	RE_string_obj_id = re.compile(r'(.*(?:[\n]?).*)OBJECT IDENTIFIER ::= {[ ]?([a-zA-Z0-9-]*)(?:.*?)[ ]?([0-9]*)[ ]?}')
	RE_import_whole = re.compile(r'IMPORTS([\s\S]*?);')
	RE_import_details = re.compile(r'((?:.|\n)*?)FROM[ ]+([A-Za-z0-9-]*)(?: -- )?(.*)?')
	
	type_matches = RE_string_obj_type.findall(content)
	for match in type_matches:
		object_type = match[0].strip() #grupy w RE są indeksowane od 1!
		syntax = match[3].strip()
		access = match[5].strip()
		status = match[7].strip()
		dscrpt = match[9].strip()
		index = match[11].strip() #None jeśli pusty
		entry = match[12].strip()
		num = match[13].strip()
		#print ("OBJECT-TYPE: {}\nSYNTAX: {}\nACCESS: {}\nSTATUS: {}\nDESCRIPTION: {}\nINDEX: {}\nENTRY: {}\nNUMBER: {}\n\n".format(object_type,syntax,access,status,dscrpt,index,entry,num))
		if (object_type,syntax,access,status,dscrpt,index,entry,num) not in type_matches_list:
			type_matches_list.append((object_type,syntax,access,status,dscrpt,index,entry,num))
		
	id_matches = RE_string_obj_id.findall(content)
	for match in id_matches:
		id = match[0].strip()
		'''raw_value = match[1].strip()
		value = raw_value.rsplit(" ")
		parent = value[0]
		number = value[1]'''
		parent = match[1].strip()
		number = match[2].strip()
		print ("OBJECT-IDENTIFIER: {}\nPARENT: {}\nNUMBER: {}\n\n".format(id, parent, number))
		if (id, parent, number) not in id_matches_list:
			id_matches_list.append((id, parent, number))
		
	imports = RE_import_whole.findall(content)
	try:
		one_import = RE_import_details.findall(imports[0])
		for match in one_import:
			raw_list = match[0].strip()
			raw_list = raw_list.replace('\n', '')
			raw_list = raw_list.replace(' ','')
			list = raw_list.rsplit(",")
			source = match[1].strip()
			RFC = match[2].strip()
			print ("items to import: {}\nsource: {}\nRFC: {}".format(list, source, RFC))
			
			load_name = 'mibs/{}'.format(source)
			try:
				load = loadFile(load_name)
				if load not in imported:
					print ("Importing {}...\n".format(source))
					imported.append(load)
					match_regexes(load, load_name, imported, type_matches_list, id_matches_list)
			except FileNotFoundError:
				print ("\tWARNING - file {} not found. Skipping.".format(load_name))
		
	except IndexError:
		print ("No imports section in file {}.".format(name))
	
	return type_matches_list, id_matches_list

def clean_lists(types, ids):
	
	names_list = [x[0] for x in ids]
	for n in names_list:
		if n[0] == '-' and n[1] == '-':
			names_list.remove(n)
			
	#print ("names list: {}\n".format(names_list))
	try:
		names_list.remove("nullSpecific")
	except:
		pass
	
	for i in ids:
		if i[0] not in names_list:
			ids.remove(i)
	
	#RFC1213 SPECIFIC
	try:
		ids.remove(('-- cmot', 'mib-2', '9'))
	except:
		pass
		
	
	return types, ids
	
def build_ids_tree(lista, llista):
	nodes = []
	triads = []
	lista.insert(0, ('iso', None, 1))
	lista.insert(1, ('org', 'iso', 3))
	lista.insert(2, ('dod', 'org', 6))
	lista.insert(3, ('internet', 'dod', 1))
		
	nodes.append(Node(("iso", 1), parent = None))
	nodes.append(Node(("org", 3), parent = None))
	nodes.append(Node(("dod", 6), parent = None))
	nodes.append(Node(("internet", 1), parent = None))
	

	#internet duplicates popping 
	for i, item in enumerate(lista):
		if item[0] == 'internet' and item[1] != 'dod':
			lista.pop(i)
	
	for item in lista:
		if item[0] == 'iso' or item[0] == 'org' or item[0] == 'dod' or item[0] == 'internet':
			continue
		nodes.append(Node((item[0], item[2]), parent = None))
	
	nodes[1].parent = nodes[0]
	nodes[2].parent = nodes[1]
	nodes[3].parent = nodes[2]	
	
	for i,l in enumerate(lista):
		triads.append((i,l[0],l[1]))
	
	'''print("id, nazwa, rodzic")
	for t in triads:
		print("{}, {}, {}".format(t[0], t[1], t[2]))'''
		
	for n in nodes:
		if n.name[0] == 'iso' or n.name[0] == 'org' or n.name[0] == 'dod' or n.name[0] == 'internet':
			continue	
		for l in lista:
			if n.name[0] == l[0]: 
				for t in triads:
					if t[1] == l[1]:
						if t[1] == 'internet' and t[2] != 'dod':
							continue
						index = t[0]
						#print("{}'s parent should be {} with index {}; actually is {}".format(n.name[0], l[1], index, nodes[index]))
						n.parent = nodes[index]
						#print (n.name[0] + "'s parent: " + str(n.parent) + "\n")
	
	for pre, _, node in RenderTree(nodes[0]):
		print("%s%s" % (pre, node.name[0]))

		
def main():
	#t = Tree()
	imported = []
	type_list = []
	id_list = []
	arg_file_content = loadFile(sys.argv[1])
	print("\n***\nPerforming task 1 - parsing files.\n***\n")
	type_list, id_list = match_regexes(arg_file_content, sys.argv[1], imported, [], []) #zawartość pliku, nazwa pliku, lista importów
	type_list, id_list = clean_lists(type_list, id_list)
	print("\n***\nTask 1 completed successfully.\n***\n")
	print("\n***\nPerforming task 2 - building binary tree.\n***\n")
	build_ids_tree(id_list, type_list)
	print("\n***\nTask 2 completed successfully.\n***\n")
	
	#print (id_list)
		
main()

