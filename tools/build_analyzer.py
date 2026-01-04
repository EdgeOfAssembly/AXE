import argparse
import json
import logging
import os
import re
import sys
import tarfile
import io

# Optional zstd support
try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

def version_key(v):
    if v == 'Not specified':
        return (0, 0, 0)
    parts = []
    for p in v.split('.'):
        # Extract only leading numeric part to handle versions like "2.52.20210101"
        num_match = re.match(r'^(\d+)', p)
        if num_match:
            parts.append(int(num_match.group(1)))
        else:
            parts.append(0)
    # Ensure at least 3 parts for consistent comparison
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)

def find_project_roots(directory, main_filenames):
    main_filenames = {f.lower() for f in main_filenames}
    main_file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower() in main_filenames:
                main_file_paths.append(os.path.join(root, file))
    roots = []
    for path in main_file_paths:
        proj_dir = os.path.dirname(path)
        is_subproject = False
        parent = os.path.dirname(proj_dir)
        while os.path.commonpath([parent, directory]) == directory:
            if any(os.path.dirname(mp) == parent for mp in main_file_paths):
                is_subproject = True
                break
            parent = os.path.dirname(parent)
        if not is_subproject:
            roots.append(proj_dir)
    return sorted(roots)

def clean_autotools_content(content):
    lines = []
    for line in content.splitlines():
        line = line.split('dnl')[0].rstrip()
        if line:
            lines.append(line)
    return '\n'.join(lines)

def clean_comment_lines(content):
    """Remove lines starting with # comments (used for Makefile, CMake, Meson)."""
    lines = []
    for line in content.splitlines():
        if not line.strip().startswith('#'):
            lines.append(line)
    return '\n'.join(lines)

def parse_configure(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        logging.warning(f"Could not read {file_path}: {e}")
        return 'Not specified', 'Not specified', [], [], []
    content = clean_autotools_content(raw_content)
    # Autoconf version
    ac_vers = []
    for match in re.finditer(r'AC_PREREQ\s*\(\s*\[?(\d+\.\d+(?:\.\d+)?)\]?\s*\)', content, re.M):
        ac_vers.append(match.group(1))
    ac_ver = max(ac_vers, key=version_key) if ac_vers else 'Not specified'
    # Automake version from configure
    am_vers = []
    am_init = re.search(r'AM_INIT_AUTOMAKE\s*\(\s*\[?([^\]]*)\]?\s*\)', content, re.M)
    if am_init:
        args = am_init.group(1)
        vers = re.findall(r'\d+\.\d+(?:\.\d+)?', args)
        am_vers.extend(vers)
    am_ver = max(am_vers, key=version_key) if am_vers else 'Not specified'
    # Options (configure switches)
    options = set()
    # Environment variables
    env_vars = set()
    # AC_ARG_ENABLE
    for match in re.finditer(r'AC_ARG_ENABLE\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content, re.M):
        feature = match.group(1)
        options.add(f'--enable-{feature}')
        options.add(f'--disable-{feature}')
    # AC_ARG_WITH
    for match in re.finditer(r'AC_ARG_WITH\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content, re.M):
        package = match.group(1)
        options.add(f'--with-{package}')
        options.add(f'--without-{package}')
    # AC_ARG_VAR - extract environment variables separately
    for match in re.finditer(r'AC_ARG_VAR\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content, re.M):
        var = match.group(1)
        env_vars.add(var)
    # Deps
    lines = raw_content.splitlines()
    current_conditions = []
    deps_dict = {}  # key: dep_base, value: is_optional
    non_linux_terms = ['darwin', 'ios', 'windows', 'cygwin', 'cocoa', 'carbon', 'win32', 'msvc', 'android', 'solaris', 'sun', 'bsd', 'next', 'aix', 'hpux', 'osf', 'qnx', 'beos', 'machten', 'rhapsody', 'dgux', 'cray', 'nsk', 'opennt', 'interix', 'openbsd', 'netbsd', 'freebsd', 'dragonfly', 'minix', 'lynxos', 'kfreebsd', 'knetbsd', 'gnu', 'haiku', 'ultrix', 'sco', 'irix', 'newsos', 'os2', 'aux', 'convex', 'mips', 'pyramid', 'univel', 'dynix', 'ekko', 'hiux', 'isc', 'powerux', 'pwux', 'stellar', 'svr4', 'svr3', 'svr2', 'svr1', 'sunos', 'unixware', 'xenix']
    optional_terms = ['with_', 'enable_', 'opt_', 'use_', 'want_']
    skip_terms = ['yes', 'no', 'true', 'false', 'sun', 'dl']
    # Common system programs that should not be treated as dependencies
    skip_progs = ['rm', 'cp', 'mv', 'ln', 'cat', 'echo', 'grep', 'sed', 'awk', 'find', 'mkdir', 'chmod', 'chown', 
                  'tar', 'gzip', 'bzip2', 'xz', 'ar', 'ranlib', 'strip', 'install', 'make', 'sh', 'bash',
                  'test', 'expr', 'true', 'false', 'pwd', 'ls', 'touch', 'head', 'tail', 'sort', 'uniq',
                  'cut', 'tr', 'wc', 'diff', 'patch', 'cmp', 'file', 'date', 'env', 'uname', 'which',
                  'dirname', 'basename', 'realpath', 'readlink', 'nm', 'objdump', 'objcopy',
                  'docbook2html', 'docbook2man', 'docbook2pdf', 'docbook2txt', 'xsltproc',
                  'lib.exe', 'link.exe', 'cl.exe', 'ml.exe', 'ml64.exe']
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('if ') or 'test ' in stripped or stripped.startswith('case '):
            current_conditions.append(stripped)
        elif stripped.startswith('fi') or stripped.startswith('esac'):
            if current_conditions:
                current_conditions.pop()
        # AC_CHECK_LIB
        match = re.search(r'AC_CHECK_LIB\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', line, re.M)
        if match:
            lib = match.group(1)
            if lib.lower() in skip_terms or lib.isupper() or 'FLAGS' in lib or 'LIB' in lib:
                continue
            if lib == 'z':
                lib = 'zlib'
            dep_base = lib
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
        # AC_CHECK_PROG
        match = re.search(r'AC_CHECK_PROG\s*\(\s*[^,]+\s*,\s*\[?([a-zA-Z0-9_.-]+)\]?\s*,', line, re.M)
        if match:
            prog = match.group(1)
            if prog.lower() in skip_terms or prog.lower() in skip_progs or prog.isupper() or 'FLAGS' in prog or 'LIB' in prog:
                continue
            dep_base = prog
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
        # PKG_CHECK_MODULES
        match = re.search(r'PKG_CHECK_MODULES\s*\(\s*[^,]+\s*,\s*([^)]+)', line, re.M)
        if match:
            modules = match.group(1).strip()
            for spec_match in re.finditer(r'([a-zA-Z0-9_+-]+)(?:\s*([<>=~!]+)\s*([\d.]+))?', modules):
                mod = spec_match.group(1)
                op = spec_match.group(2)
                ver = spec_match.group(3)
                if mod.lower() in skip_terms or mod.isupper() or 'FLAGS' in mod or 'LIB' in mod:
                    continue
                dep_base = f'{mod} {op} {ver}'.strip() if op and ver else mod
                is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
                if is_non_linux:
                    continue
                is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
                if dep_base not in deps_dict:
                    deps_dict[dep_base] = is_optional_this
                else:
                    if not is_optional_this:
                        deps_dict[dep_base] = False
    # Build deps set with tags
    deps = set()
    for dep_base, is_opt in sorted(deps_dict.items()):
        dep_str = dep_base + (' (optional)' if is_opt else '')
        deps.add(dep_str)
    return ac_ver, am_ver, sorted(options), sorted(env_vars), sorted(deps)

def parse_automake(file_path, current_am_ver):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        logging.warning(f"Could not read {file_path}: {e}")
        return current_am_ver
    content = clean_comment_lines(raw_content)
    # AUTOMAKE_OPTIONS
    am_options = re.search(r'AUTOMAKE_OPTIONS\s*=\s*([^\n]*)', content, re.M)
    if am_options:
        args = am_options.group(1)
        versions = re.findall(r'\d+\.\d+(?:\.\d+)?', args)
        if versions:
            new_ver = max(versions, key=version_key)
            if current_am_ver == 'Not specified' or version_key(new_ver) > version_key(current_am_ver):
                return new_ver
    return current_am_ver

def parse_cmake(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        logging.warning(f"Could not read {file_path}: {e}")
        return None, [], []
    content = clean_comment_lines(raw_content)
    # version
    min_req = re.search(r'cmake_minimum_required\s*\(\s*VERSION\s*(\d+\.\d+(?:\.\d+)?)', content, re.I | re.M)
    ver = min_req.group(1) if min_req else None
    # options
    opts = set()
    # option(...)
    for match in re.finditer(r'option\s*\(\s*([a-zA-Z0-9_]+)\s*"(.*?)"\s*(ON|OFF|TRUE|FALSE)\s*\)', content, re.I | re.M):
        opt = match.group(1)
        default = match.group(3).upper()
        opts.add(f'-D{opt}=<ON|OFF> (default {default})')
    # set(... CACHE ...)
    for match in re.finditer(r'set\s*\(\s*([a-zA-Z0-9_]+)\s+([^\s]+)\s*CACHE\s*([a-zA-Z0-9_]+)\s*"(.*?)"', content, re.I | re.M):
        var = match.group(1)
        type_ = match.group(3)
        opts.add(f'-D{var}=<{type_}>')
    # deps
    deps = set()
    for match in re.finditer(r'find_package\s*\(\s*([a-zA-Z0-9_]+)\s*(\d+\.\d+(?:\.\d+)?)?', content, re.I | re.M):
        pkg = match.group(1)
        v = match.group(2) or ''
        deps.add(f'{pkg} {v}'.strip())
    return ver, sorted(opts), sorted(deps)

def parse_meson(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        logging.warning(f"Could not read {file_path}: {e}")
        return None, [], []
    content = clean_comment_lines(raw_content)
    # version
    ver_match = re.search(r'meson_version\s*:\s*[\'\"]\s*([><=]+)?\s*(\d+\.\d+(?:\.\d+)?)', content, re.I | re.M)
    ver = ver_match.group(2) if ver_match else 'Not specified'
    # options - parse option() calls more robustly
    opts = set()
    
    # Find all option() calls - must be standalone (not get_option, set_option etc.)
    # Using negative lookbehind to exclude get_option, set_option etc.
    option_blocks = re.findall(r"(?<![a-z_])option\s*\([^)]+\)", content, re.M | re.S)
    for block in option_blocks:
        # Extract option name - must be a string literal
        name_match = re.search(r"option\s*\(\s*['\"]([a-zA-Z0-9_-]+)['\"]", block)
        if not name_match:
            continue
        opt_name = name_match.group(1)
        
        # Must have a type to be a valid option definition
        type_match = re.search(r"type\s*:\s*['\"]?(boolean|string|combo|array|integer|feature)['\"]?", block, re.I)
        if not type_match:
            continue
        opt_type = type_match.group(1).lower()
        
        # Extract value - handle various formats
        value_match = re.search(r"value\s*:\s*([^,)]+?)(?:\s*,|\s*\))", block)
        if value_match:
            opt_value = value_match.group(1).strip().strip("'\"")
            if opt_value == '':
                opt_value = '<empty>'
        else:
            opt_value = '<default>'
        
        # Extract description
        desc_match = re.search(r"description\s*:\s*['\"]([^'\"]*)['\"]", block)
        opt_desc = desc_match.group(1) if desc_match else ''
        
        # Truncate long values for display with indicator
        if len(opt_value) > 12:
            opt_value = opt_value[:9] + '...'
        
        opts.add(f'{opt_name:<30}{opt_type:<10}{opt_value:<14}{opt_desc}')
    
    # deps with conditional parsing
    lines = raw_content.splitlines()
    current_conditions = []
    deps_dict = {}  # key: dep_base, value: is_optional (False if any required, True if all optional)
    non_linux_terms = ['darwin', 'ios', 'windows', 'cygwin', 'cocoa', 'carbon', 'win32', 'msvc', 'android']
    # Pattern requires dependency name to be quoted to avoid matching variable references like b[0]
    dep_pattern = r'\bdependency\s*\(\s*["\']([a-zA-Z0-9_.+-]+)["\']\s*(?:,\s*version\s*:\s*["\']?([^"\']+)["\']?)?\s*(?:,\s*required\s*:\s*([^,)]+))?\s*(?:,\s*fallback\s*:\s*[^)]*)?'
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('if '):
            current_conditions.append(stripped)
        elif stripped.startswith('elif '):
            if current_conditions:
                current_conditions[-1] = stripped
        elif stripped == 'else':
            if current_conditions:
                current_conditions[-1] = 'else'
        elif stripped.startswith('endif'):
            if current_conditions:
                current_conditions.pop()
        dep_match = re.search(dep_pattern, line)
        if dep_match:
            pkg = dep_match.group(1)
            if 'declare_dependency' in line or pkg in ['link_with', 'sources']:
                continue
            v_raw = dep_match.group(2) or ''
            v = v_raw if re.match(r'[>=<~!0-9. ]', v_raw.strip()) else ''
            required_str = dep_match.group(3) or 'true'
            fallback_match = re.search(r'fallback\s*:\s*\[', line)
            is_internal = fallback_match is not None
            if is_internal:
                continue
            dep_base = f'{pkg} {v}'.strip()
            # Skip non-Linux
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            # is_optional
            required_str_lower = required_str.lower().strip()
            is_optional_this = ('false' in required_str_lower or 'get_option' in required_str_lower or 'auto' in required_str_lower or '.required()' in required_str_lower or '.allowed()' in required_str_lower or '.enabled()' in required_str_lower)
            # Update dict: if any instance is required (not optional), mark as required overall
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
    # Build deps set with tags
    deps = set()
    for dep_base, is_opt in sorted(deps_dict.items()):
        dep_str = dep_base + (' (optional)' if is_opt else '')
        deps.add(dep_str)
    return ver, sorted(opts), sorted(deps)


# Build system file patterns to look for in archives
BUILD_FILE_PATTERNS = {
    'configure.ac', 'configure.in',  # Autotools
    'cmakelists.txt',  # CMake
    'meson.build', 'meson_options.txt', 'meson.options',  # Meson
}

# Additional files that may contain version info for Automake
AUTOMAKE_PATTERNS = {'.am', 'makefile.in', 'makefile'}


def is_tar_archive(path):
    """Check if the path is a tar archive (including compressed variants)."""
    lower_path = path.lower()
    tar_extensions = (
        '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', 
        '.txz', '.tar.zst', '.tar.zstd'
    )
    return any(lower_path.endswith(ext) for ext in tar_extensions)


def get_tar_mode(path):
    """Determine the appropriate tarfile open mode for the archive."""
    lower_path = path.lower()
    if lower_path.endswith('.tar.zst') or lower_path.endswith('.tar.zstd'):
        return 'zstd'  # Special handling for zstd
    elif lower_path.endswith('.tar.xz') or lower_path.endswith('.txz'):
        return 'r:xz'
    elif lower_path.endswith('.tar.bz2') or lower_path.endswith('.tbz2'):
        return 'r:bz2'
    elif lower_path.endswith('.tar.gz') or lower_path.endswith('.tgz'):
        return 'r:gz'
    else:
        return 'r:'  # Plain tar


def open_tar_archive(path):
    """Open a tar archive, handling zstd compression if available.
    
    Returns a tarfile object. The caller is responsible for closing it.
    """
    mode = get_tar_mode(path)
    
    if mode == 'zstd':
        if not ZSTD_AVAILABLE:
            print("Error: zstandard package is required for .tar.zst archives.")
            print("Install it with: pip install zstandard")
            sys.exit(1)
        # Decompress zstd and wrap in tarfile
        # Read entire file to avoid resource leaks with the context manager
        with open(path, 'rb') as f:
            dctx = zstd.ZstdDecompressor()
            # Read and decompress the entire content
            compressed_data = f.read()
            decompressed_data = io.BytesIO(dctx.decompress(compressed_data))
        return tarfile.open(fileobj=decompressed_data, mode='r:')
    else:
        return tarfile.open(path, mode)


def should_extract_file(member_name):
    """Check if a tar member should be extracted for analysis."""
    basename = os.path.basename(member_name).lower()
    
    # Check exact matches for build files
    if basename in BUILD_FILE_PATTERNS:
        return True
    
    # Check patterns for Automake files
    for pattern in AUTOMAKE_PATTERNS:
        if basename.endswith(pattern):
            return True
    
    return False


def is_safe_tar_member(member, base_path="."):
    """Check if a tar member is safe to extract (no path traversal)."""
    # Resolve the absolute path of the member
    member_path = os.path.normpath(os.path.join(base_path, member.name))
    base_abs = os.path.abspath(base_path)
    member_abs = os.path.abspath(member_path)
    
    # Check if the member path is within the base path
    if not member_abs.startswith(base_abs + os.sep) and member_abs != base_abs:
        return False
    
    # Check for suspicious path components
    if member.name.startswith('/') or '..' in member.name.split('/'):
        return False
    
    return True


def extract_build_files_to_memory(tar):
    """Extract build system files from tar archive into memory.
    
    Returns a dict mapping virtual paths to file contents.
    """
    files_content = {}
    
    for member in tar.getmembers():
        if not member.isfile():
            continue
        
        # Security: validate path to prevent path traversal attacks
        if not is_safe_tar_member(member):
            logging.warning(f"Skipping potentially unsafe tar member: {member.name}")
            continue
        
        if should_extract_file(member.name):
            try:
                f = tar.extractfile(member)
                if f is not None:
                    content = f.read()
                    try:
                        files_content[member.name] = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try latin-1 as fallback
                        files_content[member.name] = content.decode('latin-1')
            except (tarfile.TarError, IOError, OSError) as e:
                logging.warning(f"Could not extract {member.name}: {e}")
    
    return files_content


def parse_configure_from_content(content):
    """Parse configure.ac/configure.in content directly from string."""
    raw_content = content
    content_clean = clean_autotools_content(raw_content)
    
    # Autoconf version
    ac_vers = []
    for match in re.finditer(r'AC_PREREQ\s*\(\s*\[?(\d+\.\d+(?:\.\d+)?)\]?\s*\)', content_clean, re.M):
        ac_vers.append(match.group(1))
    ac_ver = max(ac_vers, key=version_key) if ac_vers else 'Not specified'
    
    # Automake version from configure
    am_vers = []
    am_init = re.search(r'AM_INIT_AUTOMAKE\s*\(\s*\[?([^\]]*)\]?\s*\)', content_clean, re.M)
    if am_init:
        args = am_init.group(1)
        vers = re.findall(r'\d+\.\d+(?:\.\d+)?', args)
        am_vers.extend(vers)
    am_ver = max(am_vers, key=version_key) if am_vers else 'Not specified'
    
    # Options (configure switches)
    options = set()
    # Environment variables
    env_vars = set()
    
    # AC_ARG_ENABLE
    for match in re.finditer(r'AC_ARG_ENABLE\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content_clean, re.M):
        feature = match.group(1)
        options.add(f'--enable-{feature}')
        options.add(f'--disable-{feature}')
    
    # AC_ARG_WITH
    for match in re.finditer(r'AC_ARG_WITH\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content_clean, re.M):
        package = match.group(1)
        options.add(f'--with-{package}')
        options.add(f'--without-{package}')
    
    # AC_ARG_VAR
    for match in re.finditer(r'AC_ARG_VAR\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', content_clean, re.M):
        var = match.group(1)
        env_vars.add(var)
    
    # Dependencies parsing
    lines = raw_content.splitlines()
    current_conditions = []
    deps_dict = {}
    non_linux_terms = ['darwin', 'ios', 'windows', 'cygwin', 'cocoa', 'carbon', 'win32', 'msvc', 'android', 'solaris', 'sun', 'bsd', 'next', 'aix', 'hpux', 'osf', 'qnx', 'beos', 'machten', 'rhapsody', 'dgux', 'cray', 'nsk', 'opennt', 'interix', 'openbsd', 'netbsd', 'freebsd', 'dragonfly', 'minix', 'lynxos', 'kfreebsd', 'knetbsd', 'gnu', 'haiku', 'ultrix', 'sco', 'irix', 'newsos', 'os2', 'aux', 'convex', 'mips', 'pyramid', 'univel', 'dynix', 'ekko', 'hiux', 'isc', 'powerux', 'pwux', 'stellar', 'svr4', 'svr3', 'svr2', 'svr1', 'sunos', 'unixware', 'xenix']
    optional_terms = ['with_', 'enable_', 'opt_', 'use_', 'want_']
    skip_terms = ['yes', 'no', 'true', 'false', 'sun', 'dl']
    skip_progs = ['rm', 'cp', 'mv', 'ln', 'cat', 'echo', 'grep', 'sed', 'awk', 'find', 'mkdir', 'chmod', 'chown', 
                  'tar', 'gzip', 'bzip2', 'xz', 'ar', 'ranlib', 'strip', 'install', 'make', 'sh', 'bash',
                  'test', 'expr', 'true', 'false', 'pwd', 'ls', 'touch', 'head', 'tail', 'sort', 'uniq',
                  'cut', 'tr', 'wc', 'diff', 'patch', 'cmp', 'file', 'date', 'env', 'uname', 'which',
                  'dirname', 'basename', 'realpath', 'readlink', 'nm', 'objdump', 'objcopy',
                  'docbook2html', 'docbook2man', 'docbook2pdf', 'docbook2txt', 'xsltproc',
                  'lib.exe', 'link.exe', 'cl.exe', 'ml.exe', 'ml64.exe']
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('if ') or 'test ' in stripped or stripped.startswith('case '):
            current_conditions.append(stripped)
        elif stripped.startswith('fi') or stripped.startswith('esac'):
            if current_conditions:
                current_conditions.pop()
        
        # AC_CHECK_LIB
        match = re.search(r'AC_CHECK_LIB\s*\(\s*\[?([a-zA-Z0-9_-]+)\]?\s*,', line, re.M)
        if match:
            lib = match.group(1)
            if lib.lower() in skip_terms or lib.isupper() or 'FLAGS' in lib or 'LIB' in lib:
                continue
            if lib == 'z':
                lib = 'zlib'
            dep_base = lib
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
        
        # AC_CHECK_PROG
        match = re.search(r'AC_CHECK_PROG\s*\(\s*[^,]+\s*,\s*\[?([a-zA-Z0-9_.-]+)\]?\s*,', line, re.M)
        if match:
            prog = match.group(1)
            if prog.lower() in skip_terms or prog.lower() in skip_progs or prog.isupper() or 'FLAGS' in prog or 'LIB' in prog:
                continue
            dep_base = prog
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
        
        # PKG_CHECK_MODULES
        match = re.search(r'PKG_CHECK_MODULES\s*\(\s*[^,]+\s*,\s*([^)]+)', line, re.M)
        if match:
            modules = match.group(1).strip()
            for spec_match in re.finditer(r'([a-zA-Z0-9_+-]+)(?:\s*([<>=~!]+)\s*([\d.]+))?', modules):
                mod = spec_match.group(1)
                op = spec_match.group(2)
                ver = spec_match.group(3)
                if mod.lower() in skip_terms or mod.isupper() or 'FLAGS' in mod or 'LIB' in mod:
                    continue
                dep_base = f'{mod} {op} {ver}'.strip() if op and ver else mod
                is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
                if is_non_linux:
                    continue
                is_optional_this = any(any(term in cond.lower() for term in optional_terms) for cond in current_conditions)
                if dep_base not in deps_dict:
                    deps_dict[dep_base] = is_optional_this
                else:
                    if not is_optional_this:
                        deps_dict[dep_base] = False
    
    deps = set()
    for dep_base, is_opt in sorted(deps_dict.items()):
        dep_str = dep_base + (' (optional)' if is_opt else '')
        deps.add(dep_str)
    
    return ac_ver, am_ver, sorted(options), sorted(env_vars), sorted(deps)


def parse_automake_from_content(content, current_am_ver):
    """Parse Automake file content directly from string."""
    content_clean = clean_comment_lines(content)
    
    am_options = re.search(r'AUTOMAKE_OPTIONS\s*=\s*([^\n]*)', content_clean, re.M)
    if am_options:
        args = am_options.group(1)
        versions = re.findall(r'\d+\.\d+(?:\.\d+)?', args)
        if versions:
            new_ver = max(versions, key=version_key)
            if current_am_ver == 'Not specified' or version_key(new_ver) > version_key(current_am_ver):
                return new_ver
    return current_am_ver


def parse_cmake_from_content(content):
    """Parse CMakeLists.txt content directly from string."""
    content_clean = clean_comment_lines(content)
    
    min_req = re.search(r'cmake_minimum_required\s*\(\s*VERSION\s*(\d+\.\d+(?:\.\d+)?)', content_clean, re.I | re.M)
    ver = min_req.group(1) if min_req else None
    
    opts = set()
    for match in re.finditer(r'option\s*\(\s*([a-zA-Z0-9_]+)\s*"(.*?)"\s*(ON|OFF|TRUE|FALSE)\s*\)', content_clean, re.I | re.M):
        opt = match.group(1)
        default = match.group(3).upper()
        opts.add(f'-D{opt}=<ON|OFF> (default {default})')
    
    for match in re.finditer(r'set\s*\(\s*([a-zA-Z0-9_]+)\s+([^\s]+)\s*CACHE\s*([a-zA-Z0-9_]+)\s*"(.*?)"', content_clean, re.I | re.M):
        var = match.group(1)
        type_ = match.group(3)
        opts.add(f'-D{var}=<{type_}>')
    
    deps = set()
    for match in re.finditer(r'find_package\s*\(\s*([a-zA-Z0-9_]+)\s*(\d+\.\d+(?:\.\d+)?)?', content_clean, re.I | re.M):
        pkg = match.group(1)
        v = match.group(2) or ''
        deps.add(f'{pkg} {v}'.strip())
    
    return ver, sorted(opts), sorted(deps)


def parse_meson_from_content(content):
    """Parse meson.build content directly from string."""
    raw_content = content
    content_clean = clean_comment_lines(content)
    
    ver_match = re.search(r'meson_version\s*:\s*[\'\"]\s*([><=]+)?\s*(\d+\.\d+(?:\.\d+)?)', content_clean, re.I | re.M)
    ver = ver_match.group(2) if ver_match else 'Not specified'
    
    opts = set()
    option_blocks = re.findall(r"(?<![a-z_])option\s*\([^)]+\)", content_clean, re.M | re.S)
    for block in option_blocks:
        name_match = re.search(r"option\s*\(\s*['\"]([a-zA-Z0-9_-]+)['\"]", block)
        if not name_match:
            continue
        opt_name = name_match.group(1)
        
        type_match = re.search(r"type\s*:\s*['\"]?(boolean|string|combo|array|integer|feature)['\"]?", block, re.I)
        if not type_match:
            continue
        opt_type = type_match.group(1).lower()
        
        value_match = re.search(r"value\s*:\s*([^,)]+?)(?:\s*,|\s*\))", block)
        if value_match:
            opt_value = value_match.group(1).strip().strip("'\"")
            if opt_value == '':
                opt_value = '<empty>'
        else:
            opt_value = '<default>'
        
        desc_match = re.search(r"description\s*:\s*['\"]([^'\"]*)['\"]", block)
        opt_desc = desc_match.group(1) if desc_match else ''
        
        if len(opt_value) > 12:
            opt_value = opt_value[:9] + '...'
        
        opts.add(f'{opt_name:<30}{opt_type:<10}{opt_value:<14}{opt_desc}')
    
    # Dependencies parsing
    lines = raw_content.splitlines()
    current_conditions = []
    deps_dict = {}
    non_linux_terms = ['darwin', 'ios', 'windows', 'cygwin', 'cocoa', 'carbon', 'win32', 'msvc', 'android']
    dep_pattern = r'\bdependency\s*\(\s*["\']([a-zA-Z0-9_.+-]+)["\']\s*(?:,\s*version\s*:\s*["\']?([^"\']+)["\']?)?\s*(?:,\s*required\s*:\s*([^,)]+))?\s*(?:,\s*fallback\s*:\s*[^)]*)?'
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('if '):
            current_conditions.append(stripped)
        elif stripped.startswith('elif '):
            if current_conditions:
                current_conditions[-1] = stripped
        elif stripped == 'else':
            if current_conditions:
                current_conditions[-1] = 'else'
        elif stripped.startswith('endif'):
            if current_conditions:
                current_conditions.pop()
        
        dep_match = re.search(dep_pattern, line)
        if dep_match:
            pkg = dep_match.group(1)
            if 'declare_dependency' in line or pkg in ['link_with', 'sources']:
                continue
            v_raw = dep_match.group(2) or ''
            v = v_raw if re.match(r'[>=<~!0-9. ]', v_raw.strip()) else ''
            required_str = dep_match.group(3) or 'true'
            fallback_match = re.search(r'fallback\s*:\s*\[', line)
            is_internal = fallback_match is not None
            if is_internal:
                continue
            dep_base = f'{pkg} {v}'.strip()
            is_non_linux = any(any(term in cond.lower() for term in non_linux_terms) for cond in current_conditions)
            if is_non_linux:
                continue
            required_str_lower = required_str.lower().strip()
            is_optional_this = ('false' in required_str_lower or 'get_option' in required_str_lower or 'auto' in required_str_lower or '.required()' in required_str_lower or '.allowed()' in required_str_lower or '.enabled()' in required_str_lower)
            if dep_base not in deps_dict:
                deps_dict[dep_base] = is_optional_this
            else:
                if not is_optional_this:
                    deps_dict[dep_base] = False
    
    deps = set()
    for dep_base, is_opt in sorted(deps_dict.items()):
        dep_str = dep_base + (' (optional)' if is_opt else '')
        deps.add(dep_str)
    
    return ver, sorted(opts), sorted(deps)


def analyze_directory(directory):
    """Analyze build systems in a directory.
    
    Returns a dict with all discovered build system information.
    """
    results = {
        'source': directory,
        'type': 'directory',
        'projects': []
    }
    
    # Autotools
    autotools_roots = find_project_roots(directory, ['configure.ac', 'configure.in'])
    for root in autotools_roots:
        config_files_in_root = [os.path.join(root, f) for f in os.listdir(root) if f.lower() in {'configure.ac', 'configure.in'}]
        if not config_files_in_root:
            continue
        config_file = config_files_in_root[0]
        ac_ver, am_ver, opts, env_vars, deps = parse_configure(config_file)
        # am_files under root
        am_files = []
        for r, d, f in os.walk(root):
            for file in f:
                if file.lower().endswith('.am') or file.lower() == 'makefile.in' or file.lower() == 'makefile':
                    am_files.append(os.path.join(r, file))
        for am_file in am_files:
            am_ver = parse_automake(am_file, am_ver)
        
        results['projects'].append({
            'type': 'autotools',
            'path': root,
            'autoconf_version': ac_ver,
            'automake_version': am_ver,
            'options': opts,
            'environment_variables': env_vars,
            'dependencies': deps
        })
    
    # CMake
    cmake_roots = find_project_roots(directory, ['cmakelists.txt'])
    for root in cmake_roots:
        cmake_files = []
        for r, d, f in os.walk(root):
            for file in f:
                if file.lower() == 'cmakelists.txt':
                    cmake_files.append(os.path.join(r, file))
        if not cmake_files:
            continue
        cmake_vers = []
        opts = set()
        deps = set()
        for file in cmake_files:
            ver, file_opts, file_deps = parse_cmake(file)
            if ver:
                cmake_vers.append(ver)
            opts.update(file_opts)
            deps.update(file_deps)
        cmake_ver = max(cmake_vers, key=version_key) if cmake_vers else 'Not specified'
        
        results['projects'].append({
            'type': 'cmake',
            'path': root,
            'cmake_version': cmake_ver,
            'options': sorted(opts),
            'dependencies': sorted(deps)
        })
    
    # Meson
    meson_roots = find_project_roots(directory, ['meson.build'])
    for root in meson_roots:
        meson_files = []
        for r, d, f in os.walk(root):
            for file in f:
                if file.lower() in {'meson.build', 'meson_options.txt', 'meson.options'}:
                    meson_files.append(os.path.join(r, file))
        if not meson_files:
            continue
        meson_vers = []
        opts = set()
        deps = set()
        for file in meson_files:
            ver, file_opts, file_deps = parse_meson(file)
            if ver:
                meson_vers.append(ver)
            opts.update(file_opts)
            deps.update(file_deps)
        meson_ver = max(meson_vers, key=version_key) if meson_vers else 'Not specified'
        
        results['projects'].append({
            'type': 'meson',
            'path': root,
            'meson_version': meson_ver,
            'options': sorted(opts),
            'dependencies': sorted(deps)
        })
    
    return results


def analyze_archive(archive_path):
    """Analyze build systems within a tar archive without extracting to disk.
    
    Returns a dict with all discovered build system information.
    """
    results = {
        'source': archive_path,
        'type': 'archive',
        'projects': []
    }
    
    try:
        tar = open_tar_archive(archive_path)
    except (tarfile.TarError, IOError, OSError) as e:
        logging.error(f"Error opening archive: {e}")
        return results
    
    with tar:
        files_content = extract_build_files_to_memory(tar)
    
    if not files_content:
        return results
    
    # Organize files by their directory structure
    autotools_files = {}
    cmake_files = {}
    meson_files = {}
    automake_files = {}
    
    for path, content in files_content.items():
        basename = os.path.basename(path).lower()
        dirname = os.path.dirname(path)
        
        if basename in {'configure.ac', 'configure.in'}:
            if dirname not in autotools_files:
                autotools_files[dirname] = []
            autotools_files[dirname].append((path, content))
        elif basename == 'cmakelists.txt':
            if dirname not in cmake_files:
                cmake_files[dirname] = []
            cmake_files[dirname].append((path, content))
        elif basename in {'meson.build', 'meson_options.txt', 'meson.options'}:
            if dirname not in meson_files:
                meson_files[dirname] = []
            meson_files[dirname].append((path, content))
        elif basename.endswith('.am') or basename in {'makefile.in', 'makefile'}:
            if dirname not in automake_files:
                automake_files[dirname] = []
            automake_files[dirname].append((path, content))
    
    # Analyze Autotools projects
    for root_dir in sorted(autotools_files.keys()):
        is_subproject = False
        for other_dir in autotools_files.keys():
            if other_dir != root_dir and root_dir.startswith(other_dir + '/'):
                is_subproject = True
                break
        if is_subproject:
            continue
        
        config_content = autotools_files[root_dir][0][1]
        ac_ver, am_ver, opts, env_vars, deps = parse_configure_from_content(config_content)
        
        for am_dir, am_file_list in automake_files.items():
            if am_dir.startswith(root_dir) or am_dir == root_dir:
                for _, am_content in am_file_list:
                    am_ver = parse_automake_from_content(am_content, am_ver)
        
        results['projects'].append({
            'type': 'autotools',
            'path': root_dir,
            'autoconf_version': ac_ver,
            'automake_version': am_ver,
            'options': opts,
            'environment_variables': env_vars,
            'dependencies': deps
        })
    
    # Analyze CMake projects
    for root_dir in sorted(cmake_files.keys()):
        is_subproject = False
        for other_dir in cmake_files.keys():
            if other_dir != root_dir and root_dir.startswith(other_dir + '/'):
                is_subproject = True
                break
        if is_subproject:
            continue
        
        cmake_vers = []
        all_opts = set()
        all_deps = set()
        
        for cmake_dir, cmake_file_list in cmake_files.items():
            if cmake_dir.startswith(root_dir) or cmake_dir == root_dir:
                for _, cmake_content in cmake_file_list:
                    ver, file_opts, file_deps = parse_cmake_from_content(cmake_content)
                    if ver:
                        cmake_vers.append(ver)
                    all_opts.update(file_opts)
                    all_deps.update(file_deps)
        
        cmake_ver = max(cmake_vers, key=version_key) if cmake_vers else 'Not specified'
        
        results['projects'].append({
            'type': 'cmake',
            'path': root_dir,
            'cmake_version': cmake_ver,
            'options': sorted(all_opts),
            'dependencies': sorted(all_deps)
        })
    
    # Analyze Meson projects
    for root_dir in sorted(meson_files.keys()):
        is_subproject = False
        for other_dir in meson_files.keys():
            if other_dir != root_dir and root_dir.startswith(other_dir + '/'):
                is_subproject = True
                break
        if is_subproject:
            continue
        
        meson_vers = []
        all_opts = set()
        all_deps = set()
        
        for meson_dir, meson_file_list in meson_files.items():
            if meson_dir.startswith(root_dir) or meson_dir == root_dir:
                for _, meson_content in meson_file_list:
                    ver, file_opts, file_deps = parse_meson_from_content(meson_content)
                    if ver and ver != 'Not specified':
                        meson_vers.append(ver)
                    all_opts.update(file_opts)
                    all_deps.update(file_deps)
        
        meson_ver = max(meson_vers, key=version_key) if meson_vers else 'Not specified'
        
        results['projects'].append({
            'type': 'meson',
            'path': root_dir,
            'meson_version': meson_ver,
            'options': sorted(all_opts),
            'dependencies': sorted(all_deps)
        })
    
    return results


def print_results(results, output_json=False):
    """Print analysis results in either text or JSON format."""
    if output_json:
        print(json.dumps(results, indent=2))
        return
    
    source = results['source']
    source_type = results['type']
    
    if source_type == 'archive':
        print(f"Analyzing tar archive: {source}")
        print("(Reading directly from archive without extracting to disk)")
        print()
    
    projects = results.get('projects', [])
    
    if not projects:
        if source_type == 'archive':
            print("No build systems (autotools, cmake, meson) found in archive.")
        else:
            print(f"No build systems (autotools, cmake, meson) found in '{source}'.")
        return
    
    for project in projects:
        proj_type = project['type']
        path = project['path']
        
        if proj_type == 'autotools':
            print(f"Autotools project at {path}:")
            print(f"Autoconf version expected: {project['autoconf_version']}")
            print(f"Automake version expected: {project['automake_version']}")
            print("Supported configure switches (sorted):")
            for opt in project['options']:
                print("    " + opt)
            print("Environment variables (sorted):")
            for var in project['environment_variables']:
                print("    " + var)
            print("Dependencies (sorted):")
            for dep in project['dependencies']:
                print("    " + dep)
            print()
        
        elif proj_type == 'cmake':
            print(f"CMake project at {path}:")
            print(f"CMake version expected: {project['cmake_version']}")
            print("Supported options (sorted):")
            for opt in project['options']:
                print("    " + opt)
            print("Dependencies (sorted):")
            for dep in project['dependencies']:
                print("    " + dep)
            print()
        
        elif proj_type == 'meson':
            print(f"Meson project at {path}:")
            print(f"Meson version expected: {project['meson_version']}")
            print("Supported options (sorted):")
            for opt in project['options']:
                print("    " + opt)
            print("Dependencies (sorted):")
            for dep in project['dependencies']:
                print("    " + dep)
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze build systems in a directory or compressed tar archive.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Supported archive formats:
  .tar, .tar.gz, .tgz, .tar.bz2, .tbz2, .tar.xz, .txz
  .tar.zst, .tar.zstd (requires: pip install zstandard)

Examples:
  python build_analyzer.py /path/to/source
  python build_analyzer.py project-1.0.tar.xz
  python build_analyzer.py --json project-1.0.tar.gz
'''
    )
    parser.add_argument('target', help='Directory or tar archive to analyze')
    parser.add_argument('--json', action='store_true', dest='output_json',
                        help='Output results in JSON format for machine-readable output')
    
    args = parser.parse_args()
    
    target = args.target
    
    if not os.path.exists(target):
        print(f"Error: '{target}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    # Check if it's a tar archive
    if os.path.isfile(target) and is_tar_archive(target):
        results = analyze_archive(target)
        print_results(results, args.output_json)
        return
    
    # Otherwise, treat as directory
    if not os.path.isdir(target):
        print(f"Error: '{target}' is not a directory or supported archive.", file=sys.stderr)
        sys.exit(1)
    
    results = analyze_directory(target)
    print_results(results, args.output_json)


if __name__ == "__main__":
    main()