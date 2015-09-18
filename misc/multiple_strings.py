# coding=utf-8


def multiple_of(value, string_of_single, string_of_multiple, return_with_value=False,
                before_string='', after_string=''):
    """
    Helps with english. If the word has a form of multiple, you can feed it's value
    and it returns you the appropriate form. (Also has some extra features, in case you have a collection of strings.)

    :param value: Numerical value
    :type value: bool | float | int
    :param string_of_single: String representation of a single thing
    :type string_of_single: str
    :param string_of_multiple: String representation of multiple things
    :type string_of_multiple: str
    :param return_with_value: Should it return with the value formatted?
    :type return_with_value: bool
    :param before_string: String content before
    :type before_string: str
    :param after_string: String content after
    :type after_string: str
    :return: Complete string representation
    :rtype: str
    """
    cache = ''
    cache += before_string

    if return_with_value:
        cache += str(value) + " "
    if value == 0:
        return
    if value == 1:
        return cache + string_of_single + after_string
    return cache + string_of_multiple + after_string
