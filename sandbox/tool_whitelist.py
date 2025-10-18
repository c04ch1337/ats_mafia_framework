"""
Tool Whitelist and Command Validation
Defines approved security tools and validates commands for safety.
"""

import re
from typing import Dict, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)

# Approved security tools by category
APPROVED_TOOLS: Dict[str, List[str]] = {
    'reconnaissance': [
        'nmap', 'masscan', 'dnsenum', 'whois', 'dig', 'host',
        'traceroute', 'ping', 'nslookup', 'netdiscover', 'arp-scan',
        'enum4linux', 'smbclient', 'smbmap', 'nbtscan'
    ],
    'exploitation': [
        'msfconsole', 'msfvenom', 'searchsploit', 'sqlmap',
        'hydra', 'medusa', 'exploit', 'auxiliary'
    ],
    'web_testing': [
        'nikto', 'dirb', 'gobuster', 'wpscan', 'wfuzz',
        'burpsuite', 'zaproxy', 'commix', 'ffuf', 'dirbuster'
    ],
    'wireless': [
        'aircrack-ng', 'airodump-ng', 'aireplay-ng',
        'wifite', 'reaver', 'bully', 'wash'
    ],
    'forensics': [
        'volatility', 'autopsy', 'foremost', 'binwalk',
        'strings', 'exiftool', 'steghide', 'dd'
    ],
    'password': [
        'john', 'hashcat', 'crunch', 'cewl', 'medusa',
        'hydra', 'ophcrack', 'rainbowcrack'
    ],
    'sniffing': [
        'wireshark', 'tshark', 'tcpdump', 'ettercap',
        'dsniff', 'urlsnarf', 'webspy'
    ],
    'enumeration': [
        'enum4linux', 'ldapsearch', 'ldapdomaindump',
        'rpcclient', 'rpcinfo', 'showmount'
    ],
    'vulnerability_scanning': [
        'nessus', 'openvas', 'nikto', 'wpscan',
        'nuclei', 'skipfish'
    ],
    'utilities': [
        'cat', 'grep', 'sed', 'awk', 'find', 'ls',
        'head', 'tail', 'wc', 'sort', 'uniq', 'cut',
        'tr', 'less', 'more', 'file', 'which', 'whereis'
    ]
}

# Dangerous commands that should be blocked
DANGEROUS_COMMANDS: Set[str] = {
    'rm', 'rmdir', 'mv', 'dd', 'mkfs', 'fdisk',
    'parted', 'format', 'shutdown', 'reboot', 'init',
    'kill', 'killall', 'pkill', 'chmod', 'chown',
    'useradd', 'userdel', 'passwd', 'su', 'sudo',
    '>', '>>', '&', '&&', '||', ';', '|',
    '$(', '`', 'eval', 'exec', 'source', '.'
}

# Dangerous patterns in commands
DANGEROUS_PATTERNS: List[str] = [
    r'/dev/',  # Device files
    r'/proc/',  # Process information
    r'/sys/',  # System information
    r'\.\.',  # Directory traversal
    r'\\x',  # Hex escape sequences
    r'%[0-9a-f]{2}',  # URL encoding
    r'\$\(',  # Command substitution
    r'`.*`',  # Backtick command execution
    r'>\s*/dev',  # Redirecting to device files
    r'nc\s+-[el]',  # Netcat listening
    r'bash\s+-i',  # Interactive bash
    r'/bin/[sb]h',  # Shell executables
]

# Safe parameter patterns for common tools
SAFE_PARAMETERS: Dict[str, List[str]] = {
    'nmap': [
        r'-sS', r'-sT', r'-sU', r'-sA', r'-sW', r'-sN',
        r'-p\s*\d+', r'-p\s*\d+-\d+', r'-F', r'-r',
        r'-O', r'-A', r'-v', r'-vv', r'-Pn', r'--script',
        r'-oN', r'-oX', r'-oG', r'--top-ports'
    ],
    'sqlmap': [
        r'-u\s+https?://', r'--dbs', r'--tables', r'--columns',
        r'--dump', r'-D\s+\w+', r'-T\s+\w+', r'-C\s+\w+',
        r'--batch', r'--level=\d', r'--risk=\d'
    ],
    'hydra': [
        r'-l\s+\w+', r'-L\s+[\w/\.]+', r'-p\s+\w+', r'-P\s+[\w/\.]+',
        r'-s\s+\d+', r'-t\s+\d+', r'-v', r'-V', r'-f', r'-F'
    ],
    'nikto': [
        r'-h\s+[\w\.:]+', r'-p\s+\d+', r'-ssl', r'-Tuning',
        r'-Display', r'-output', r'-Format'
    ],
    'metasploit': [
        r'use\s+\w+', r'set\s+\w+', r'show\s+\w+',
        r'exploit', r'search', r'info'
    ]
}


def get_all_approved_tools() -> List[str]:
    """Get flattened list of all approved tools."""
    tools = set()
    for category_tools in APPROVED_TOOLS.values():
        tools.update(category_tools)
    return sorted(list(tools))


def is_tool_approved(tool: str) -> bool:
    """
    Check if a tool is in the approved list.
    
    Args:
        tool: Name of the tool to check
        
    Returns:
        True if tool is approved, False otherwise
    """
    all_tools = get_all_approved_tools()
    return tool.lower() in [t.lower() for t in all_tools]


def get_tool_category(tool: str) -> str:
    """
    Get the category of an approved tool.
    
    Args:
        tool: Name of the tool
        
    Returns:
        Category name or 'unknown'
    """
    for category, tools in APPROVED_TOOLS.items():
        if tool.lower() in [t.lower() for t in tools]:
            return category
    return 'unknown'


def validate_command(command: str) -> Tuple[bool, str]:
    """
    Validate a command for safety before execution.
    
    Args:
        command: The command string to validate
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if not command or not command.strip():
        return False, "Empty command"
    
    command = command.strip()
    
    # Extract the base tool name
    tool_name = command.split()[0].split('/')[-1]
    
    # Check if tool is approved
    if not is_tool_approved(tool_name):
        return False, f"Tool '{tool_name}' is not in approved whitelist"
    
    # Check for dangerous commands
    command_lower = command.lower()
    for dangerous_cmd in DANGEROUS_COMMANDS:
        if dangerous_cmd in command_lower:
            return False, f"Dangerous command pattern detected: '{dangerous_cmd}'"
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous pattern detected: {pattern}"
    
    # Check for command chaining/injection attempts
    if any(char in command for char in ['&&', '||', ';', '`', '$(']):
        return False, "Command chaining/injection detected"
    
    # Check for file redirection (except to /tmp)
    if re.search(r'>>\s*(?!/tmp/)', command) or re.search(r'>\s*(?!/tmp/)', command):
        return False, "File redirection to non-tmp directory not allowed"
    
    # Validate specific tool parameters if available
    if tool_name in SAFE_PARAMETERS:
        # At least one safe parameter should be present
        has_safe_param = False
        for safe_pattern in SAFE_PARAMETERS[tool_name]:
            if re.search(safe_pattern, command):
                has_safe_param = True
                break
        
        if not has_safe_param:
            logger.warning(f"No recognized safe parameters found for {tool_name}")
    
    # Additional checks for high-risk tools
    if tool_name in ['msfconsole', 'msfvenom', 'metasploit']:
        # Ensure no reverse shell creation
        if re.search(r'(reverse_tcp|reverse_https|meterpreter)', command, re.IGNORECASE):
            if not re.search(r'LHOST\s*=\s*172\.(20|25)\.', command):
                return False, "Metasploit payloads must target internal training network only"
    
    if tool_name == 'dd':
        # dd is dangerous but sometimes needed for forensics
        if not re.search(r'if=.*of=/tmp/', command):
            return False, "dd command must read from file and write to /tmp only"
    
    return True, "Command validated successfully"


def sanitize_command(command: str) -> str:
    """
    Sanitize a command by removing potentially dangerous elements.
    
    Args:
        command: The command to sanitize
        
    Returns:
        Sanitized command string
    """
    # Remove shell metacharacters
    sanitized = re.sub(r'[;&|`$()]', '', command)
    
    # Remove multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def build_safe_command(tool: str, target: str, options: Dict[str, str] = None) -> Tuple[str, bool]:
    """
    Build a safe command with validated parameters.
    
    Args:
        tool: Name of the tool
        target: Target IP/hostname
        options: Optional parameters
        
    Returns:
        Tuple of (command_string, is_safe)
    """
    if not is_tool_approved(tool):
        return "", False
    
    # Validate target is an IP or safe hostname
    if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target) and \
       not re.match(r'^[a-zA-Z0-9\-\.]+$', target):
        return "", False
    
    # Build command
    cmd_parts = [tool]
    
    # Add options based on tool
    if options:
        for key, value in options.items():
            # Sanitize each parameter
            safe_key = re.sub(r'[^a-zA-Z0-9\-_]', '', key)
            safe_value = re.sub(r'[^a-zA-Z0-9\-_\.:/]', '', str(value))
            cmd_parts.append(f"{safe_key} {safe_value}")
    
    cmd_parts.append(target)
    command = ' '.join(cmd_parts)
    
    # Validate the built command
    is_valid, reason = validate_command(command)
    
    if is_valid:
        return command, True
    else:
        logger.warning(f"Built command failed validation: {reason}")
        return "", False


# Export public API
__all__ = [
    'APPROVED_TOOLS',
    'get_all_approved_tools',
    'is_tool_approved',
    'get_tool_category',
    'validate_command',
    'sanitize_command',
    'build_safe_command',
]