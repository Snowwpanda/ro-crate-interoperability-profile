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
    match literal:
        case LiteralType.BOOLEAN:
            return XSD.boolean
        case LiteralType.INTEGER:
            return XSD.integer
        case LiteralType.DOUBLE:
            return XSD.double
        case LiteralType.DECIMAL:
            return XSD.decimal
        case LiteralType.FLOAT:
            return XSD.float
        case LiteralType.DATETIME:
            return XSD.dateTime
        case LiteralType.STRING:
            return XSD.string
        case LiteralType.XML_LITERAL:
            from rdflib.namespace import RDF

            return RDF.XMLLiteral
        case _:
            raise ValueError(f"Unknown LiteralType: {literal}")
