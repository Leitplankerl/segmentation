# ------------------------------------------------------------------------------
# Introspection function to create object instances from string arguments.
# ------------------------------------------------------------------------------

def get_class(class_path):
    """Creates a class dynamically."""
    if isinstance(class_path, str):
        class_path = class_path.split('.')
    class_name = class_path[-1]
    module_path = class_path[:-1]
    module = __import__('.'.join(module_path))
    for m in module_path[1:]:
        module = getattr(module, m)
    module = getattr(module, class_name)
    return module