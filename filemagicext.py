# -*- coding: utf-8 -*-

"""
magic is a wrapper around the libmagic file identification library.

See README for more information.

Usage:

>>> import magic
>>> magic.from_file("testdata/test.pdf")
'PDF document, version 1.2'
>>> magic.from_file("testdata/test.pdf", mime=True)
'application/pdf'
>>> magic.from_buffer(open("testdata/test.pdf").read(1024))
'PDF document, version 1.2'
>>>


"""

import sys
import glob
import os.path
import ctypes
import ctypes.util
import threading

from ctypes import c_char_p, c_int, c_size_t, c_void_p


class MagicException(Exception):
    def __init__(self, message):
        super(MagicException, self).__init__(message)
        self.message = message


class Magic:
    """
    Magic is a wrapper around the libmagic C library.

    """

    def __init__(self, mime=False, magic_file=None, mime_encoding=False,
                 keep_going=False, uncompress=False):
        """
        Create a new libmagic wrapper.

        mime - if True, mimetypes are returned instead of textual descriptions
        mime_encoding - if True, codec is returned
        magic_file - use a mime database other than the system default
        keep_going - don't stop at the first match, keep going
        uncompress - Try to look inside compressed files.
        """
        self.flags = MAGIC_NONE
        if mime:
            self.flags |= MAGIC_MIME
        elif mime_encoding:
            self.flags |= MAGIC_MIME_ENCODING
        if keep_going:
            self.flags |= MAGIC_CONTINUE

        if uncompress:
            self.flags |= MAGIC_COMPRESS

        self.cookie = magic_open(self.flags)
        self.lock = threading.Lock()

        magic_load(self.cookie, magic_file)

    def from_buffer(self, buf):
        """
        Identify the contents of `buf`
        """
        with self.lock:
            try:
                return maybe_decode(magic_buffer(self.cookie, buf))
            except MagicException as e:
                return self._handle509Bug(e)

    def from_file(self, filename):
        # raise FileNotFoundException or IOError if the file does not exist
        with open(filename):
            pass
        with self.lock:
            try:
                return maybe_decode(magic_file(self.cookie, filename))
            except MagicException as e:
                return self._handle509Bug(e)

    def _handle509Bug(self, e):
        # libmagic 5.09 has a bug where it might fail to identify the
        # mimetype of a file and returns null from magic_file (and
        # likely _buffer), but also does not return an error message.
        if e.message is None and (self.flags & MAGIC_MIME):
            return "application/octet-stream"
        else:
            raise e

    def __del__(self):
        # no _thread_check here because there can be no other
        # references to this object at this point.

        # during shutdown magic_close may have been cleared already so
        # make sure it exists before using it.

        # the self.cookie check should be unnecessary and was an
        # incorrect fix for a threading problem, however I'm leaving
        # it in because it's harmless and I'm slightly afraid to
        # remove it.
        if self.cookie and magic_close:
            magic_close(self.cookie)
            self.cookie = None


_instances = {}


def _get_magic_type(mime):
    i = _instances.get(mime)
    if i is None:
        i = _instances[mime] = Magic(mime=mime)
    return i


def from_file(filename, mime=False):
    """
    Accepts a filename and returns the detected filetype.  Return
    value is the mimetype if mime=True, otherwise a human readable
    name.

    >>> magic.from_file("testdata/test.pdf", mime=True)
    'application/pdf'
    """
    m = _get_magic_type(mime)
    return m.from_file(filename)


def from_buffer(buffer, mime=False):
    """
    Accepts a binary string and returns the detected filetype.  Return
    value is the mimetype if mime=True, otherwise a human readable
    name.

    >>> magic.from_buffer(open("testdata/test.pdf").read(1024))
    'PDF document, version 1.2'
    """
    m = _get_magic_type(mime)
    return m.from_buffer(buffer)


libmagic = None
# Let's try to find magic or magic1
dll = ctypes.util.find_library('magic') or ctypes.util.find_library(
    'magic1') or ctypes.util.find_library('cygmagic-1')

# This is necessary because find_library returns None if it doesn't find the library
if dll:
    libmagic = ctypes.CDLL(dll)

if not libmagic or not libmagic._name:
    windows_dlls = ['magic1.dll', 'cygmagic-1.dll']
    platform_to_lib = {'darwin': ['/opt/local/lib/libmagic.dylib',
                                  '/usr/local/lib/libmagic.dylib'] +
                                 # Assumes there will only be one version installed
                                 glob.glob(
                                     '/usr/local/Cellar/libmagic/*/lib/libmagic.dylib'),
                       'win32': windows_dlls,
                       'cygwin': windows_dlls}
    for dll in platform_to_lib.get(sys.platform, []):
        try:
            libmagic = ctypes.CDLL(dll)
            break
        except OSError:
            pass

if not libmagic or not libmagic._name:
    # It is better to raise an ImportError since we are importing magic module
    raise ImportError('failed to find libmagic.  Check your installation')

magic_t = ctypes.c_void_p


def errorcheck_null(result, func, args):
    if result is None:
        err = magic_error(args[0])
        raise MagicException(err)
    else:
        return result


def errorcheck_negative_one(result, func, args):
    if result is -1:
        err = magic_error(args[0])
        raise MagicException(err)
    else:
        return result


# return str on python3.  Don't want to unconditionally
# decode because that results in unicode on python2
def maybe_decode(s):
    if str == bytes:
        return s
    else:
        return s.decode('utf-8')


def coerce_filename(filename):
    if filename is None:
        return None

    # ctypes will implicitly convert unicode strings to bytes with
    # .encode('ascii').  If you use the filesystem encoding
    # then you'll get inconsistent behavior (crashes) depending on the user's
    # LANG environment variable
    is_unicode = (sys.version_info[0] <= 2 and
                  isinstance(filename, unicode)) or \
                 (sys.version_info[0] >= 3 and
                  isinstance(filename, str))
    if is_unicode:
        return filename.encode('utf-8')
    else:
        return filename


magic_open = libmagic.magic_open
magic_open.restype = magic_t
magic_open.argtypes = [c_int]

magic_close = libmagic.magic_close
magic_close.restype = None
magic_close.argtypes = [magic_t]

magic_error = libmagic.magic_error
magic_error.restype = c_char_p
magic_error.argtypes = [magic_t]

magic_errno = libmagic.magic_errno
magic_errno.restype = c_int
magic_errno.argtypes = [magic_t]

_magic_file = libmagic.magic_file
_magic_file.restype = c_char_p
_magic_file.argtypes = [magic_t, c_char_p]
_magic_file.errcheck = errorcheck_null


def magic_file(cookie, filename):
    return _magic_file(cookie, coerce_filename(filename))


_magic_buffer = libmagic.magic_buffer
_magic_buffer.restype = c_char_p
_magic_buffer.argtypes = [magic_t, c_void_p, c_size_t]
_magic_buffer.errcheck = errorcheck_null


def magic_buffer(cookie, buf):
    return _magic_buffer(cookie, buf, len(buf))


_magic_load = libmagic.magic_load
_magic_load.restype = c_int
_magic_load.argtypes = [magic_t, c_char_p]
_magic_load.errcheck = errorcheck_negative_one


def magic_load(cookie, filename):
    return _magic_load(cookie, coerce_filename(filename))


magic_setflags = libmagic.magic_setflags
magic_setflags.restype = c_int
magic_setflags.argtypes = [magic_t, c_int]

magic_check = libmagic.magic_check
magic_check.restype = c_int
magic_check.argtypes = [magic_t, c_char_p]

magic_compile = libmagic.magic_compile
magic_compile.restype = c_int
magic_compile.argtypes = [magic_t, c_char_p]

MAGIC_NONE = 0x000000  # No flags
MAGIC_DEBUG = 0x000001  # Turn on debugging
MAGIC_SYMLINK = 0x000002  # Follow symlinks
MAGIC_COMPRESS = 0x000004  # Check inside compressed files
MAGIC_DEVICES = 0x000008  # Look at the contents of devices
MAGIC_MIME = 0x000010  # Return a mime string
MAGIC_MIME_ENCODING = 0x000400  # Return the MIME encoding
MAGIC_CONTINUE = 0x000020  # Return all matches
MAGIC_CHECK = 0x000040  # Print warnings to stderr
MAGIC_PRESERVE_ATIME = 0x000080  # Restore access time on exit
MAGIC_RAW = 0x000100  # Don't translate unprintable chars
MAGIC_ERROR = 0x000200  # Handle ENOENT etc as real errors

MAGIC_NO_CHECK_COMPRESS = 0x001000  # Don't check for compressed files
MAGIC_NO_CHECK_TAR = 0x002000  # Don't check for tar files
MAGIC_NO_CHECK_SOFT = 0x004000  # Don't check magic entries
MAGIC_NO_CHECK_APPTYPE = 0x008000  # Don't check application type
MAGIC_NO_CHECK_ELF = 0x010000  # Don't check for elf details
MAGIC_NO_CHECK_ASCII = 0x020000  # Don't check for ascii files
MAGIC_NO_CHECK_TROFF = 0x040000  # Don't check ascii/troff
MAGIC_NO_CHECK_FORTRAN = 0x080000  # Don't check ascii/fortran
MAGIC_NO_CHECK_TOKENS = 0x100000  # Don't check ascii/tokens

################################################################################

def from_file(filename):
    m = _get_magic_type(False)
    base_info = m.from_file(filename)
    return TypeInfo(base_info=base_info)


def from_buffer(buffer):
    m = _get_magic_type(False)
    base_info = m.from_buffer(buffer)
    return TypeInfo(base_info=base_info)


class TypeInfo(object):

    def __init__(self, base_info, mime=None):
        super(TypeInfo, self).__init__()
        self._base_info = base_info
        self._mime = mime

    # def is_ppt(self):
    #     return self._mime == 'application/vnd.ms-powerpoint' or self._mime == 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    #
    # def is_word(self):
    #     return self._mime == 'application/msword' or self._mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    #
    # def is_excel(self):
    #     return self._mime == 'application/vnd.ms-excel' or self._mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    # def is_rft(self):
    #     return self._mime == 'text/rtf'
    #
    # def is_html(self):
    #     return self._mime == 'text/html'

    def is_word(self):
        '''
        macOS docx: Microsoft Word 2007+
        macOS doc:  Composite Document File V2 Document, Little Endian, Os: MacOS, Version 10.3, Code page: 10008, Author: Microsoft Office , Template: Normal.dotm, Last Saved By: Microsoft Office , Revision Number: 3, Name of Creating Application: Microsoft Macintosh Word, Create Time/Date: Mon May 14 08:18:00 2018, Last Saved Time/Date: Mon May 14 08:18:00 2018, Number of Pages: 1, Number of Words: 0, Number of Characters: 0, Security: 0
        win docx:   Microsoft Word 2007+
        win doc:    Composite Document File V2 Document, Little Endian, Os: Windows, Version 5.1, Code page: 936, Title: C++, Template: Normal, Revision Number: 1, Name of Creating Application: Microsoft Office Word, Total Editing Time: 02:00, Create Time/Date: Thu Feb  2 12:48:00 2012, Last Saved Time/Date: Thu Feb  2 12:50:00 2012, Number of Pages: 1, Number of Words: 1210, Number of Characters: 6897, Security: 0
        '''
        return "Microsoft Office Word" in self._base_info or \
               self._base_info == "Microsoft Word document (*.docx)" or \
               'Microsoft Macintosh Word' in self._base_info or \
               self._base_info == 'Microsoft Word 2007+'

    def is_excel(self):
        '''
        macOS xlsx: Microsoft Excel 2007+
        macOS xls:  Composite Document File V2 Document, Little Endian, Os: MacOS, Version 10.3, Code page: 10008, Author: Microsoft Office , Last Saved By: Microsoft Office , Name of Creating Application: Microsoft Macintosh Excel, Create Time/Date: Mon May 14 08:20:11 2018, Last Saved Time/Date: Mon May 14 08:20:22 2018, Security: 0
        win xlsx:   Microsoft Excel 2007+
        win xls:    Composite Document File V2 Document, Little Endian, Os: Windows, Version 5.0, Code page: 936, Name of Creating Application: Microsoft Excel, Create Time/Date: Tue Dec 17 01:32:42 1996, Last Saved Time/Date: Thu Jan 31 07:43:10 2008, Security: 0
        '''
        return "Microsoft Excel" in self._base_info or \
               self._base_info == "Microsoft Excel document (*.xlsx)" or \
               'Microsoft Macintosh Excel' in self._base_info or \
               self._base_info == 'Microsoft Excel 2007+'

    def is_ppt(self):
        '''
        macOS pptx: Microsoft PowerPoint 2007+
        macOS ppt:  Composite Document File V2 Document, Little Endian, Os: MacOS, Version 10.3, Code page: 10008, Title: PowerPoint , Author: Microsoft Office , Last Saved By: Microsoft Office , Revision Number: 1, Name of Creating Application: Microsoft Macintosh PowerPoint, Total Editing Time: 00:15, Create Time/Date: Mon May 14 08:19:15 2018, Last Saved Time/Date: Mon May 14 08:19:31 2018, Number of Words: 0
        win pptx:   Microsoft PowerPoint 2007+
        win ppt:    Composite Document File V2 Document, Little Endian, Os: Windows, Version 6.1, Code page: 936, Title: PowerPoint , Author: mwz2, Last Saved By: nijch, Revision Number: 69, Name of Creating Application: Microsoft Office PowerPoint, Total Editing Time: 3d+10:21:36, Create Time/Date: Wed Mar 24 08:08:03 2004, Last Saved Time/Date: Sun Nov 25 10:53:30 2012, Number of Words: 13734
        '''
        return "Microsoft Office PowerPoint" in self._base_info or \
               self._base_info == "Microsoft PowerPoint document (*.pptx)" or \
               'Microsoft Macintosh PowerPoint' in self._base_info or \
               self._base_info == 'Microsoft PowerPoint 2007+'

    def is_pdf(self):
        return self._base_info.startswith("PDF document")

    def is_rtf(self):
        return self._base_info.startswith("Rich Text Format")

    def is_html(self):
        return self._base_info.startswith('HTML document text')

    def is_script(self):
        return 'script' in self._base_info

    def is_other_text(self):
        return 'text' in self._base_info

    def is_linux_executable(self):
        return "ELF" in self._base_info or "COFF" in self._base_info

    def is_pe(self):
        return " PE " in self._base_info or " PE32" in self._base_info or \
               self._base_info.startswith("PE ") or \
               self._base_info.startswith("MS-DOS executable") or \
               self._base_info.startswith("Self-extracting PKZIP archive") or \
               self._base_info.startswith("Microsoft Windows Autorun file") or \
               self._base_info.startswith("x86 boot sector")

    def is_7_zip(self):
        return self._base_info.startswith("7-zip archive data")

    def is_rar(self):
        return self._base_info.startswith("RAR archive data")

    def is_tar(self):
        return self._base_info == "tar archive"

    def is_other_zip(self):
        return  self._base_info.startswith("application/zip") or \
                self._base_info.startswith("Zip archive data") or \
                self._base_info.startswith("gzip compressed data") or \
                self._base_info.startswith("Microsoft Cabinet archive") or \
                self._base_info.startswith("bzip2 compressed data") or \
                self._base_info.startswith("POSIX tar archive") or \
                self._base_info == "InstallShield CAB" or \
                self._base_info.startswith("xar archive") or \
                self._base_info == "xz compressed data" or \
                self._base_info.startswith("Zip64 archive data")