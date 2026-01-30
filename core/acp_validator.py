"""
ACP Validator for Agent Communication Protocol.
Validates custom abbreviations against standard IT/security terminology database
to prevent conflicts with well-known abbreviations.
"""
import sqlite3
import os
from typing import Dict, List, Optional
from pathlib import Path
class ACPValidator:
    """Validates custom abbreviations against IT standards database."""
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the ACP Validator.
        Args:
            db_path: Path to IT abbreviations database.
                    Defaults to data/it_abbreviations.db relative to project root.
        """
        if db_path is None:
            # Default to data/it_abbreviations.db in project root
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "it_abbreviations.db"
        self.db_path = str(db_path)
        self._conn: Optional[sqlite3.Connection] = None
    def _get_connection(self) -> sqlite3.Connection:
        """Lazy load database connection."""
        if self._conn is None:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(
                    f"IT abbreviations database not found at {self.db_path}. "
                    "Run data/create_abbreviations_db.py to create it."
                )
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
    def conflicts_with_standard(self, abbrev: str) -> bool:
        """
        Check if abbreviation conflicts with any IT standard.
        Args:
            abbrev: Abbreviation to check (case-insensitive)
        Returns:
            True if abbreviation conflicts with a standard term, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        # Case-insensitive check
        cursor.execute(
            "SELECT COUNT(*) FROM abbreviations WHERE UPPER(abbrev) = UPPER(?)",
            (abbrev,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    def get_standard_meaning(self, abbrev: str) -> Optional[str]:
        """
        Get the standard meaning of an abbreviation if it exists.
        Args:
            abbrev: Abbreviation to lookup
        Returns:
            Full form of the abbreviation, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_form FROM abbreviations WHERE UPPER(abbrev) = UPPER(?)",
            (abbrev,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    def validate_custom_abbreviations(self, custom: Dict[str, str]) -> List[str]:
        """
        Validate custom abbreviations against standard IT terms.
        Args:
            custom: Dictionary mapping custom abbreviations to their meanings
        Returns:
            List of conflicting abbreviations (those that conflict with standards)
        """
        conflicts = []
        for abbrev in custom.keys():
            if self.conflicts_with_standard(abbrev):
                standard_meaning = self.get_standard_meaning(abbrev)
                conflicts.append(
                    f"{abbrev} (conflicts with standard: {standard_meaning})"
                )
        return conflicts
    def get_all_standard_abbreviations(self) -> Dict[str, str]:
        """
        Get all standard abbreviations from the database.
        Returns:
            Dictionary mapping abbreviations to their full forms
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT abbrev, full_form FROM abbreviations")
        return {row[0]: row[1] for row in cursor.fetchall()}
    def close(self):
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
    def __enter__(self):
        """Context manager entry."""
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()