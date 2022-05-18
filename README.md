<h3 align="center">PowerManWolAgent</h3>

---

<p align="center"> An agent which wakes LAN devices according to messages posted to a queue.
    <br> 
</p>

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Built Using](#built_using)
- [Authors](#authors)

## About <a name = "about"></a>

A little python script and associated Docker bits to monitor an Azure Storage Account Queue for messages instructing it to wake another host on the network. Can be easily adapted to handle other types of messages. Using Docker for portability.

## Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

- A Docker environment. I used one running on Ubuntu 20.10
- An Azure Subscription with a Storage Account provisioned

### Installing

The following assumes working from one Windows system running two terminal windows; one SSH'd to the Linux system running Docker, the other a local PowerShell session. Adapt as required.

From the Linux system, clone this project to a location suitable to run the Docker container

Create a self signed certificate which will be used to authenticate the script to the Storage Account and allow it to process Queue messages 

```
openssl req -x509 -newkey rsa:2048 -subj '/CN=powermanwolagent' -keyout key.pem -out cert.pem -sha256 -days 365 -nodes
openssl x509 -in cert.pem -text
```

Copy the Base64 certificate to the clipboard i.e. everything between but not including "-----BEGIN CERTIFICATE-----" and "-----END CERTIFICATE-----".

From the PowerShell session construct a certificate object from the clipboard data

```
$certBase64 = Get-clipboard
$certObject = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new([System.Convert]::FromBase64String($certBase64))
```

Connect to Azure and create a new Service Principal to allow certificate based authentication

```
Connect-AzAccount
$sp = New-AzADServicePrincipal -DisplayName 'powermanwolagent-sp' -CertValue $certData -StartDate $certObject.NotBefore -EndDate $certObject.NotAfter
```

Get the Storage Account object, create a new Queue and get the Queue ID

```
$storageAccount = Get-AzStorageAccount -Name 'mystorageaccount' -ResourceGroupName 'MyResourceGroup'
$storageContext = New-AzStorageContext -StorageAccountName $storageAccount.StorageAccountName
$queue = New-AzStorageQueue -Context $storageContext -Name 'powermanwolagentqueue'
$queueId = "$($storageAccount.Id)/queueServices/default/queues/$($queue.Name)"
```

Create a role assignment for the service principal to allow the script to process Queue messages

```
New-AzRoleAssignment -ApplicationId $sp.AppId -RoleDefinitionName 'Storage Queue Data Message Processor' -Scope $queueId
```

On the Linux system, run the following from the project directory. This network configuration is to allow the container to send WOL messages directly to the Ethernet network on a Docker host with multiple VLAN interfaces. Adapt as required

```
docker build --tag powermanwolagent .
docker network create -d macvlan --gateway 192.168.1.1 --subnet 192.168.1.0/24 --ip-range 192.168.1.240/29 -o parent=vlan_network powermanwolagent_net
docker run -d --network powermanwolagent_net --dns 192.168.1.1  powermanwolagent
```

## Usage <a name="usage"></a>

Write a message to the Queue in the format replacing the MAC address:

```
{
  "type": "wol",
  "mac": "aa:bb:cc:dd:ee:ff"
}
```

## Built Using <a name = "built_using"></a>

- [Azure](https://azure.microsoft.com/)
- [Python](https://www.python.org/)
- [Docker](https://www.docker.com/)

## Authors <a name = "authors"></a>

- [@lukewegener](https://github.com/lukewegener)
