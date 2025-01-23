# Change Log
All the major changes of the Batch GPS Importer are documented in this file.

## [1.1.0] - 2025-01-26

### Fixed
- **Dynamic Help**: Dynamic help not showing contents fixed.
- **Fields imported**: Fixed missing fields when importing.

### Changed
- **User Interface**: Change Projection to GPX Coordinate System, Geometry Type to Output Geometry Type, Layer Name to Output Layer Name.
- **User Interface**: Reordered inputs
- **Fields imported**: Data types are now recognized as Double for elevation, QDateTime for date and String for the rest.

## [1.0.1] - 2020-01-26

### Fixed
- **Help**: Fixed help file not loading in the help window.

## [1.0.0] - 2018-09-21

### Changed
- **Plugin**: Changed the Plugin Python version to Python 3.x and the QGIS to 3.x.


## [0.2.0] - 2017-06-27

### Added
- **Language**: Added Russian Language. Thank you very much, Nikolai!
- **GPX Feature Identification**: Creates separate features for each group of tracks and routes in the same file.
- **File search**: Added fields to search using file prefix and suffix.

### Fixed
- **Encoding**: Fixed encoding issue for non-English languages.


## [0.1.1] - 2017-04-04

### Changed
- **Documentation**: Enabled the English dynamic and static help for non-English languages.
- **Documentation-Dynamic Help**: Customized the static help to also serve as dynamic help file.
