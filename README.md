# FUSE

FUSE is a penetration testing system designed to identify Unrestricted
Executable File Upload (UEFU) vulnerabilities. The details of the testing
strategy is in our
[paper](https://wsp-lab.github.io/papers/lee-fuse-ndss20.pdf),
"FUSE: Finding File Upload Bugs via Penetration Testing", which appeared in
NDSS 2020. To see how to configure and execute FUSE, see the followings.

# Setup
## Install

FUSE currently works on Ubuntu 18.04 and Python 2.7.15.

1. Install dependencies
```
# apt-get install rabbitmq-server
# apt-get install python-pip
# apt-get install git
```

2. Clone and build FUSE
```
$ git clone https://github.com/WSP-LAB/FUSE
$ pip install -r requirement.txt
```

* If you plan to leverage headless browser verification using selenium, please
install Chrome and Firefox web driver by refering [selenium
document](https://selenium.dev/selenium/docs/api/py/index.html).

## Usage
### Configuration

* FUSE uses a user-provided [configuration file](configs/default-credential.conf)
that specifies parameters for a target PHP application. The script must be
filled out before testing a target Web application. You can check out
[README](configs/README.md) file and [example configuration files](configs).


* Configuration for File Monitor (Optional)
```
$ vim filemonitor.py

...
 10 MONITOR_PATH='/var/www/html/' <- Web root of the target application
 11 MONITOR_PORT=20174            <- Default port of File Monitor
 12 EVENT_LIST_LIMITATION=8000    <- Maxium number of elements in EVENT_LIST
...
```


### Execution

* FUSE

```
$ python framework.py [Path of configuration file]
```

* File Monitor

```
$ python filemonitor.py
```

* Result
  * When FUSE completes the penetration testing, a [HOST] directory and a [HOST_report.txt] file are created.
  * A [HOST] folder stores files that have been attempted to upload.
  * A [HOST_report.txt] file contains test results and information related to files that trigger U(E)FU.


# Author
This research project has been conducted by [WSP Lab](https://wsp-lab.github.io) at KAIST.

* Taekjin Lee
* [Seongil Wi](https://seongil-wi.github.io/)
* [Suyoung Lee](https://leeswimming.com/)
* [Sooel Son](https://sites.google.com/site/ssonkaist/home)

# Citing FUSE
To cite our paper:
```
@INPROCEEDINGS{lee:ndss:2020,
    author = {Taekjin Lee and Seongil Wi and Suyoung Lee and Sooel Son},
    title = {{FUSE}: Finding File Upload Bugs via Penetration Testing},
    booktitle = {Proceedings of the Network and Distributed System Security Symposium},
    year = 2020
}
```


