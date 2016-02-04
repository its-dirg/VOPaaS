# VOPaaS

VOPaaS is a lightweight proxy used as a bridge between a SAML2int Service Providers and a number of 
identity providers such as Facebook, google and SAML2int IdP's.

# Architectural overview
In this section the some describing the VOPaaS application on different levels

##Service communications
![](images/VOPaaS_overview.png "VOPaaS overview image")

1. The client SP sends a request to a specific URL which specifies which identity provider it wants to communicate with.
1. The proxy connects to the requested identity provider and receives user information 
1. The proxy connects to a account linking service 
1. The proxy connects to a consent manager service 
1. The returned user info attributes which where returned from the 
service provider and for which the user has given consent will be sent to the SP

##Internal components
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

##SP view
![](images/vopaas_sp_view.png "VOPaaS SP view")

The service provider does not know that it's actually talking to a proxy. It only knows about the identity providers.

##Consent
![](images/vopaas_consent_comunication.png "Consent communication")

1. Verifies if consent was given for a given SP, IdP and set of attributes

    1.1 If no consent where given the requested attributes, a redirect URL and some information 
    about the Service provider will be stored and a ticket will be generated
    
    1.2 Send ticket to show consent page
1. If consent where given the consent service will redirect back to the proxy 

##Account linking
![](images/vopaas_AL_comunication.png "Account linking communication")

1. Request unique identifier for a given user in combination with a identity provider
    1. If a link between the user and identity provider does NOT exists a ticket is returned to the proxy
        1. Create link between the user and identity provider
        1. Restart flow
    1. If a link between the user and identity provider exists an UUID is returned

<br>
<br>

# Installation

In order to make the installation easier a separate project which uses ansible in order to install tha VOPaaS proxy has been created. For more information visit:
https://github.com/its-dirg/vopaas_ansible

1. Download this repository as a [zip file](https://github.com/its-dirg/vopaas_ansible/archive/master.zip).
1. Install dependencies:
```
pip install -e .
pip install -r requirements.txt
```
1. Example configuration files are located in the example folder
1. Modify all necessary parameters, described in [Configuration](#configuration) section below.
1. In order to start the application run:
```
gunicorn -b<socket address> satosa.wsgi:app --keyfile=<https key> --certfile=<https cert>
```

<br>
<br>

# Configuration

See the [SATOSA configuration instructions](https://github.com/its-dirg/SATOSA/tree/master/doc#configuration).

NOTE: Make sure that the **module** attribute in the frontend configuration file is set 
to **satosa.frontends.saml2.SamlMirrorFrontend**

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

<br>
<br>

# Metadata

For more information on how to generate metadata which mirrors all the identity providers 
defined in the backend plugins visit
[SATOSA proxy doc](https://github.com/its-dirg/SATOSA/blob/master/doc/README.md#saml_metadata), 


<br>
<br>

# Run proxy
For more infomation on how to start the proxy please visit:
[SATOSA proxy doc](https://github.com/its-dirg/SATOSA/blob/master/doc/README.md#run), 

<br>
<br>

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
