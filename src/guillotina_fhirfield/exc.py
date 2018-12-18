from zope.interface import Invalid


class SearchQueryError(Invalid):
    """ """


class SearchQueryValidationError(SearchQueryError):
    """ """


__all__ = [str(x) for x in ('SearchQueryError', 'SearchQueryValidationError')]
