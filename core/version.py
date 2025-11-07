from importlib import metadata

try:
    # The package name is normalized to lowercase by packaging tools
    __version__ = metadata.version("contextpacker")
except metadata.PackageNotFoundError:
    # The package is not installed, so we fall back to a default version.
    # This is useful for development environments or running from source
    # without an editable install.
    __version__ = "0.0.0-dev"
