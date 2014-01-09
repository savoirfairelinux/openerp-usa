##Module that converts the Xml response to dictionary
from lxml import etree
import re

def dictlist(node):
    res = {}
    node_tag = re.findall(r'}(\w*)', node.tag)
    node_tag = node_tag[0]
    res[node_tag] = []
    xmltodict(node, res[node_tag])
    reply = {}
    reply[node_tag] = res[node_tag]

    return reply

def xmltodict(node, res):
    rep = {}
    node_tag = re.findall(r'}(\w*)', node.tag)
    node_tag = node_tag[0]
    if len(node):
        #n = 0
        for n in list(node):

            rep[node_tag] = []
            value = xmltodict(n, rep[node_tag])
            if len(n):
                n_tag = re.findall(r'}(\w*)', n.tag)
                n_tag = n_tag[0]
                value = rep[node_tag]
                res.append({n_tag:value})
            else :

                res.append(rep[node_tag][0])

    else:
        value = {}
        value = node.text
        res.append({node_tag:value})

    return

def main(xml_string):
    tree = etree.fromstring(xml_string)
    res = dictlist(tree)
    return res

if __name__ == '__main__' :
    main()
