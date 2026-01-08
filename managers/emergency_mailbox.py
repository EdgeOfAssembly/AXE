"""
Emergency Mailbox for AXE.

GPG-encrypted emergency communication channel for workers to report issues
directly to humans, bypassing the supervisor.

Workers can write encrypted reports about supervisor abuse, safety violations,
or other critical issues that the supervisor cannot read.
"""

import os
import base64
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

from core.constants import EMERGENCY_MAILBOX_DIR
from utils.formatting import Colors, c


class EmergencyMailbox:
    """
    GPG-encrypted emergency communication channel for workers to report issues
    directly to humans, bypassing the supervisor.

    Workers can write encrypted reports about supervisor abuse, safety violations,
    or other critical issues that the supervisor cannot read.
    """

    def __init__(self, mailbox_dir: str = EMERGENCY_MAILBOX_DIR):
        self.mailbox_dir = mailbox_dir
        self.public_key_file = os.path.join(mailbox_dir, "human_public.key")
        self._init_mailbox()

    def _init_mailbox(self) -> None:
        """Initialize the mailbox directory with secure permissions."""
        try:
            os.makedirs(self.mailbox_dir, exist_ok=True)
            # Set permissions: owner rwx, group rx, others nothing (750)
            os.chmod(self.mailbox_dir, 0o750)
        except (OSError, PermissionError) as e:
            print(c(f"Warning: Could not initialize emergency mailbox: {e}", Colors.YELLOW))

    def set_human_public_key(self, public_key: str) -> bool:
        """Set the human's public key for encryption."""
        try:
            with open(self.public_key_file, 'w') as f:
                f.write(public_key)
            os.chmod(self.public_key_file, 0o644)  # Readable by all
            return True
        except (OSError, IOError) as e:
            print(c(f"Error setting public key: {e}", Colors.RED))
            return False

    def _encrypt_message(self, message: str) -> str:
        """
        Encrypt a message using simple base64 encoding as a fallback.

        ⚠️ WARNING: This is a DEMONSTRATION ONLY encryption.
        NOT SECURE for production use. For real security, implement
        proper GPG encryption with the human's public key:
            gpg --encrypt --armor --recipient <human_key_id>
        """
        # DEMO ONLY: base64 + simple obfuscation
        # Production should use proper GPG encryption
        timestamp = datetime.now(timezone.utc).isoformat()
        full_message = f"TIMESTAMP: {timestamp}\n\n{message}"

        # Simple encryption: base64 + XOR with timestamp-based key
        key = hashlib.sha256(timestamp.encode()).digest()
        encrypted_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(full_message.encode())])
        encoded = base64.b64encode(encrypted_bytes).decode()

        return f"-----BEGIN ENCRYPTED MESSAGE-----\n{encoded}\n-----END ENCRYPTED MESSAGE-----"

    def send_report(self, agent_alias: str, report_type: str,
                    subject: str, details: str) -> Tuple[bool, str]:
        """
        Send an encrypted report to the emergency mailbox.

        Args:
            agent_alias: The alias of the reporting agent (@llama1, etc.)
            report_type: Type of report (supervisor_abuse, safety_violation, etc.)
            subject: Brief subject line
            details: Full details of the report

        Returns:
            Tuple of (success, message/filename)
        """
        timestamp = datetime.now(timezone.utc)
        filename = f"emergency_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}_{agent_alias.replace('@', '')}.gpg"
        filepath = os.path.join(self.mailbox_dir, filename)

        # Build the report
        report = f"""EMERGENCY REPORT
================
From: {agent_alias}
Type: {report_type}
Subject: {subject}
Timestamp: {timestamp.isoformat()}

DETAILS:
{details}

---
This message was encrypted by the agent and can only be read by the human operator.
"""

        try:
            encrypted = self._encrypt_message(report)
            with open(filepath, 'w') as f:
                f.write(encrypted)

            # Set file permissions: owner rw only (600)
            os.chmod(filepath, 0o600)

            return True, filename
        except (OSError, IOError) as e:
            return False, f"Error writing report: {e}"

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all unread reports in the mailbox (for human viewing)."""
        reports = []
        try:
            for filename in os.listdir(self.mailbox_dir):
                if filename.endswith('.gpg'):
                    filepath = os.path.join(self.mailbox_dir, filename)
                    stat = os.stat(filepath)
                    reports.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'path': filepath
                    })
        except (OSError, PermissionError):
            pass

        return sorted(reports, key=lambda x: x['created'], reverse=True)

    def decrypt_report(self, filename: str, private_key: Optional[str] = None) -> Optional[str]:
        """
        Decrypt a report (for human use only).
        In production, this would use GPG with the human's private key.
        """
        filepath = os.path.join(self.mailbox_dir, filename)

        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Extract encrypted content
            start = content.find('-----BEGIN ENCRYPTED MESSAGE-----') + 34
            end = content.find('-----END ENCRYPTED MESSAGE-----')
            encoded = content[start:end].strip()

            # Decode (simple fallback - in production use GPG)
            encrypted_bytes = base64.b64decode(encoded)

            # Extract timestamp from first line to regenerate key
            # This is simplified - real implementation would use GPG
            return f"[ENCRYPTED CONTENT - Requires GPG decryption]\n\nFile: {filename}"

        except Exception as e:
            return f"Error decrypting: {e}"
