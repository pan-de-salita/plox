from abc import ABC, abstractmethod


class InformalParserInterface:
    def load_data_source(self, path: str, file_name: str) -> str:
        """Load in the file for extracting text."""
        return ""

    def extract_text(self, full_file_path: str) -> dict:
        """Extract test from the currently loaded file."""
        return {}


class PdfParser(InformalParserInterface):
    """Extract text from a PDF."""

    def load_data_source(self, path: str, file_name: str) -> str:
        """Overrides InformalParserInterface.load_data_source()."""
        return "PDF"

    def extract_text(self, full_file_path: str) -> dict:
        """Overrides InformalParserInterface.extract_text()."""
        return {"res": "pdf"}


class EmlParser(InformalParserInterface):
    """Extract text from an email."""

    def load_data_source(self, path: str, file_name: str) -> str:
        """Overrides InformalParserInterface.load_data_source()."""
        return "Email"

    def extract_text_from_email(self, full_file_path: str) -> dict:
        """A method defined only in EmlParser.
        Does not override InformalParserInterface.extract_text()"""
        return {"res": "email"}


issubclass(PdfParser, InformalParserInterface)  # True.
issubclass(EmlParser, InformalParserInterface)  # True. We want this to be False.
PdfParser.__mro__
EmlParser.__mro__


class ParserMeta(type):
    """A Parser metaclass that will be used for parser class creation."""

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    # When defined, called to implement issubclass(subclass, cls)
    # See https://docs.python.org/3/reference/datamodel.html#type.__subclasscheck__.
    def __subclasscheck__(cls, subclass):
        return (
            hasattr(subclass, "load_data_source")
            and callable(subclass.load_data_source)
            and hasattr(subclass, "extract_text")
            and callable(subclass.extract_text)
        )


class UpdatedInformalParserInterface(metaclass=ParserMeta):
    """This interface is used for concrete classes to inherit from.
    There is no need to define the ParserMeta methods as any class
    as they are implicitly made avaialble via .__subclasscheck__().
    """

    pass


# class PdfParserNew:
#     """Extract text from a PDF."""
#
#     def load_data_source(self, path: str, file_name: str) -> str:
#         """Overrides UpdatedInformalParserInterface.load_data_source()."""
#         return "PDF"
#
#     def extract_text(self, full_file_path: str) -> dict:
#         """Overrides UpdatedInformalParserInterface.extract_text()."""
#         return {"res": "pdf"}
#
#
# class EmlParserNew:
#     """Extract text from an email."""
#
#     def load_data_source(self, path: str, file_name: str) -> str:
#         """Overrides UpdatedInformalParserInterface.load_data_source()."""
#         return "Email"
#
#     def extract_text_from_email(self, full_file_path: str) -> dict:
#         """A method defined only in EmlParser.
#         Does not override UpdatedInformalParserInterface.extract_text()"""
#         return {"res": "email"}
#
#
# issubclass(PdfParserNew, UpdatedInformalParserInterface)  # True.
# issubclass(EmlParserNew, UpdatedInformalParserInterface)  # False!
# PdfParserNew.__mro__
# EmlParserNew.__mro__


class FormalParserInterface(ABC):
    # Is this needed for concrete classes to implement load_data_source()
    # and extract_text()?
    # @classmethod
    # def __subclasshook__(cls, subclass):
    #     return (
    #         hasattr(subclass, "load_data_source")
    #         and callable(subclass.load_data_source)
    #         and hasattr(subclass, "extract_text")
    #         and callable(subclass.extract_text)
    #     )

    @abstractmethod
    def load_data_source(self, path: str, file_name: str):
        """Load in the data set."""
        raise NotImplementedError

    @abstractmethod
    def extract_text(self, full_file_path: str):
        """Extract txt from the data set"""
        raise NotImplementedError


class PdfParserNew(FormalParserInterface):
    """Extract text from a PDF."""

    def load_data_source(self, path: str, file_name: str) -> str:
        """Overrides UpdatedInformalParserInterface.load_data_source()."""
        return "PDF"

    def extract_text(self, full_file_path: str) -> dict:
        """Overrides UpdatedInformalParserInterface.extract_text()."""
        return {"res": "pdf"}


class EmlParserNew(FormalParserInterface):
    """Extract text from an email."""

    def load_data_source(self, path: str, file_name: str) -> str:
        """Overrides UpdatedInformalParserInterface.load_data_source()."""
        return "Email"

    def extract_text_from_email(self, full_file_path: str) -> dict:
        """A method defined only in EmlParser.
        Does not override UpdatedInformalParserInterface.extract_text()"""
        return {"res": "email"}


issubclass(PdfParserNew, FormalParserInterface)  # True.
issubclass(EmlParserNew, FormalParserInterface)  # False!
PdfParserNew.__mro__
EmlParserNew.__mro__

pdf_parser = PdfParserNew()
eml_parser = EmlParserNew()  # Raises Exception.


# Crafting Interpreters Visitor Pattern example with pastries.


class Pastry(ABC):
    @abstractmethod
    def accept(self, visitor: "PastryVisitor"):
        pass


class Beignet(Pastry):
    def accept(self, visitor: "PastryVisitor"):
        visitor.visit_beignet(self)


class Cruller(Pastry):
    def accept(self, visitor: "PastryVisitor"):
        visitor.visit_cruller(self)


class PastryVisitor(ABC):
    @abstractmethod
    def visit_beignet(self, beignet: Beignet):
        pass

    @abstractmethod
    def visit_cruller(self, cruller: Cruller):
        pass
