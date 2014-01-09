##Module that converts the Xml response to dictionary
from lxml import etree


def dictlist(node):
	res = {}
	res[node.tag] = []
	xmltodict(node,res[node.tag])
	reply = {}
	reply[node.tag] =res[node.tag]

	return reply

def xmltodict(node,res):
	rep = {}

	if len(node):
		#n = 0
		for n in list(node):
			rep[node.tag] = []
			value = xmltodict(n,rep[node.tag])
			if len(n):

				value = rep[node.tag]
				res.append({n.tag:value})
			else :

				res.append(rep[node.tag][0])

	else:
		value = {}
		value = node.text
		res.append({node.tag:value})

	return

def main(xml_string):
	tree = etree.fromstring(xml_string)
	res = dictlist(tree)
	return res


if __name__ == '__main__' :
	main()
