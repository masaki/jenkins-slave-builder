jenkins-slave-builder
=====================

jenkins-slave-builder is a command line tool for managing jenkins slaves with yaml files and back your slaves with SCM.

Installation
---

Install jenkins-slave-builder at a system level or in an isolated virtualenv by running the following command:

        pip install jenkins-slave-builder

Usage
---

See sample yaml files under sample/ directory.

jenkins-slave-builder needs a jenkins config file which tells it how to connect to jenkins. The config file looks like this

        [jenkins]
        user=user
        password=password
        url=http[s]://jenkinsurl

Once that is ready, we are all set to create the slave in jenkins using the following command

        jenkins-slave-builder update --conf=/path/to/jenkins.conf /path/to/slaves.yaml
