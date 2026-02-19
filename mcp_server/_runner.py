import os
import sys
import importlib
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr


def run_extraction(env_vars: dict, log_path: str):
    """Run Read_Medium_From_Gmail.main() with provided env vars and append logs to log_path.

    This imports the module (without modifying it) and calls its `main()` entrypoint.
    """
    # Backup current env vars we will override
    backup = {k: os.environ.get(k) for k in env_vars.keys()}
    os.environ.update({k: v for k, v in env_vars.items() if v is not None})

    timestamp = datetime.utcnow().isoformat()
    try:
        # Import the target module fresh. Try normal import first,
        # otherwise load directly from the repository root file path.
        try:
            if "Read_Medium_From_Gmail" in sys.modules:
                importlib.reload(sys.modules["Read_Medium_From_Gmail"])
                module = sys.modules["Read_Medium_From_Gmail"]
            else:
                module = importlib.import_module("Read_Medium_From_Gmail")
        except Exception:
            # Fallback: locate Read_Medium_From_Gmail.py relative to repo root
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            candidate = os.path.join(repo_root, "Read_Medium_From_Gmail.py")
            if not os.path.exists(candidate):
                # As a last resort, search upwards from cwd for the file
                cur = os.getcwd()
                found = None
                for _ in range(6):
                    p = os.path.join(cur, "Read_Medium_From_Gmail.py")
                    if os.path.exists(p):
                        found = p
                        break
                    cur = os.path.dirname(cur)
                if found:
                    candidate = found

            if not os.path.exists(candidate):
                raise ImportError("Could not find Read_Medium_From_Gmail.py to import")

            # Load module from file location
            import importlib.util

            spec = importlib.util.spec_from_file_location("Read_Medium_From_Gmail", candidate)
            module = importlib.util.module_from_spec(spec)
            sys.modules["Read_Medium_From_Gmail"] = module
            spec.loader.exec_module(module)

        # Prepare argv for non-interactive run (module.main will parse args)
        old_argv = sys.argv[:]
        sys.argv = [module.__file__]

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"\n=== RUN START {timestamp} ===\n")
            try:
                with redirect_stdout(lf), redirect_stderr(lf):
                    module.main()
            except SystemExit:
                # main() may call sys.exit(); treat as normal termination
                pass
            except Exception as e:
                lf.write(f"\nERROR during run: {e}\n")
            lf.write(f"\n=== RUN END {datetime.utcnow().isoformat()} ===\n")

    finally:
        # Restore argv and environment
        sys.argv = old_argv
        for k, v in backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
