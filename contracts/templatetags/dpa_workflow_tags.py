"""Template filters for the DPA workflow builder — a single generic dict
lookup, needed because Django templates can't index a dict by a loop
variable (`{{ errors.field.key }}` looks up a literal "field" key, not the
value of the `field` template variable).
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None
