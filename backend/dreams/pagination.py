from rest_framework.pagination import PageNumberPagination


class DynamicPageSizePagination(PageNumberPagination):
    """
    Custom pagination class that allows dynamic page size via page_size parameter.
    """

    page_size = 20  # Default page size
    page_size_query_param = "page_size"  # Allow client to override page size
    max_page_size = 100  # Maximum page size to prevent abuse
