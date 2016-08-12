====
Pods
====

Creating a Pod
--------------

`Pod`_ is the base entity to run on Kubernetes and merge the entity to Neutron
is maybe the main action that Raven does. Raven watches on pods `events`_ (there
is no more accurate URL on API reference) and reacts accordingly. Basically, the
steps are the following:

1. :command:`User creates a Pod`: When a user creates a Pod, Kubernetes takes
   care of schedule it and spawn the containers that conform a Pod to a Node
   worker.

2. :command:`Raven sees the event`: Raven receives the event of Pod creation,
   then it `creates a port` in Neutron (in the appropriate `namespace network`_)
   and receives the IP address reserved for this port as a response.

3. :command:`Raven updates the Pod`: Then, Raven updates the Kubernetes Pod entity
   (Kubernetes let you write on any of the entities by updating some metadata field)

4. :command:`CNI receives the order of bind the Pod` CNI driver receives the command
   of bind a Pod. This Pod has the information of the Neutron port and hence, the IP
   of the container. CNI driver does the binding.


Due to the asynchronous nature of this actions, it may happen that CNI driver
tries to read the IP address from Pod's metadata but Raven hasn't written yet
the Neutron info. When that happens, CNI driver fails. But K8s API is very
stubborn and will try again, so eventually (in 1 or 2 seconds) the binding will
be done.

To see an illustrative example, let's create a simple Pod that deploys an nginx
server:

.. code-block:: bash

    # STEP 1: User creates a Pod

    apiVersion: v1
    kind: Pod
    metadata:
      name: nginx
      spec:
        containers:
          - name: nginx
            image: nginx

Saving this contents in a file and running:

 | kubectl create -f pod.yaml

That will create a port on neutron, as we can see:

.. code-block:: bash

    # STEP 2: Raven catches the event and creates a port on Neutron

    user@kuryr > neutron port-list --name nginx -c name -c mac_address -c fixed_ips
	+-------+-------------------+------------------------------------------------------------------------------------+
	| name  | mac_address       | fixed_ips                                                                          |
	+-------+-------------------+------------------------------------------------------------------------------------+
	| nginx | fa:16:3e:36:47:de | {"subnet_id": "397f6de9-bee3-4e66-8056-f9e54a7ec5e0", "ip_address": "192.168.0.2"} |
	+-------+-------------------+------------------------------------------------------------------------------------+

Please note that the port name in neutron is the same name as the Pod, it is a handy way to troubleshoot.

Then, we can see that the Pod on Kubernetes API has the metadata according to the Neutron port:

.. code-block:: bash

    # STEP 3: Raven writes Neutron data on kubernetes
    # (Data here was been formatted for a better understanding, don't expect
    # this 'beautiful' output).

    user@kuryr:~ > kubectl get pod nginx -o template --template={{.metadata.annotations}}

	map[kuryr.org/neutron-port:{"admin_state_up": true, "name": "nginx", "port_security_enabled": true, "tenant_id": "253cbc7015b344bb8d31b980fda6fe60",
                                "security_groups": ["04662319-b305-4652-9299-9f517375c880"], "binding:vnic_type": "normal", "device_id": "",
                                "binding:profile": null, "allowed_address_pairs": [], "device_owner": "kuryr:container", "binding:host_id": null,
                                "network_id": "8321a4a7-65f8-4e87-885d-8625549ab51c", "status": "ACTIVE", "id": "b345e440-b9c8-48d8-9d1c-07b91d066b08",
                                "binding:vif_details": {"port_filter": true}, "fixed_ips": [{"ip_address": "192.168.0.2",
                                "subnet_id": "397f6de9-bee3-4e66-8056-f9e54a7ec5e0"}], "binding:vif_type": "midonet", "mac_address": "fa:16:3e:36:47:de"}
    kuryr.org/neutron-subnet:{"name": "default-subnet", "host_routes": [], "tenant_id": "253cbc7015b344bb8d31b980fda6fe60",
                              "allocation_pools": [{"start": "192.168.0.2", "end": "192.168.0.254"}], "cidr": "192.168.0.0/24", "ipv6_ra_mode": null,
                              "gateway_ip": "192.168.0.1", "subnetpool_id": "0928df83-4984-4079-a457-1280a3a65dbe",
                              "network_id": "8321a4a7-65f8-4e87-885d-8625549ab51c", "enable_dhcp": true, "id": "397f6de9-bee3-4e66-8056-f9e54a7ec5e0",
                              "dns_nameservers": [], "ip_version": 4, "ipv6_address_mode": null}]~

Finally, we can check out the container is running and the ip address matches with the Neutorn one:

.. code-block:: bash

    # STEP 4: Container matches the IP with Neutron one looking at pod ip

    user@kuryr > docker exec $(docker ps -f ancestor=nginx -q) ip - 4 a
	1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
	   link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
	   inet 127.0.0.1/8 scope host lo
	   valid_lft forever preferred_lft forever
	   inet6 ::1/128 scope host
	   valid_lft forever preferred_lft forever
	2: gre0@NONE: <NOARP> mtu 1476 qdisc noop state DOWN group default qlen 1
	   link/gre 0.0.0.0 brd 0.0.0.0
	3: gretap0@NONE: <BROADCAST,MULTICAST> mtu 1462 qdisc noop state DOWN group default qlen 1000
	   link/ether 00:00:00:00:00:00 brd ff:ff:ff:ff:ff:ff
	143: eth0@if144: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
	   link/ether fa:16:3e:36:47:de brd ff:ff:ff:ff:ff:ff
	   inet 192.168.0.2/24 scope global eth0
		   valid_lft forever preferred_lft forever
	   inet6 fe80::f816:3eff:fe36:47de/64 scope link
		   valid_lft forever preferred_lft forever

Or you can also look at the pod definition:

.. code-block:: bash

    # STEP 4: Container matches the IP with Neutron one looking at pod ip

	user@kuryr > kubectl get pod nginx -o template --template {{.status.podIP}}
	192.168.0.2


Deleting a Pod
--------------

The Neutron port will be deleted once you remove the Pod:

.. code-block:: bash

	user@kuryr > kubectl delete pod nginx
	pod "nginx" deleted
	user@kuryr > neutron port-list --name nginx -c name -c mac_address -c fixed_ips
	list index out of range

.. _`Pod`: http://kubernetes.io/docs/user-guide/pods/
.. _`events`: http://kubernetes.io/docs/api-reference/v1/operations/
.. _`creates a port`: http://developer.openstack.org/api-ref/networking/v2/index.html#ports
.. _`namespace network`: ./namespaces.html
