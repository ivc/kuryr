# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from kuryr.schemata import commons

REQUEST_ADDRESS_SCHEMA = {
    u'links': [{
        u'method': u'POST',
        u'href': u'/IpamDriver.RequestAddress',
        u'description': u'Allocate an ip addresses',
        u'rel': u'self',
        u'title': u'Create'
    }],
    u'title': u'Create an IP',
    u'required': [u'PoolID', u'Address', u'Options'],
    u'definitions': {u'commons': {}},
    u'$schema': u'http://json-schema.org/draft-04/hyper-schema',
    u'type': u'object',
    u'properties': {
        u'PoolID': {
            u'description': u'neutron uuid of allocated subnetpool',
            u'$ref': u'#/definitions/commons/definitions/uuid'
        },
        u'Address': {
            u'description': u'Prefered address in regular IP form.',
            u'example': u'10.0.0.1',
            u'$ref': u'#/definitions/commons/definitions/ipv4_or_ipv6'
        },
        u'Options': {
            u'type': [u'object', u'null'],
            u'description': u'Options',
            u'example': {}
        }
    }

}

REQUEST_ADDRESS_SCHEMA[u'definitions'][u'commons'] = commons.COMMONS
