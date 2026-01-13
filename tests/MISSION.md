# AXE Test Mission

This is a test mission file used for token detection tests.

## Purpose

This file is used to verify that reading documentation files does not trigger
false positive token detection in the AXE system.

## Test Scenarios

1. File reading should not trigger break request detection
2. File reading should not trigger emergency detection
3. File reading should not trigger spawn detection
4. File reading should not trigger task complete detection

## Notes

- All tokens mentioned in documentation should be safe
- Result blocks protect against false positives
- This file intentionally contains no action tokens
