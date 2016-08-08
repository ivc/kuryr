===============
Getting Started
===============

Neutron topology
----------------

This section discusses the Neutron entities that Raven creates when it spawns
(in case they don't exist).

When you configured Kuryr-Kubernetes, you did see the following section:

.. code-block:: bash

    [k8s]

    #
    # From kuryr
    #

    # (string value)
    #api_root = http://localhost:8080

    # Subnet pool used to grab ranges of IPs for each new K8s namespace. Pod IPs
    # will be inside those ranges (string value)
    cluster_subnet_pool = 192.168.0.0/16

    # Network range of the Floating IPs used when creating services with externalIP
    # access. (string value)
    cluster_external_subnet = 172.16.0.0/16

    # Range of IPs used as K8s ClusterIPs. It must match with Kubernetes
    # SERVICE_CLUSTER_IP_RANGE (string value)
    cluster_service_subnet = 10.0.0.0/24

These values define basically the range of IPs of the Pods, the externalIPs and the
VIPs of the Kubernetes entities.

* :command:`cluster_subnet_pool`: You'll see in more detail in the
  `namespaces`_ section, but basically it defines the Neutron `subnetpool`_ from
  where we will pick the namespaces' networks. The network names will be based
  on namespaces names.

* :command:`cluster_external_subnet`: `public services`_ can define
  `externalIPs`_ addresses to let external access to Kubernetes services. This
  option define what's the range of this `externalIPs`_. The network name will be
  (not configurable yet) *raven-default-external-net*

* :command:`cluster_service_subnet`: This is the range of VIPs that K8s gives
  to services. This value **MUST MATCH** with Kubernetes configuration option
  `SERVICE_CLUSTER_IP_RANGE`_ when is deployed. The network name will be (not
  configurable yet) *raven-default-service*


As network topology, this is traduced to:

.. code-block:: bash

        `raven-default-external-net`
        ------------+---------------
                    |
                    |
        +-----------+-------------+
        |   raven-default-router  |
        +--+----------+--------+--+
           |          |        |           net-1 (range taken from `cluster_subnet_pool`)
           |          |   +----+----------------------------------------------------------+
           |          |
           |          |       net-2 (range taken from `cluster_subnet_pool`)
           |     +----+-----------------------------------------------------------------+
           |
           |      `raven-default-service`
        ---+------------------------------------------------------------------+

Or, if you prefer to see it on Neutron commands:

.. code-block:: bash

	happyuser@kuryr:~ > neutron net-list -c name -c subnets
	+----------------------------+-----------------------------------------------------+
	| name                       | subnets                                             |
	+----------------------------+-----------------------------------------------------+
	| default                    | 29f5df27-427e-4282-8fb1-b8b64a152575 192.168.0.0/24 |
	| raven-default-service      | 1610fb22-d8e1-4de9-8896-adc542699157 10.0.0.0/24    |
	| raven-default-external-net | 1f2a9589-2b7b-444e-a6cc-a9fb88f4f75c 172.16.0.0/16  |
	+----------------------------+-----------------------------------------------------+
	happyuser@kuryr:~ > neutron router-list -c name
	+----------------------+
	| name                 |
	+----------------------+
	| raven-default-router |
	+----------------------+
	happyuser@kuryr:~ > neutron router-port-list raven-default-router -c fixed_ips
	+------------------------------------------------------------------------------------+
	| fixed_ips                                                                          |
	+------------------------------------------------------------------------------------+
	| {"subnet_id": "29f5df27-427e-4282-8fb1-b8b64a152575", "ip_address": "192.168.0.1"} |
	| {"subnet_id": "1f2a9589-2b7b-444e-a6cc-a9fb88f4f75c", "ip_address": "172.16.0.2"}  |
	| {"subnet_id": "1610fb22-d8e1-4de9-8896-adc542699157", "ip_address": "10.0.0.1"}    |
	+------------------------------------------------------------------------------------+
	happyuser@kuryr:~ > neutron subnet-list -c name -c cidr
	+-------------------------------+----------------+
	| name                          | cidr           |
	+-------------------------------+----------------+
	| default-subnet                | 192.168.0.0/24 |
	| raven-default-10.0.0.0/24     | 10.0.0.0/24    |
	| raven-default-external-subnet | 172.16.0.0/16  |
	+-------------------------------+----------------+


All this topology will not be created if it is created already with the same
names. As pointed out on `limitations`_ section, there is no way to reuse any
current network or subnet right now.

You could, though, give access to already created networks (that probably will have Virtual
Machines running on it) by `adding a router interface`_ attaching that network to the
*raven-default-router* manually.


.. _`namespaces`: ./features/namespaces.html
.. _`limitations`: ./limitations.html
.. _`subnetpool`: http://developer.openstack.org/api-ref/networking/v2-ext/index.html#subnet-pools-extension-subnetpools
.. _`public services`: ./features/services.html
.. _`externalIPs`: http://kubernetes.io/docs/user-guide/services/#external-ips
.. _`SERVICE_CLUSTER_IP_RANGE`: http://kubernetes.io/docs/getting-started-guides/scratch/#network
.. _`adding a router interface`: http://developer.openstack.org/api-ref/networking/v2-ext/index.html#layer-3-networking-routers-floatingips
