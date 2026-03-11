import importlib.util, sys, os

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

routes_dir = r"c:\Users\HP\OneDrive\Desktop\Parani_Dev_Proj\aihas\app\routes"

for bp_name in ['auth', 'patients', 'beds', 'emergency', 'vitals', 'pharmacy', 'analytics', 'records', 'appointments']:
    print(f"Loading {bp_name}...", flush=True)
    load_module(bp_name, os.path.join(routes_dir, f"{bp_name}.py"))
    print(f"Finished {bp_name}", flush=True)
