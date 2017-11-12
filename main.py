import collections, sys, re, pprint
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
		parent = match[1].strip()
		number = match[2].strip()
		#print ("OBJECT-IDENTIFIER: {}\nPARENT: {}\nNUMBER: {}\n\n".format(id, parent, number))
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
	
def build_tree(lista, llista):
	nodes = []
	lista.insert(0, ('iso', None, 1))
	lista.insert(1, ('org', 'iso', 3))
	lista.insert(2, ('dod', 'org', 6))
	lista.insert(3, ('internet', 'dod', 1))
	
	nodes.append(Node(("iso", None, 1), parent = None))
	nodes.append(Node(("org", "iso", 3), parent = None))
	nodes.append(Node(("dod", "org", 6), parent = None))
	nodes.append(Node(("internet", "dod", 1), parent = None))
	
	
	lista = list(set(lista))
	llista = list(set(llista))
	llista.sort()
	#pprint.pprint (llista)

	#'internet' entry duplicates popping 
	for i, item in enumerate(lista):
		if item[0] == 'internet' and item[1] != 'dod':
			lista.pop(i)
	
	#remove duplicates from long-list
	
	#TODO: sprawdzać, czy pozycja llista[0] się powtarza, i zostawiać wersję z opisem jeśli są dwie
	saved = []
	for i,l in enumerate(llista):
		saved = l[0], i
		if l[0] in saved:
			if l[4] == '':
				llista.pop(i)
			#else:
				#llista.pop(int(l[1]))
			
	
	for item in lista:
		if item[0] == 'iso' or item[0] == 'org' or item[0] == 'dod' or item[0] == 'internet':
			continue
		nodes.append(Node((item[0], item[1], item[2]), parent = None))
		
	for iitem in llista:
		nodes.append(Node((iitem[0], iitem[6], iitem[7]), parent = None))
	
	for n in nodes:
		n.children = [x for x in nodes if x.name[1] == n.name[0]]
	
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
	build_tree(id_list, type_list)
	print("\n***\nTask 2 completed successfully.\n***\n")
	
	#print (id_list)
		
main()

