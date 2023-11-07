import warnings ,urllib3

from .exceptions import RequestsDependencyWarning

try: from charset_normalizer import __version__ as charset_normalizer_version
except ImportError: charset_normalizer_version = None

try: from chardet import __version__ as chardet_version
except ImportError: chardet_version = None


def check_compatibility(urllib3_version, chardet_version, charset_normalizer_version):
    urllib3_version = urllib3_version.split("."); assert urllib3_version != ["dev"]

    if len(urllib3_version) == 2: urllib3_version.append("0")

    major, minor, patch = urllib3_version; major, minor, patch = int(major), int(minor), int(patch)
    assert major >= 1
    if major == 1: assert minor >= 21

    if chardet_version:
        major, minor, patch = chardet_version.split(".")[:3]
        major, minor, patch = int(major), int(minor), int(patch)
        assert (3, 0, 2) <= (major, minor, patch) < (6, 0, 0)
    elif charset_normalizer_version:
        major, minor, patch = charset_normalizer_version.split(".")[:3]
        major, minor, patch = int(major), int(minor), int(patch)
        assert (2, 0, 0) <= (major, minor, patch) < (4, 0, 0)
    else: raise Exception("You need either charset_normalizer or chardet installed")


def _check_cryptography(cryptography_version):
    try: cryptography_version = list(map(int, cryptography_version.split(".")))
    except ValueError: return

    if cryptography_version < [1, 3, 4]:
        warning = "Old version of cryptography ({}) may cause slowdown.".format( cryptography_version )
        warnings.warn(warning, RequestsDependencyWarning)


try: check_compatibility( urllib3.__version__, chardet_version, charset_normalizer_version )
except (AssertionError, ValueError): warnings.warn("urllib3 ({}) or chardet ({})/charset_normalizer ({}) doesn't match a supported " "version!".format( urllib3.__version__, chardet_version, charset_normalizer_version ), RequestsDependencyWarning, )


try:
    try: import ssl
    except ImportError: ssl = None

    if not getattr(ssl, "HAS_SNI", False):
        from urllib3.contrib import pyopenssl

        pyopenssl.inject_into_urllib3()

        # Check cryptography version
        from cryptography import __version__ as cryptography_version

        _check_cryptography(cryptography_version)
except ImportError: pass

# urllib3's DependencyWarnings should be silenced.
from urllib3.exceptions import DependencyWarning

warnings.simplefilter("ignore", DependencyWarning)

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

from . import packages, utils
from .__version__ import ( __author__, __author_email__, __build__, __cake__, __copyright__, __description__, __license__, __title__, __url__, __version__,
)
from .api import delete, get, head, options, patch, post, put, request
from .exceptions import ( ConnectionError, ConnectTimeout, FileModeWarning, HTTPError, JSONDecodeError, ReadTimeout, RequestException, Timeout, TooManyRedirects, URLRequired,)
from .models import PreparedRequest, Request, Response
from .sessions import Session, session
from .status_codes import codes

logging.getLogger(__name__).addHandler(NullHandler())

# FileModeWarnings go off per the default.
warnings.simplefilter("default", FileModeWarning, append=True)
