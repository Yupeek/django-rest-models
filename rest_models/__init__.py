__VERSION__ = '3.0.2'

try:
    from rest_models.checks import register_checks
    register_checks()
except ImportError:  # pragma: no cover
    pass
