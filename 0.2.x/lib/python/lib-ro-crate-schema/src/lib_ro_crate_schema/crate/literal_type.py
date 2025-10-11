from enum import Enum

from rdflib import Node, XSD


class LiteralType(Enum):
    BOOLEAN = "xsd:boolean"
    INTEGER = "xsd:integer"
    DOUBLE = "xsd:double"
    DECIMAL = "xsd:decimal"
    FLOAT = "xsd:float"
    DATETIME = "xsd:dateTime"
    STRING = "xsd:string"
    XML_LITERAL = "rdf:XMLLiteral"


def to_rdf(literal: LiteralType) -> Node:
    if literal == LiteralType.BOOLEAN:
        return XSD.boolean
    elif literal == LiteralType.INTEGER:
        return XSD.integer
    elif literal == LiteralType.DOUBLE:
        return XSD.double
    elif literal == LiteralType.DECIMAL:
        return XSD.decimal
    elif literal == LiteralType.FLOAT:
        return XSD.float
    elif literal == LiteralType.DATETIME:
        return XSD.dateTime
    elif literal == LiteralType.STRING:
        return XSD.string
    elif literal == LiteralType.XML_LITERAL:
        from rdflib.namespace import RDF
        return RDF.XMLLiteral
    else:
        raise ValueError(f"Unknown LiteralType: {literal}")
