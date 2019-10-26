# OpenCast Downloader

If your university uses OpenCast for lecture videos and you're looking for a simple-to-use downloader so you can save these lecture videos to your mobile devices and use them on the go, this tool is for you!

## Prerequisites

To use this tool, you will need Python 3 on your system with the `requests` module installed. (If the module is missing from your Python installation, it will be installed automatically.)

## Usage

The Python script is run by `./oc_download.py` or `python3 oc_download.py`. It offers an interactive menu, however, by specifying all of the appropriate optional flags, you can run this script unattended. For options, please refer to the help output:

    usage: oc_download.py [-h] [-U URL] [-u USERNAME] [-p PASSWORD]
                        [-o OUTPUT_DIRECTORY] [-r RESOLUTION] [-s SERIES] [-ls]
                        [-le] [-e EPISODES] [-pr] [-pn]

    Downloads videos from an OpenCast sever.

    optional arguments:
    -h, --help            Display this help message and exit.
    -v, --version         Display version info and exit.
    -U URL, --url URL     URL of the OpenCast server.
    -u USERNAME, --username USERNAME
                            Username for the OpenCast server.
    -p PASSWORD, --password PASSWORD
                            Password for the OpenCast server.
    -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                            Download directory for videos.
    -r RESOLUTION, --resolution RESOLUTION
                            Resolution string to match. (The value "max"
                            automatically selects the maximum resolution.)
    -s SERIES, --series SERIES
                            String to match for series titles.
    -ls, --list-series    List available series and exit.
    -le, --list-episodes  List available episodes. (Can be used with --series.)
    -e EPISODES, --episodes EPISODES
                            String to match for episode titles, use "all" to
                            download all.
    -pr, --presenter      Download presenter videos.
    -pn, --presentation   Download presentation videos.

## Authors
* **Sora Steenvoort**

## Note

So far, this tool has only been successfully tested for the OpenCast server of Ruhr University Bochum - your mileage may vary. If the tool doesn't work for you, please file a bug report and include the appropriate data.

## Acknowledgements

Thanks to StackOverflow's **FogleBird** for a [code snippet for parsing numerical ranges](https://stackoverflow.com/a/6405228) and the **Django** project for a [code snippet for creating safe file names](https://github.com/django/django/blob/master/django/utils/text.py).
