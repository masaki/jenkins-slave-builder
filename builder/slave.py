import logging
import json
import requests
import xml.etree.ElementTree as ET

from builder.utils import camelize


class Slave():
    """
    Slave node model
    """
    log = logging.getLogger(__name__)

    fields = [ 'name', 'description', 'executors', 'remote_fs', 'labels', 'mode' ]

    create_params_mapping = {
        "name"       : [ 'name',            lambda x:x ],
        "description": [ 'nodeDescription', lambda x:x ],
        "executors"  : [ 'numExecutors',    lambda x:x ],
        "remote_fs"  : [ 'remoteFS',        lambda x:x ],
        "labels"     : [ 'labelString',     lambda x:" ".join(x) ],
        "mode"       : [ 'mode',            lambda x:x.upper() ],
    }

    update_params_mapping = {
        "name"       : [ 'name',         lambda x:x ],
        "description": [ 'description',  lambda x:x ],
        "executors"  : [ 'numExecutors', lambda x:x ],
        "remote_fs"  : [ 'remoteFS',     lambda x:x ],
        "labels"     : [ 'label',        lambda x:" ".join(x) ],
        "mode"       : [ 'mode',         lambda x:x.upper() ],
    }

    launcher_mapping = {
        "jnlp": {
            "class": 'hudson.slaves.JNLPLauncher',
            "keys":  ['tunnel', 'vmargs'],
        },
        "command": {
            "class": 'hudson.slaves.CommandLauncher',
            "keys":  ['command'],
        },
        "ssh": {
            "class": 'hudson.plugins.sshslaves.SSHLauncher',
            "keys":  [
                'host',
                'port',
                'private_key',
                'credentials_id',
                'java_path',
                'jvm_options',
                'prefix_start_slave_cmd',
                'suffix_start_slave_cmd',
                'launch_timeout_seconds',
                'max_num_retries',
                'retry_wait_time',
            ],
        },
        "windows": {
            "class": 'hudson.os.windows.ManagedWindowsServiceLauncher',
            "keys":  ['user_name', 'password', 'host', 'java_path', 'vmargs'],
        },
    }

    def __init__(self, params={}, jenkins={}):
        self.construct_params(params)
        self.construct_launcher_params(params['launcher'])
        self.construct_jenkins_params(jenkins)

    def construct_params(self, params={}):
        default_params = {
            "description": "Automatically created through jenkins-slave-builder",
            "executors":   2,
            "remote_fs":   "/tmp",
            "labels":      [],
            "mode":        "normal",
        }

        default_params.update(params)
        self.params = default_params

    def construct_launcher_params(self, params={}):
        launcher = self.launcher_mapping[ params['type'].lower() ]
        self.launcher_class = launcher['class']

        launcher_params = {}
        for key in launcher['keys']:
            if params.has_key(key) and params[key]:
                launcher_params[key] = params[key]
        self.launcher_params = launcher_params

    def construct_jenkins_params(self, params={}):
        self.jenkins = params


    def name(self):
        return self.params['name']

    def authinfo(self):
        return (self.jenkins['user'], self.jenkins['password'])


    def check_url(self):
        url = "%s/computer/%s/api/json" % (self.jenkins['url'], self.name())
        return url

    def create_url(self):
        url = "%s/computer/doCreateItem" % self.jenkins['url']
        return url

    def update_url(self):
        url = "%s/computer/%s/config.xml" % (self.jenkins['url'], self.name())
        return url


    def is_already_created(self):
        res = requests.head(self.check_url(), auth=self.authinfo())
        return res.status_code == requests.codes.ok

    def create_or_update(self):
        if self.is_already_created():
            self.log.info("Slave '%s' already exists." % self.name())
            self.update()
        else:
            self.create()


    def create(self):
        # launcher
        launcher_params = { "stapler-class": self.launcher_class }
        for k,v in self.launcher_params.items():
            launcher_params[camelize(k)] = v

        # JSON includes launcher
        json_params = {
            "type": 'hudson.slaves.DumbSlave$DescriptorImpl',
            "retentionStrategy": {
                "stapler-class": 'hudson.slaves.RetentionStrategy$Always',
            },
            "nodeProperties": {
                "stapler-class-bag": 'true',
            },
            "launcher": launcher_params,
        }
        for f in self.fields:
            if self.params.has_key(f):
                value = self.params[f]
                key, fn = self.create_params_mapping[f]
                json_params[key] = fn(value)

        payload = {
            "name": self.params['name'],
            "type": 'hudson.slaves.DumbSlave$DescriptorImpl',
            "json": json.dumps(json_params), # serialize to JSON
        }
        self.log.debug(payload)

        # create endpoint accepts POST with x-www-form-urlencoded
        res = requests.post(self.create_url(), data=payload, auth=self.authinfo())

        status = 'Success' if res.status_code == requests.codes.ok else 'Failure'
        self.log.info("Creating slave '%s' ... %s" % (self.name(), status))


    def update(self):
        # get config.xml before update
        self.log.debug("Get slave '%s' config.xml" % self.name())
        res = requests.get(self.update_url(), auth=self.authinfo())
        self.log.debug(res.text)
        xml = ET.fromstring(res.text)

        # update core fields
        for f in self.fields:
            key, fn = self.update_params_mapping[f]
            elem = xml.find(key)
            if elem is not None and self.params.has_key(f):
                value = str(fn(self.params[f]))
                if elem.text != value:
                    self.log.debug("Update field '%s': '%s' => '%s'" % (key, elem.text, value))
                    elem.text = value

        # update launcher fields
        launcher = xml.find('launcher')
        for k,v in self.launcher_params.items():
            key = self.fixup_update_launcher_key(k)
            elem = launcher.find(key)
            if elem is not None:
                value = str(v)
                self.log.debug("Update launcher field '%s': '%s' => '%s'" % (key, elem.text, value))
                elem.text = value

        self.log.debug(ET.tostring(xml))

        header = { 'Content-Type': 'application/xml' }
        body = ET.tostring(xml)
        res = requests.post(self.update_url(), data=body, headers=header, auth=self.authinfo())

        status = 'Success' if res.status_code == requests.codes.ok else 'Failure'
        self.log.info("Updating slave '%s' ... %s" % (self.name(), status))

    def fixup_update_launcher_key(self, key):
        fixed_key = camelize(key)
        if key is 'command':
            fixed_key = 'agentCommand'
        return fixed_key
