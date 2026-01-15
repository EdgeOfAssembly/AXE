#!/usr/bin/env python3
"""
Create IT abbreviations database for ACP conflict checking.
This populates the database with standard IT/security abbreviations from various sources.
"""

import sqlite3
import os

# Standard IT/security abbreviations to check for conflicts
# Sources: RFC Editor, CWE/CVE, common IT initialisms
STANDARD_ABBREVIATIONS = {
    # Security vulnerabilities
    "BOF": "Buffer Overflow",
    "UAF": "Use After Free",
    "XSS": "Cross-Site Scripting",
    "SQLI": "SQL Injection",
    "CSRF": "Cross-Site Request Forgery",
    "RCE": "Remote Code Execution",
    "LFI": "Local File Inclusion",
    "RFI": "Remote File Inclusion",
    "XXE": "XML External Entity",
    "SSRF": "Server-Side Request Forgery",
    "IDOR": "Insecure Direct Object Reference",
    
    # Development workflow
    "PR": "Pull Request",
    "CI": "Continuous Integration",
    "CD": "Continuous Deployment",
    "MR": "Merge Request",
    "WIP": "Work In Progress",
    
    # Networking
    "TCP": "Transmission Control Protocol",
    "UDP": "User Datagram Protocol",
    "HTTP": "Hypertext Transfer Protocol",
    "HTTPS": "HTTP Secure",
    "DNS": "Domain Name System",
    "IP": "Internet Protocol",
    "MAC": "Media Access Control",
    "TLS": "Transport Layer Security",
    "SSL": "Secure Sockets Layer",
    "VPN": "Virtual Private Network",
    
    # File systems
    "FS": "File System",
    "VFS": "Virtual File System",
    
    # Programming concepts
    "API": "Application Programming Interface",
    "SDK": "Software Development Kit",
    "OOP": "Object-Oriented Programming",
    "FP": "Functional Programming",
    "REPL": "Read-Eval-Print Loop",
    "CLI": "Command Line Interface",
    "GUI": "Graphical User Interface",
    "IDE": "Integrated Development Environment",
    
    # Testing
    "TDD": "Test-Driven Development",
    "BDD": "Behavior-Driven Development",
    "QA": "Quality Assurance",
    
    # Architecture
    "REST": "Representational State Transfer",
    "SOAP": "Simple Object Access Protocol",
    "MVC": "Model-View-Controller",
    "SPA": "Single Page Application",
    
    # Data formats
    "JSON": "JavaScript Object Notation",
    "XML": "Extensible Markup Language",
    "YAML": "YAML Ain't Markup Language",
    "CSV": "Comma-Separated Values",
    
    # Hardware/OS
    "CPU": "Central Processing Unit",
    "GPU": "Graphics Processing Unit",
    "RAM": "Random Access Memory",
    "ROM": "Read-Only Memory",
    "OS": "Operating System",
    "VM": "Virtual Machine",
    
    # Version control
    "VCS": "Version Control System",
    "SCM": "Source Code Management",
    
    # Cryptography
    "AES": "Advanced Encryption Standard",
    "RSA": "Rivest-Shamir-Adleman",
    "SHA": "Secure Hash Algorithm",
    "MD5": "Message Digest 5",
    
    # Binary analysis
    "ELF": "Executable and Linkable Format",
    "PE": "Portable Executable",
    "GOT": "Global Offset Table",
    "PLT": "Procedure Linkage Table",
    "ASM": "Assembly",
    "JMP": "Jump",
    "NOP": "No Operation",
    
    # Memory
    "ASLR": "Address Space Layout Randomization",
    "DEP": "Data Execution Prevention",
    "NX": "No Execute",
    "PIE": "Position Independent Executable",
}


def create_database(db_path: str):
    """Create and populate the IT abbreviations database."""
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create database and table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE abbreviations (
            abbrev TEXT PRIMARY KEY,
            full_form TEXT NOT NULL,
            category TEXT,
            source TEXT
        )
    """)
    
    # Categorize abbreviations
    categories = {
        "security": ["BOF", "UAF", "XSS", "SQLI", "CSRF", "RCE", "LFI", "RFI", "XXE", "SSRF", "IDOR"],
        "workflow": ["PR", "CI", "CD", "MR", "WIP"],
        "networking": ["TCP", "UDP", "HTTP", "HTTPS", "DNS", "IP", "MAC", "TLS", "SSL", "VPN"],
        "filesystem": ["FS", "VFS"],
        "programming": ["API", "SDK", "OOP", "FP", "REPL", "CLI", "GUI", "IDE"],
        "testing": ["TDD", "BDD", "QA"],
        "architecture": ["REST", "SOAP", "MVC", "SPA"],
        "dataformat": ["JSON", "XML", "YAML", "CSV"],
        "hardware": ["CPU", "GPU", "RAM", "ROM", "OS", "VM"],
        "vcs": ["VCS", "SCM"],
        "crypto": ["AES", "RSA", "SHA", "MD5"],
        "binary": ["ELF", "PE", "GOT", "PLT", "ASM", "JMP", "NOP"],
        "memory": ["ASLR", "DEP", "NX", "PIE"],
    }
    
    # Map abbreviations to categories
    abbrev_to_category = {}
    for category, abbrevs in categories.items():
        for abbrev in abbrevs:
            abbrev_to_category[abbrev] = category
    
    # Insert abbreviations
    for abbrev, full_form in STANDARD_ABBREVIATIONS.items():
        category = abbrev_to_category.get(abbrev, "general")
        cursor.execute(
            "INSERT INTO abbreviations (abbrev, full_form, category, source) VALUES (?, ?, ?, ?)",
            (abbrev, full_form, category, "standard")
        )
    
    conn.commit()
    
    # Print statistics
    cursor.execute("SELECT COUNT(*) FROM abbreviations")
    count = cursor.fetchone()[0]
    print(f"Created database with {count} standard IT abbreviations")
    
    # Show sample by category
    print("\nSample abbreviations by category:")
    for category in sorted(set(categories.keys())):
        cursor.execute(
            "SELECT abbrev FROM abbreviations WHERE category = ? LIMIT 3",
            (category,)
        )
        abbrevs = [row[0] for row in cursor.fetchall()]
        print(f"  {category}: {', '.join(abbrevs)}")
    
    conn.close()
    print(f"\nDatabase created at: {db_path}")


if __name__ == "__main__":
    # Create database in data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "it_abbreviations.db")
    create_database(db_path)
