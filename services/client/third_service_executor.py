import logging
import re
from typing import Any, Dict
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from fastapi import HTTPException, status

from core.exceptions import ExternalServiceError, ServiceUnavailableError
from models.db import ThirdServiceConf

logger = logging.getLogger(__name__)

# Defense-in-depth for the one path in this backend that actually makes an
# outbound fetch against a URL not fully controlled by this codebase (the
# destination host is admin-configured via ThirdServiceConf.base_url, but the
# response is fully attacker/vendor-controlled). See
# docs/backend/features/url-evaluation/README.md Domain 5/6 notes.
_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MiB


class ThirdServiceExecutor:
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    
    def __init__(self, conf: ThirdServiceConf):
        self.conf = conf
    
    def resolve_url(self, runtime_vars: Dict[str, Any]) -> str:
        url = self.conf.base_url
        
        url = self._replace_variables(url, runtime_vars)
        
        url_template = self.conf.config_json.get("url_template", {})
        query_params = url_template.get("query_params", {})
        
        if query_params:
            parsed = urlparse(url)
            existing_params = parse_qs(parsed.query, keep_blank_values=True)
            
            final_params = {}
            for key, value in existing_params.items():
                final_params[key] = value[0] if len(value) == 1 else value
            
            for param_name, var_name in query_params.items():
                if param_name not in final_params and var_name in runtime_vars:
                    final_params[param_name] = runtime_vars[var_name]
            
            if final_params:
                new_query = urlencode(final_params)
                url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
        
        return url
    
    def _replace_variables(self, text: str, runtime_vars: Dict[str, Any]) -> str:
        def replacer(match):
            var_name = match.group(1)
            if var_name in runtime_vars:
                return str(runtime_vars[var_name])
            return match.group(0)
        
        return self.VARIABLE_PATTERN.sub(replacer, text)
    
    def resolve_body(self, runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        body_template = self.conf.config_json.get("body_template", [])
        
        if not isinstance(body_template, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="config_json.body_template must be a list"
            )
        
        body = {}
        
        for mapping in body_template:
            if not isinstance(mapping, dict):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Each body_template item must be a dict"
                )
            
            key = mapping.get("key")
            input_key = mapping.get("input")
            
            if not key or not input_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="body_template items must have 'key' and 'input' fields"
                )
            
            if input_key not in runtime_vars:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required input variable: '{input_key}'"
                )
            
            body[key] = runtime_vars[input_key]
        
        return body
    
    def map_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        response_mapping = self.conf.config_json.get("response_mapping", {})
        
        if not response_mapping:
            return response_data
        
        mapped = {}
        for output_key, source_path in response_mapping.items():
            value = self._get_nested_value(response_data, source_path)
            if value is not None:
                mapped[output_key] = value
        
        mapped["_raw"] = response_data
        return mapped
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    async def execute(self, runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        resolved_url = self.resolve_url(runtime_vars)
        body = self.resolve_body(runtime_vars)
        headers = dict(self.conf.headers_json) if self.conf.headers_json else {}
        
        method = self.conf.http_method.upper()
        
        try:
            # follow_redirects=False made explicit rather than relying on
            # httpx's default -- a redirect from an admin-configured detector
            # endpoint into a private/internal address is exactly the SSRF
            # shape this backend must not walk into automatically.
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
                if method == "GET":
                    params = body if body and len(body) > 0 else None
                    response = await client.request(
                        method=method,
                        url=resolved_url,
                        headers=headers,
                        params=params
                    )
                else:
                    if body and len(body) > 0:
                        response = await client.request(
                            method=method,
                            url=resolved_url,
                            headers=headers,
                            json=body
                        )
                    else:
                        response = await client.request(
                            method=method,
                            url=resolved_url,
                            headers=headers
                        )

                if response.is_redirect:
                    raise ExternalServiceError(
                        'Third-party service returned a redirect; redirects are not followed',
                        code='THIRD_PARTY_REDIRECT',
                    )

                content_length = response.headers.get('content-length')
                if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
                    raise ExternalServiceError(
                        'Third-party service response exceeded the maximum allowed size',
                        code='THIRD_PARTY_RESPONSE_TOO_LARGE',
                    )
                if len(response.content) > _MAX_RESPONSE_BYTES:
                    raise ExternalServiceError(
                        'Third-party service response exceeded the maximum allowed size',
                        code='THIRD_PARTY_RESPONSE_TOO_LARGE',
                    )

                response.raise_for_status()
                response_data = response.json()

                return self.map_response(response_data)

        except ExternalServiceError:
            raise
        except httpx.HTTPStatusError as e:
            # This executor is called both from the admin-owned "test
            # connection" flow AND from /prediction/predict for any
            # authenticated MEMBER (services/prediction_service.py
            # ::_predict_with_third_party) -- the vendor's raw response body
            # and connection-error text previously landed in `detail` and
            # propagated straight through to whichever caller triggered it,
            # not just the admin who configured the service. Real detail is
            # logged server-side only; the client gets a generic message.
            logger.warning(
                'third-party service returned an error status: %s', e.response.status_code, exc_info=e
            )
            raise ExternalServiceError(
                f"Third-party service returned an error (status {e.response.status_code})",
                code='THIRD_PARTY_ERROR',
            )
        except httpx.RequestError as e:
            logger.warning('failed to connect to third-party service', exc_info=e)
            raise ServiceUnavailableError(
                'Failed to connect to the configured third-party service',
                code='THIRD_PARTY_UNAVAILABLE',
            )
        except Exception as e:
            logger.error('unexpected error during third-party service execution', exc_info=e)
            raise ExternalServiceError(
                'Unexpected error while executing the third-party service call',
                code='THIRD_PARTY_ERROR',
            )
