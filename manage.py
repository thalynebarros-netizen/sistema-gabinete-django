#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    vendor_dir = Path(__file__).resolve().parent / "vendor"
    vendor_django = vendor_dir / "django" / "__init__.py"
    try:
        vendor_django.read_bytes()
        can_use_vendor = True
    except (OSError, PermissionError):
        can_use_vendor = False
    if can_use_vendor:
        sys.path.insert(0, str(vendor_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
