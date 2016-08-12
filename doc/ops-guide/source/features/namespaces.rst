==========
Namespaces
==========

According to `official documentation`_, Namespaces are "support for multiple
virtual clusters backed in the same physical cluster".

Based to this definition, a Kubernetes namespaces could be mapped into either a
Neutron tenant or a Neutron network. Since Kubernetes already have
`authenticating configuration`_ options that can be backed by `keystone`_, (and
that could lead to a more specific multitenancy support) and since the Kuryr
project works on network support for Kubernetes, we chose the later.

More specifically, every namespace on Kubernetes is mapped in a Neutron network
and a subnet (more details later). When you create a `Pod`_ inside a namespace,
that `Pod`_ will take an IP of the corresponding Neutron subnet.

Creating a Namespace
--------------------

Creating a Namespace implies the same steps described on `Pod`_ guide, except
the CNI part:

1. :command:`User creates a Namespace`: When a Kubernetes user creates a
   Namespace, it just creates the entity on `etcd`_.

2. :command:`Raven sees the event`: Raven, who is listening on Namespaces' API
   endpoint, creates `a network`_ and `a subnet`_ in Neutron. Subnet takes its
   range from the *cluster-subnet-pool* configuration option and after that it
   attaches a new interface on the *raven-default-router* (See `Getting Started`_
   document for more info about these values)

3. :command:`Raven updates the Namespace`: Then, Raven updates the Kubernetes
   Namespace entity with data about Neutron network and Neutron subnet.

A namespace is a very trivial Kubernetes object, it only needs a name. For the
sake of a good demo, we will create two on the same yaml file.

.. code-block:: bash

    # STEP 1: create two namespaces

    apiVersion: v1
    kind: Namespace
    metadata:
      name: ops-guide1
    ---
    apiVersion: v1
    kind: Namespace
    metadata:
      name: ops-guide2

Copy the contents of this block on a file and run the following command:

 | kubectl create -f namespace.yaml

Once we have created the namespace, the matching rules on Neutron are:

1. :command:`There is a new network with the namespace name`
2. :command:`There is a new subnet with the namespace name+'subnet' suffix`: The
   CIDR belongs to range taken from the `subnetpool` called *raven-default-pool*
   and configured with the option *cluster-subnet-pool*
3. :command:`There is a new interface on the raven router with the previous subnet`

Let's check it:

.. code-block:: bash

    # STEP 2: Raven has created entities on Neutron for ops-guide1

    ~ user@kuryr > neutron net-list -c name -c subnets
    +------------+-----------------------------------------------------+
    | name       | subnets                                             |
    +------------+-----------------------------------------------------+
    | ops-guide1 | cfd92fbc-51d5-4fca-a550-f76ad7018b6f 192.168.1.0/24 |
    | ops-guide2 | 191369dc-609a-11e6-835b-0021ccb7a292 192.168.2.0/24 |
    +------------+-----------------------------------------------------+
    ~ user@kuryr > neutron subnetpool-list
    +--------------------------------------+--------------------+----------------+-------------------+
    | id                                   | name               | prefixes       | default_prefixlen |
    +--------------------------------------+--------------------+----------------+-------------------+
    | 0928df83-4984-4079-a457-1280a3a65dbe | raven-default-pool | 192.168.0.0/16 | 24                |
    +--------------------------------------+--------------------+----------------+-------------------+
    ~ user@kuryr > neutron subnet-list --name ops-guide1-subnet -c name -c cidr
    +-------------------+----------------+
    | name              | cidr           |
    +-------------------+----------------+
    | ops-guide1-subnet | 192.168.1.0/24 | # As you can see, they are subranges of the previous subnetpool!
    | ops-guide2-subnet | 192.168.2.0/24 |
    +-------------------+----------------+
    ~ user@kuryr > neutron router-port-list raven-default-router --fixed_ips subnet_id=$(neutron subnet-list --name ops-guide1-subnet -c id -f value) -c fixed_ips
    +------------------------------------------------------------------------------------+
    | fixed_ips                                                                          |
    +------------------------------------------------------------------------------------+
    | {"subnet_id": "cfd92fbc-51d5-4fca-a550-f76ad7018b6f", "ip_address": "192.168.1.1"} |
    +------------------------------------------------------------------------------------+
    ~ user@kuryr > neutron router-port-list raven-default-router --fixed_ips subnet_id=$(neutron subnet-list --name ops-guide2-subnet -c id -f value) -c fixed_ips
    +------------------------------------------------------------------------------------+
    | fixed_ips                                                                          |
    +------------------------------------------------------------------------------------+
    | {"subnet_id": "191369dc-609a-11e6-835b-0021ccb7a292", "ip_address": "192.168.2.1"} |
    +------------------------------------------------------------------------------------+

We can check the metadata annotations of the Kubernetes Namespaces now:

.. code-block:: bash

    # STEP 3: Raven writes on namespace object metadata
    # (Data here was been formatted for a better understanding, don't expect
    # this 'beautiful' output).

    user@kuryr > kubectl get namespace
    NAME         STATUS    AGE
    default      Active    90d
    ops-guide1   Active    38m
    ops-guide2   Active    38m

    user@kuryr > kubectl get namespace ops-guide1 -o template --template={{.metadata.annotations}}

    map[kuryr.org/neutron-network:
        {"status": "ACTIVE", "admin_state_up": true, "name": "ops-guide1", "port_security_enabled": true,
         "id": "0a6273a7-c4bb-44c4-a1ef-6a5829e48502", "tenant_id": "253cbc7015b344bb8d31b980fda6fe60",
         "router:external": false, "shared": false, "subnets": []}
        kuryr.org/neutron-subnet:
        {"name": "ops-guide1-subnet", "host_routes": [], "tenant_id": "253cbc7015b344bb8d31b980fda6fe60",
         "allocation_pools": [{"start": "192.168.1.2", "end": "192.168.1.254"}], "cidr": "192.168.1.0/24",
         "ipv6_ra_mode": null, "gateway_ip": "192.168.1.1", "subnetpool_id": "0928df83-4984-4079-a457-1280a3a65dbe",
         "network_id": "0a6273a7-c4bb-44c4-a1ef-6a5829e48502", "enable_dhcp": true,
         "id": "cfd92fbc-51d5-4fca-a550-f76ad7018b6f", "dns_nameservers": [], "ip_version": 4, "ipv6_address_mode": null}]


At this point we can say that the Namespace has been created successfully.

Pod connectivity between Namespaces
-----------------------------------

Although NetworkPolicy (which uses Isolated Namespaces) `merged`_ on v1.3 as
experimental, in this version we use non-isolated Namespaces. That means all the
Pods are able to see each other on different namespaces without restrictions.

In terms of implementation, we use the `default` Security Group on Neutron that
allows unrestricted access between them.

To see it working, we can use the example (and the file) on `Pod`_\s section but
specifying the namespaces recently created.

.. code-block:: bash

    user@kuryr > kubectl --namespace ops-guide1 create -f pod.yaml
    pod "nginx" created
    user@kuryr > kubectl --namespace ops-guide2 create -f pod.yaml
    pod "nginx" created
    user@kuryr > kubectl get --namespace ops-guide2 pod nginx -o template --template={{.status.podIP}}
    192.168.2.2
    user@kuryr > kubectl get --namespace ops-guide1 pod nginx -o template --template={{.status.podIP}}
    192.168.1.2

As you can see, the Pods have IPs on different /24 subnets, the ones created by each namespace.
From one you should be able to access to the other:

.. code-block:: bash

    user@kuryr > kubectl exec --namespace ops-guide1 nginx -- ping -c 1 192.168.2.2
    PING 192.168.2.2 (192.168.2.2): 56 data bytes
    64 bytes from 192.168.2.2: icmp_seq=0 ttl=63 time=9.380 ms
    --- 192.168.2.2 ping statistics ---
    1 packets transmitted, 1 packets received, 0% packet loss
    round-trip min/avg/max/stddev = 9.380/9.380/9.380/0.000 ms


Deleting Namespaces
-------------------

Delete a namespace deletes the namespace and the pods inside. That means that
Raven will delete the neutron network and the ports associated to it:

.. code-block:: bash

    user@kuryr > neutron net-list --name ops-guide2
    +--------------------------------------+------------+-----------------------------------------------------+
    | id                                   | name       | subnets                                             |
    +--------------------------------------+------------+-----------------------------------------------------+
    | 89e8f21e-0d6e-4e2c-ac68-4e8cfe857fc5 | ops-guide2 | 4ffaac8a-0d3d-4d70-b480-9ecf81067598 192.168.2.0/24 |
    +--------------------------------------+------------+-----------------------------------------------------+
    user@kuryr > neutron port-list --fixed_ips ip_address=192.168.2.2
    +--------------------------------------+-------+-------------------+------------------------------------------------------------------------------------+
    | id                                   | name  | mac_address       | fixed_ips                                                                          |
    +--------------------------------------+-------+-------------------+------------------------------------------------------------------------------------+
    | 9730604b-8ea9-4b0a-88af-bb5fda4a50f5 | nginx | fa:16:3e:0b:2c:31 | {"subnet_id": "4ffaac8a-0d3d-4d70-b480-9ecf81067598", "ip_address": "192.168.2.2"} |
    +--------------------------------------+-------+-------------------+------------------------------------------------------------------------------------+

    user@kuryr > kubectl delete namespace ops-guide2  # here we delete the namespace
    namespace "ops-guide2" deleted

    # Neutron entities not anymore
    user@kuryr > neutron port-list --fixed_ips ip_address=192.168.2.2
    list index out of range
    user@kuryr > neutron net-list --name ops-guide2
    list index out of range

.. _`official documentation`: http://kubernetes.io/docs/user-guide/namespaces/
.. _`authenticating configuration`: http://kubernetes.io/docs/admin/authentication/
.. _`keystone`: https://github.com/kubernetes/kubernetes/issues/11626
.. _`Getting Started`: ../getting_started.html
.. _`Pod`: ./pods.rst
.. _`a network`: http://developer.openstack.org/api-ref/networking/v2/#networks
.. _`a subnet`: http://developer.openstack.org/api-ref/networking/v2/#subnets
.. _`etcd`: http://kubernetes.io/docs/admin/etcd/
.. _`merged`: https://github.com/kubernetes/kubernetes/pull/25638
