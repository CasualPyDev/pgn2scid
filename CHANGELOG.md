# Changelog
All notable changes to this project will be documented in this file.

## [1.8](https://github.com/CasualPyDev/pgn2scid/releases/tag/1.8) - 2021-09-19

### Changed
- User-Agent request header added
- Windows executable pgn2scid.exe updated to v1.8

## [1.7](https://github.com/CasualPyDev/pgn2scid/releases/tag/1.7) - 2020-04-19

### Changed
- HTML parser rewritten to make it more robust
- file required.txt added to resolve external library dependencies
- File pgn2scid_manual.pdf updated to rev. 1.7b (extended installation details added to reflect the fact that pgn2scid uses
external libraries as of version 1.7)
- File pgn2scid_win_amd64_executable.zip updated to v1.7

## 1.6.1 - 2020-01-12

### Fixed
- Fixed an uncritical but slightly annoying bug which causes a blanked out working directory or database
input field when clicking on "Cancel" in the related dialog box.

### Changed
- File pgn2scid_manual.pdf updated to rev. 1.6.a
- File pgn2scid_win_amd64_executable.zip updated to v1.6.1

## 1.5 - 2019-09-07

### Fixed
- Fixed a bug which creates a folder 'zip_files' although there's nothing to copy into it.

### Changed
- File pgn2scid_manual.pdf updated to rev 1.5.a
- File pgn2scid_win_amd64_executable.zip updated to v1.5

## 1.4 - 2019-07-10

### Added
- When there's a new version available pgn2scid now opens a notification window on start up

### Changed
- Some internal changes to enable secure https data transfer
- File pgn2scid_manual.pdf updated to rev 1.4.d
- File pgn2scid_win_amd64_executable.zip updated to v1.4

## 1.3 - 2019-05-05
### Fixed
- Fixed a bug which, under certain circumstances, caused an unecessary
'No ZIP files found to decompress' message in the message window

### Changed
- File pgn2scid_manual.pdf updated to rev 1.3.a
- File pgn2scid_win_amd64_executable.zip updated to v1.3

## 1.2 - 2018-12-16
### Fixed
- Fixed a problem with nested ZIP files
- pgn2sicd now ignores hidden MAC OSX folders (__MACOSX) in ZIP files because they can
cause some trouble in the unzip routine on non MAC machines
- New icon set with transparent background to fix some visual problems

### Changed
- File pgn2scid_manual.pdf updated to rev 1.2.a
- File pgn2scid_win_executable.zip updated to v1.2

## 1.1 - 2017-08-23
### Added
- All network errors now cause an entry in the master logfile (pgn2scid_error.log)

### Fixed
- After an interrupted download caused by a network error pgn2scid doesn't save the correct TWIC issue number for the last successfully downloaded file - fixed
- After PGN to Scid conversion pgn2scid displays a summary even when the only converted file has been suspended - fixed
- When pgn2scid runs into a PGN to Scid conversion error for the first time, it creates a 'suspended_pgn_files' folder even when there's no file moved to this folder - fixed

### Changed
- File pgn2scid_manual.pdf updated to rev 1.1.b
- File pgn2scid_win_executable.zip updated to v1.1

## 1.0 - 2017-08-04
- Initial release

### Added
- File pgn2scid_manual.pdf rev 1.0.c
- File pgn2scid_win_executable.zip - A Windows executable build from pgn2scid.pyw v1.0
