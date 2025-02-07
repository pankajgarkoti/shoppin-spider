import re


def filter_product_urls(urls: list[str]) -> list[str]:
    """
    From a list of URLs select the ones that are product pages.
    The product pages are identified by the presence of specific patterns in the URL.

    Common patterns detected:
    - /p/, /product/, /item/ in the path
    - Product IDs/SKUs (alphanumeric sequences)
    - Category hierarchies leading to products
    - Product detail or PDP indicators

    Args:
        urls (list[str]): list of URLs
    Returns:
        list[str]: list of product URLs
    """

    patterns_regex = [
        r"/p/[\w-]+",  # /p/ followed by product identifier
        r"/product/[\w-]+",  # /product/ followed by identifier
        r"/item/[\w-]+",  # /item/ followed by identifier
        r"/[\w-]+/[\w-]+/p/[\w-]+",  # category/subcategory/p/product structure
        r"/pd/[\w-]+",  # product detail pages
        r"/[\w-]+/\d+\.html",  # product pages with numeric IDs
        r"/products?/[\w-]{6,}",  # /product(s)/ with longer identifiers
        r"/catalog/product/view/id/\d+",  # common ecommerce platform pattern
        r"/dp/[A-Z0-9]{10}",  # Amazon-style product identifiers
        r"-pid-\d+",  # PID based product identifiers
    ]

    # Combine all patterns with OR operator
    combined_pattern = "|".join(f"({pattern})" for pattern in patterns_regex)

    # Filter URLs that match any of the patterns
    product_urls = [
        url for url in urls if re.search(combined_pattern, url, re.IGNORECASE)
    ]

    return product_urls
