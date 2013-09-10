import sys
import imp

def vandelay_import(module_path):
    if module_path in sys.modules:
        return sys.modules[module_path]

    parts = module_path.split('.')
    filename = None
    fileobj = None

    try:
        prefix = parts[:-1]
        last_part = parts[-1]
        for part in prefix:
            (fileobj, filename, descr) = imp.find_module(part, filename)
            if fileobj is not None:
                fileobj.close()
                fileobj = None
            filename = [filename]
        (fileobj, filename, descr) = imp.find_module(last_part, filename)
        module = imp.load_module(last_part, fileobj, filename, descr)
        return module

    finally:
        if fileobj is not None:
            fileobj.close()


