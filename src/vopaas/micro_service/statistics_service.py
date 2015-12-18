"""
Micro service module for sending statistics to a statistics service.
"""
import json
import logging
from jwkest.jwk import rsa_load, RSAKey
from jwkest.jws import JWS
import requests
from satosa.context import Context
from satosa.internal_data import InternalResponse
from satosa.logging_util import satosa_logging
from satosa.micro_service.service_base import ResponseMicroService

LOGGER = logging.getLogger(__name__)


class StatisticsService(ResponseMicroService):
    """
    Micro service that sends statistics to a statistic service
    """

    def __init__(self, config: dict) -> None:
        """
        :param config: service config
        """

        super(StatisticsService, self).__init__()
        self.config = config
        self.stat_uri = config["rest_uri"]
        self.verify_ssl = config["verify_ssl"] if "verify_ssl" in config else False

        _bkey = rsa_load(config["signing_key"])
        self.sign_key = RSAKey().load_key(_bkey)
        self.sign_key.use = "sig"

    def process(self, context: Context, data: InternalResponse) -> InternalResponse:
        """
        :param context: The current context
        :param data: Internal response from backend
        """
        # Send stat to service
        try:
            ticket = self._get_ticket()
            self._register(data.to_requestor, data.auth_info.issuer, ticket)
        except requests.ConnectionError as e:
            satosa_logging(LOGGER, logging.ERROR, "Could not connect to the statistics service '{}'".format(self.stat_uri), context.state)
        except Exception as e:
            satosa_logging(LOGGER, logging.ERROR, "Could not connect to the statistics service '{}'".format(self.stat_uri), context.state, exc_info=True)

        return data

    def _register(self, sp: str, idp: str, ticket: str) -> None:
        """
        Registers the statistic
        :param sp: sp id
        :param idp: idp id
        :param ticket: ticket given by statistics service
        """
        data = {"sp": sp, "idp": idp, "ticket": ticket}
        jws = self._to_jws(data)

        request = "{}/register/{}".format(self.stat_uri, jws)
        res = requests.post(request, verify=self.verify_ssl)

        assert res.status_code == 200, "Bad status code: {}".format(res.status_code)

    def _get_ticket(self) -> str:
        """
        Get a ticket from the statistics service
        :return: A ticket
        """
        request = "{}/get_ticket".format(self.stat_uri)
        res = requests.get(request, verify=self.verify_ssl)

        assert res.status_code == 200, "Bad status code: {}".format(res.status_code)

        ticket = res.text
        return ticket

    def _to_jws(self, data: dict) -> str:
        """
        Converts data to a jws

        :param data: Data to be converted to jws
        :return: a signed jwt
        """
        algorithm = "RS256"
        _jws = JWS(json.dumps(data), alg=algorithm)
        return _jws.sign_compact([self.sign_key])
