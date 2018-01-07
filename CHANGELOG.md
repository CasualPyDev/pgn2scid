# Changelog
All notable changes to this project will be documented in this file.

## 1.4 - TBA
### Unreleased
- pgn2scid is currently undergoing a major redevelopment and code reorganisation effort. The actual code base (v1.4) is reaching 2000 lines of
code by now and it is still growing. To keep readability and maintainability it requires modularisation
and turning away from the somewhat hacky procedural programming style to OOP. There are also new features
in the pipeline so stay tuned.

## [1.1](https://github.com/CasualPyDev/pgn2scid/releases/tag/v1.1) - 2017-08-23
### Added
- All network errors now cause an entry in the master logfile (pgn2scid_error.log)

### Fixed
- After an interrupted download caused by a network error pgn2scid doesn't save the correct TWIC issue number for the last successfully downloaded file - fixed
- After PGN to Scid conversion pgn2scid displays a summary even when the only converted file has been suspended - fixed
- When pgn2scid runs into a PGN to Scid conversion error for the first time, it creates a 'suspended_pgn_files' folder even when there's no file moved to this folder - fixed

### Changed
- File pgn2scid_manual.pdf updated to rev 1.1.b
- File pgn2scid_win_executable.zip updated to v1.1

## [1.0](https://github.com/CasualPyDev/pgn2scid/releases/tag/v1.0) - 2017-08-04
- Initial release

### Added
- File pgn2scid_manual.pdf rev 1.0.c
- File pgn2scid_win_executable.zip - A Windows executable build from pgn2scid.pyw v1.0
