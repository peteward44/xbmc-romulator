
import xml
from xml.dom import minidom


def FindFirstDataInXmlTagList( dom, tagName ):

	tag = FindFirstChildNodeByTagName( dom, tagName )
	if tag != None:
		for childTag in tag.childNodes:
			if childTag.nodeType == childTag.TEXT_NODE or childTag.nodeType == childTag.CDATA_SECTION_NODE:
				return childTag.data
	return None


def FindChildNodesByTagName( dom, tagName ):

	list = []
	for childTag in dom.childNodes:
		if childTag.nodeType == childTag.ELEMENT_NODE and childTag.localName == tagName:
			list.append( childTag )
	return list


def FindFirstChildNodeByTagName( dom, tagName ):

	for childTag in dom.childNodes:
		if childTag.nodeType == childTag.ELEMENT_NODE and childTag.localName == tagName:
			return childTag
	return None


def GetAttributeDefault( domNode, attribName, defaultValue ):

	try:
		return domNode.getAttribute( attribName )
	except:
		pass

	return defaultValue
	
	
	