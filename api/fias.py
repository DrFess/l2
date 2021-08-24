import pickle

import logging
import requests
import simplejson as json
from django.core.cache import cache

from appconf.manager import SettingManager
from rmis_integration.client import get_md5


logger = logging.getLogger(__name__)

BASE_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/{}"


def suggest(query, resource='address', count=5):
    k = SettingManager.get("dadata_key", default='', default_type='s')
    if not k:
        return []
    key = get_md5('{}{}{}'.format(k, resource, query))
    result = cache.get(key)
    if not result:
        url = BASE_URL.format(resource)
        headers = {"Authorization": "Token {}".format(k), "Content-Type": "application/json"}
        data = {"query": query, "count": count, "locations_boost": [{"kladr_id": SettingManager.get("dadata_kladr_prior_city", default='38', default_type='s')}]}
        r = requests.post(url, data=json.dumps(data), headers=headers)
        result = list(map(lambda x: x.get('value', ''), r.json().get('suggestions', [])))
        cache.set(key, pickle.dumps(result, protocol=4), 24 * 3600)
    else:
        result = pickle.loads(result, encoding="utf8")

    return result


def kladrapi_request(data: dict):
    kladrapi_url = SettingManager.get('kladrapi_url', default='https://kladr-api.ru/api.php', default_type='s')
    token = SettingManager.get('kladrapi_token', default='', default_type='s')
    try:
        if token:
            data['token'] = token

        key = f"kladrapi_request:{get_md5(json.dumps(data, sort_keys=True))}"
        result = cache.get(key)

        if not result:
            result = requests.get(kladrapi_url, params=data).json()
            if not result or not isinstance(result, dict) or 'result' not in result:
                return {}
            cache.set(key, pickle.dumps(result, protocol=4), 24 * 3600)
        else:
            result = pickle.loads(result, encoding="utf8")

        return result
    except Exception as e:
        logger.exception(e)
        return {}
