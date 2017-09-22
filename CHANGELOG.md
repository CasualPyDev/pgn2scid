# Changelog
All notable changes to this project will be documented in this file.

## 1.1 - 2017-08-19
### Added
- All network errors now cause an entry in the master logfile (pgn2scid_error.log)

### Fixed
- After an interrupted download caused by a network error pgn2scid don't save the correct TWIC issue number for the last successfuly downloaded file - fixed
- After PGN to Scid conversion pgn2scid displays a summary even when the only converted file has been suspended - fixed
- When pgn2scid runs into a PGN to Scid conversion error for the first time, it creates a 'suspended_pgn_files' folder even when there's no file moved to this folder - fixed

### Changed
- File pgn2scid_manual.pdf updated to rev 1.1.a
- File pgn2scid_win_executable.zip updated to v1.1

## 1.0 - 2017-08-04
- initial release

### Added
- File pgn2scid_manual.pdf rev 1.0.c
- File pgn2scid_win_executable.zip - A Windows executable build from pgn2scid.pyw v1.0
