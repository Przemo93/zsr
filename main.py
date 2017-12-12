import collections, sys, re, pprint
from anytree import Node, RenderTree, PreOrderIter, LevelOrderIter
	
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
	
	nodes.append(Node(["iso", None, 1, "oid", None, None, None, None, '1'], parent = None))
	nodes.append(Node(["org", "iso", 3, "oid", None, None, None, None, '0'], parent = None))
	nodes.append(Node(["dod", "org", 6, "oid", None, None, None, None, '0'], parent = None))
	nodes.append(Node(["internet", "dod", 1, "oid", None, None, None, None, '0'], parent = None))
	
	lista = list(set(lista))
	llista = list(set(llista))
	llista.sort()
	#pprint.pprint (llista)

	#'internet' entry duplicates popping 
	'''for i, item in enumerate(lista):
		if item[0] == 'internet' and item[1] != 'dod':
			lista.pop(i)'''
	
	#remove duplicates from long-list
	saved = []
	for i,l in enumerate(llista):
		saved = l[0], i
		if l[0] in saved:
			if l[4] == '':
				llista.pop(i)
			
	
	for item in lista:
		if item[0] == 'iso' or item[0] == 'org' or item[0] == 'dod' or item[0] == 'internet':
			continue
		nodes.append(Node([item[0], item[1], item[2], "oid", None, None, None, None, '0'], parent = None))
		
	# 0 nazwa, 1 rodzic, 2 cyferka, 3 syntax (typ), 4 access (dostępność), 5 status (obowiązkowość), 6 opis, 7 entry(rodzic), 8 path
		
	for iitem in llista:
		nodes.append(Node([iitem[0], iitem[6], iitem[7], iitem[1], iitem[2], iitem[3], iitem[4], iitem[5], '0'], parent = None))
	
	for n in nodes:
		n.children = [x for x in nodes if x.name[1] == n.name[0]]
		
	#nodes.sort(key=lambda n:int(n.name[8]))
		
	#nodes = build_paths(nodes)
		
	return nodes

def display_mib(name, tree):
	al = ''
	for s in name:
		if s is '.':
			continue
		else:
			al += s 
	for n in tree:
		if al == n.name[8] or al == n.name[0]:
			print ("\nOBJECT-TYPE: {}\nSYNTAX: {}\nACCESS: {}\nSTATUS: {}\nDESCRIPTION: {}\nNUMBER: {}\nENTRY: {}\n\n".\
			format(n.name[0],n.name[3],n.name[4],n.name[5],n.name[6],n.name[2],n.name[1],n.name[7]))
			#print (n)
	
		

def build_paths(tree):
	for n in LevelOrderIter(tree[0]):
		if n.name[1] == None: #skip root of the tree
			continue	
		try:
			n.name[8] = n.parent.name[8] + str(n.name[2])
		except:
			print (n)
			print ("caused exception\n")
			pass
			
	#tree.sort(key=lambda x: int(x.name[8]))
	return tree

def sortbypath(items):
	return sorted(items, key=lambda item:int(item.name[8]))

def print_tree(nodes):
	#nodes.sort(key=lambda n:int(n.name[8]))
	for pre, _, node in RenderTree(nodes[0], childiter=sortbypath):
		#if(node.name[8][0]=='0'): #debug
		print("%s(%s)%s - %s, %s, %s" % (pre, node.name[2], node.name[0], node.name[3], node.name[4], node.name[5]))
		
def main():
	imported = []
	type_list = []
	id_list = []
	tree = []
	arg_file_content = loadFile(sys.argv[1])
	print("\n***\nPerforming task 1 - parsing files.\n***\n")
	type_list, id_list = match_regexes(arg_file_content, sys.argv[1], imported, [], []) #zawartość pliku, nazwa pliku, lista importów
	type_list, id_list = clean_lists(type_list, id_list)
	print("\n***\nTask 1 completed successfully.\n***\n")
	print("\n***\nPerforming task 2 - building binary tree.\n***\n")
	tree = build_tree(id_list, type_list)
	tree = build_paths(tree)
	print_tree(tree)
	print("\n***\nTask 2 completed successfully.\n***\n")
	mib_string = ""
	while mib_string != "q":
		mib_string = input("enter mib to display, e.x. 1.3.6.1.2.1, 1361 or egpNeighAs, q to quit: ")
		display_mib(mib_string, tree)
		
		
main()

