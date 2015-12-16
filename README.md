# VOPaaS

VOPaaS is a lightweight proxy used as a bridge between a SAML2int Service Providers and a number of 
identity providers such as Facebook, google and SAML2int IdP's.

# Architectural overview

![](images/VOPaaS_overview.png "VOPaaS overview image")

1. The client SP sends a request  
1. The proxy connects to the requested identity provider and receives user infomation 
1. The proxy connects to a account linking service 
1. The proxy connects to a consent manager service 
1. The returned user info attributes which where returned from the 
service provider and for which the user has given consent will be sent to the SP


![](images/VOPaaS_proxy_internals.png "VOPaaS internal communication")

1. Service provider makes request to proxy. At a specific url which specifies which identity it want to use
1. The frontend module is responsible to convert to incoming request to the internal representation 
1. The internal request is passed on the the router
1. The internal request is routed to the right backend based on the url to which the Service provider sent the request
1. The backend converts the request from internal data to external request 
1. The backend send the request and receives user info
1. The backend converts the external response to internal data
1. Then the information is passed on to the account linking module 
1. The account linking module contacts the account linking service by a REST API
1. The information is then passed on to the consent manager
1. The consent manager contacts the consent manager service 
1. The info is passed on to the router 
1. By using a state object the router can determine which frontend module should receive the response
1. The internal data is the converted to a SAML2 int response.
1. The response is returned to the service provider 

![](images/vopaas_consent_comunication.png "VOPaaS internal communication")

1. Verifies if consent was given for a given SP, IdP and set of attributes

    1.1 If no consent where given the requested attributes, a redirect URL and some information 
    about the Service provider will be stored and a ticket will be generated
    
    1.2 Send ticket to show consent page
1. If consent where given the consent service will redirect back to the proxy 


![](images/vopaas_AL_comunication.png "VOPaaS internal communication")

1. Request unique identifier for a given user in combination with a identity provider
    1. If a link between the user and identity provider does NOT exists a ticket is returned to the proxy
        1. Create link between the user and identity provider
        1. Restart flow
    1. If a link between the user and identity provider exists an UUID is returned

# Installation

1. Download this repository as a [zip file](https://github.com/its-dirg/vopaas_ansible/archive/master.zip).
1. All configuration files are located in **TODO add skeleton configuration files somewhere in vopaas_ansible**
1. Modify all necessary parameters, described in [Configuration](configuration).
1. Run `ansible-playbook` **TODO specify command to run and describe example inventory?**
1. **TODO Should SP's/backing IdP's read metadata from URL? (in that case we really should let a proper webserver (nginx or Apache) serve static files).
1. **TODO specify location of generated frontend/backend metadata or make location configurable in Ansible**


# Configuration

See the [SATOSA configuration instructions](https://github.com/its-dirg/SATOSA/tree/master/doc).

## SAML2 frontend
**TODO how should SP metadata be handled in production? can VOPaaS reload the specified metadata file at certain intervals or should we use MDX or something else?, see `metadata` param in table below**

**TODO should there be any default "attribute_restrictions"?**
**TODO is the default assertion lifetime reasonable?**

## Backend configuration

### SAML2 backend

**TODO how should IdP metadata be handled in production? can VOPaaS reload the specified metadata file at certain intervals or should we use MDX or something else?, see `metadata` param in table below**

### Social login backends

#### Facebook

**TODO set sane defaults for `fields` in vopaas example/default FB config**

## Statistics micro service

To collect anonymous statistics about which SP and IdP combination the end users use in the [statistics service](https://github.com/its-dirg/vopaas_statistics), the statistics micro service must be configured in VOPaaS.

Configuration parameters:

| Parameter name | Data type | Example values | Description |
| -------------- | --------- | -------------- | ----------- |
| `module` | string | `vopaas.micro_service.statistics_service.StatisticsService` | the python micro service module to import |
| `plugin` | string | `ResponseMicroService` | whether this is a response or a request micro service | 
| `config.rest_uri` | string | `https://127.0.0.1:8168` | url to the REST endpoint of the service |
| `config.signing_key` | string | `pki/statistics.key` | path to key used for signing the request to the service |
| `config.verify_ssl` | bool | `No` | whether the HTTPS certificate of the service should be verified when doing requests to it |

# Service Provider requirements

* Technical requirement: Any SP connecting to the proxy must provide an `mdui:DisplayName` in the metadata. **TODO can we expect this or should we have a fallback when fetching the `requester_name` to send to the consent service?**


# Metadata

In addition to generating the proxy metadata with the [SATOSA `make_saml_metadata.py` script](https://github.com/its-dirg/SATOSA/tree/master/doc#metadata), 
metadata for all backends must be generated to mirror the backing providers defined in the backend
plugins.

## Generate proxy frontend metadata
The script **make_vopaas_metadata.py \<proxy_config_path\>** will generate metadata files for the 
proxy frontend. Each file represents one of the target IDP/OP and contains some gui information 
about the original IDP/OP.
In the case of IDP, the gui information is retrieved from the IDPs original metadata. For OP, the
information is manually added in the openid backend configuration and is retrieved by the script.

### Arguments to script:
positional arguments:

    proxy_config_path

optional arguments:

    -h, --help  show this help message and exit
    -v VALID    How long, in days, the metadata is valid from the time of
              creation
    -c CERT     certificate
    -i ID       The ID of the entities descriptor
    -k KEYFILE  A file with a key to sign the metadata with
    -n NAME
    -s          sign the metadata
    -x XMLSEC   xmlsec binaries to be used for the signing
    -o OUTPUT   Where to write metadata files

# State

The VOPaaS adds the following additional information to the [SATOSA state cookie](https://github.com/its-dirg/SATOSA/blob/master/doc/internals/state.md): 

## Frontends

### VOPaaSSamlFrontend

* **proxy_idp_entityid**: Which entity id the proxy will answer as, when sending the authentication 
response back to the calling SP.
* **relay_state**: The relay state given by the SP request
* **resp_args.in_response_to**: The id of the request
* **resp_args.binding**: Which binding type to use
* **resp_args.sp_entity_id**: Entity id of the calling SP
* **resp_args.name_id_policy**: The SAML2 name id policy

## Backends

### VOPaaSSamlBackend

Only saves the relay state for the backend-IDP request.

### VOPaaSOpenIdBackend
TODO

### VOPaaSOFacebookBackend
TODO
