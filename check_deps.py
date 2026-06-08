import os, ast, sys
import importlib.util

stdlib_paths = [sys.base_prefix, sys.base_exec_prefix]

def is_stdlib(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        if spec.origin is None:
            return True
        return any(spec.origin.startswith(p) for p in stdlib_paths) and 'site-packages' not in spec.origin
    except:
        return False

modules = set()
for f in os.listdir('.'):
    if f.endswith('.py'):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            modules.add(name.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            modules.add(node.module.split('.')[0])
        except Exception as e:
            pass

missing = []
for m in modules:
    if m not in sys.builtin_module_names and not is_stdlib(m):
        try:
            importlib.import_module(m)
        except ImportError:
            missing.append(m)

print("MISSING_MODULES:", missing)
